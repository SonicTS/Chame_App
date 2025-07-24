from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from chame_app.database import Base
from models.enhanced_soft_delete_mixin import EnhancedSoftDeleteMixin, SoftDeleteCascadeRule, HardDeleteCascadeRule
from utils.firebase_logger import log_debug, log_error

class Ingredient(Base, EnhancedSoftDeleteMixin):
    __tablename__ = "ingredients"

    # Define cascade rules for ingredients
    _cascade_rules = [
        SoftDeleteCascadeRule(
            "ingredient_products", 
            SoftDeleteCascadeRule.CASCADE_DISABLE,
            condition_callback=lambda pi: hasattr(pi, 'product') and pi.product and pi.product.is_available
        )
    ]
    
    # Define hard delete rules for ingredients
    _hard_delete_rules = [
        HardDeleteCascadeRule(
            "ingredient_products",
            HardDeleteCascadeRule.CASCADE_RESTRICT,  # Prevent deletion if products use this ingredient
            condition_callback=lambda pi: pi.product and pi.product.is_available,
            cascade_order=0
        )
    ]

    ingredient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price_per_package = Column(Float)  # Purchasing price per package
    number_of_units = Column(Integer)  # Number of units in a package
    pfand = Column(Float, default=0)  # Deposit price for the package(Pfand)
    price_per_unit = Column(Float)  # Purchasing price per unit

    stock_quantity = Column(Float, default=0)

    # Relationship back to Product (via the ProductIngredient table)
    ingredient_products = relationship("ProductIngredient", back_populates="ingredient")
    
    # Relationship to stock history
    stock_history = relationship("StockHistory", back_populates="ingredient")
    
    def __init__(self, name, price_per_package, number_of_units, price_per_unit, pfand=0.0, stock_quantity=0):
        self.name = name
        self.pfand = pfand
        self.price_per_package = price_per_package
        self.number_of_units = number_of_units
        self.price_per_unit = price_per_unit
        self.stock_quantity = stock_quantity
        
    def __repr__(self):
        return f"<Ingredient(name={self.name}, price_per_package={self.price_per_package}, price_per_unit={self.price_per_unit}, number_of_units={self.number_of_units}, stock={self.stock_quantity}), pfand={self.pfand})>"

    def to_dict(self, include_products=False):
        try:
            # log_debug(f"Converting Ingredient {self.ingredient_id} to dict", {
            #     "ingredient_id": self.ingredient_id, 
            #     "include_products": include_products
            # })
            
            def _round(val):
                return round(val, 2) if isinstance(val, float) and val is not None else val
            
            data = {
                "ingredient_id": self.ingredient_id,
                "name": self.name,
                "price_per_package": _round(self.price_per_package),
                "number_of_units": self.number_of_units,
                "price_per_unit": _round(self.price_per_unit),
                "stock_quantity": _round(self.stock_quantity),
                "pfand": _round(self.pfand),
                # Add soft delete fields for restore functionality
                "is_deleted": getattr(self, 'is_deleted', False),
                "deleted_at": self.deleted_at.isoformat() if getattr(self, 'deleted_at', None) else None,
                "deleted_by": getattr(self, 'deleted_by', None),
                "is_disabled": getattr(self, 'is_disabled', False),
                "disabled_reason": getattr(self, 'disabled_reason', None),
            }
            
            if include_products:
                try:
                    if self.ingredient_products is None:
                        #log_debug(f"Ingredient {self.ingredient_id} has None ingredient_products relationship")
                        data["products"] = []
                    else:
                        products_data = []
                        for ip in self.ingredient_products:
                            if ip is None:
                                #log_debug(f"Found None ingredient_product in Ingredient {self.ingredient_id}")
                                continue
                            if ip.product is None:
                                log_error(f"Ingredient {self.ingredient_id} has ingredient_product with None product", 
                                         {"ingredient_id": self.ingredient_id, "ip_id": getattr(ip, 'id', 'unknown')})
                                continue
                            try:
                                products_data.append(ip.product.to_dict(include_ingredients=False, include_sales=False, include_toast_rounds=False, include_product_ingredients=False))
                            except Exception as e:
                                log_error(f"Error converting product to dict for Ingredient {self.ingredient_id}", 
                                         {"ingredient_id": self.ingredient_id, "product_id": getattr(ip.product, 'product_id', 'unknown')}, 
                                         exception=e)
                        data["products"] = products_data
                except Exception as e:
                    log_error(f"Error processing products for Ingredient {self.ingredient_id}", 
                             {"ingredient_id": self.ingredient_id}, exception=e)
                    data["products"] = []
            
            #log_debug(f"Successfully converted Ingredient {self.ingredient_id} to dict")
            return data
            
        except Exception as e:
            log_error(f"Critical error in Ingredient.to_dict for ingredient {getattr(self, 'ingredient_id', 'unknown')}", 
                     {"ingredient_id": getattr(self, 'ingredient_id', None)}, exception=e)
            # Return minimal safe data on error
            return {
                "ingredient_id": getattr(self, 'ingredient_id', None),
                "name": getattr(self, 'name', 'Unknown'),
                "price_per_package": 0.0,
                "number_of_units": 0,
                "price_per_unit": 0.0,
                "stock_quantity": 0.0,
                "pfand": 0.0,
                "products": [] if include_products else None
            }


def main():
    #Base.metadata.create_all(bind=engine)
    pass
    # db = SessionLocal()

    # # Create some ingredients
    # bread = Ingredient(name="Bread", price_per_unit=0.5, stock_quantity=100)
    # cheese = Ingredient(name="Cheese", price_per_unit=1.2, stock_quantity=50)
    # speed = Ingredient(name="Speed", price_per_unit=0.2, stock_quantity=200)

    # # Add ingredients to the session
    # db.add(bread)
    # db.add(cheese)
    # db.add(speed)


    # # Commit to the database
    # db.commit()

    # # Close the session
    # db.close()

if __name__ == "__main__":
    main()