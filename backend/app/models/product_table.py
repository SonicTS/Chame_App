from typing import List
from models.ingredient import Ingredient
from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from chame_app.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
from utils.firebase_logger import log_debug, log_error


class Product(Base, SoftDeleteMixin):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 'raw ingredient' or 'toast'
    price_per_unit = Column(Float)
    cost_per_unit = Column(Float)  # Cost price per unit	
    profit_per_unit = Column(Float)  # Profit per unit
    stock_quantity = Column(Integer, default=0)
    toaster_space = Column(Integer, default=0)  # For toast products
    sales = relationship("Sale", back_populates="product")

    pfand_history = relationship("PfandHistory", back_populates="product")
    product_toast_rounds = relationship("ProductToastround", back_populates="product")
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")

    def update_stock(self):
        """
        Update the stock of the product based on the stock of its ingredients and the quantity required.
        """
        self.stock_quantity = float('inf')  # Assume infinite until limited by ingredients

        for assoc in self.product_ingredients:
            ingredient = assoc.ingredient
            quantity_needed = assoc.ingredient_quantity

            if not ingredient:
                print(f"Ingredient with ID {assoc.ingredient_id} not found.")
                continue

            if quantity_needed <= 0:
                print(f"Invalid quantity needed for ingredient {ingredient.name}")
                continue

            # Calculate how many products can be made from this ingredient
            ingredient_stock = ingredient.stock_quantity
            max_product_qty = ingredient_stock // quantity_needed

            self.stock_quantity = min(self.stock_quantity, max_product_qty)

        print(f"Stock updated for product: {self.name} -> {self.stock_quantity}")

    def get_pfand(self) -> float:
        """
        Calculate the total deposit price for the product based on its ingredients.
        """
        total_deposit = 0.0
        for assoc in self.product_ingredients:
            ingredient = assoc.ingredient
            if ingredient and ingredient.pfand:
                total_deposit += ingredient.pfand * assoc.ingredient_quantity
        return round(total_deposit, 2)
    
    def __init__(self, name: str, category: str, price_per_unit: float = 0, cost_per_unit: float = 0, profit_per_unit: float = 0, stock_quantity: int = 0, toaster_space: int = 0):
        self.name = name
        self.category = category
        self.price_per_unit = price_per_unit
        self.cost_per_unit = cost_per_unit
        self.profit_per_unit = profit_per_unit
        self.stock_quantity = stock_quantity
        self.toaster_space = toaster_space

    def __repr__(self):
        return f"<Product(name={self.name}, category={self.category}, price={self.price_per_unit}, stock={self.stock_quantity}, ingredients={self.ingredients})>"

    def to_dict(self, include_ingredients=False, include_sales=False, include_toast_rounds=False, include_product_ingredients=False, include_product_toast_rounds=False):
        try:
            log_debug(f"Converting Product {self.product_id} to dict", {
                "product_id": self.product_id, 
                "include_ingredients": include_ingredients,
                "include_sales": include_sales,
                "include_toast_rounds": include_toast_rounds,
                "include_product_ingredients": include_product_ingredients,
                "include_product_toast_rounds": include_product_toast_rounds
            })
            
            def _round(val):
                return round(val, 2) if isinstance(val, float) and val is not None else val
            
            # Get basic product data
            data = {
                "product_id": self.product_id,
                "name": self.name,
                "category": self.category,
                "price_per_unit": _round(self.price_per_unit),
                "cost_per_unit": _round(self.cost_per_unit),
                "profit_per_unit": _round(self.profit_per_unit),
                "stock_quantity": self.stock_quantity,
                "toaster_space": self.toaster_space,
            }
            
            # Get pfand safely
            try:
                data["pfand"] = self.get_pfand()
            except Exception as e:
                log_error(f"Error calculating pfand for Product {self.product_id}", 
                         {"product_id": self.product_id}, exception=e)
                data["pfand"] = 0.0
            
            # Process ingredients
            if include_ingredients:
                try:
                    if self.product_ingredients is None:
                        log_debug(f"Product {self.product_id} has None product_ingredients relationship")
                        data["ingredients"] = []
                    else:
                        ingredients_data = []
                        for pi in self.product_ingredients:
                            if pi is None:
                                log_debug(f"Found None product_ingredient in Product {self.product_id}")
                                continue
                            if pi.ingredient is None:
                                log_error(f"Product {self.product_id} has product_ingredient with None ingredient", 
                                         {"product_id": self.product_id, "pi_id": getattr(pi, 'id', 'unknown')})
                                continue
                            try:
                                ingredients_data.append(pi.ingredient.to_dict())
                            except Exception as e:
                                log_error(f"Error converting ingredient to dict for Product {self.product_id}", 
                                         {"product_id": self.product_id, "ingredient_id": getattr(pi.ingredient, 'ingredient_id', 'unknown')}, 
                                         exception=e)
                        data["ingredients"] = ingredients_data
                except Exception as e:
                    log_error(f"Error processing ingredients for Product {self.product_id}", 
                             {"product_id": self.product_id}, exception=e)
                    data["ingredients"] = []
            
            # Process product_ingredients
            if include_product_ingredients:
                try:
                    if self.product_ingredients is None:
                        data["product_ingredients"] = []
                    else:
                        pi_data = []
                        for pi in self.product_ingredients:
                            if pi is None:
                                continue
                            try:
                                pi_data.append(pi.to_dict())
                            except Exception as e:
                                log_error(f"Error converting product_ingredient to dict for Product {self.product_id}", 
                                         {"product_id": self.product_id, "pi_id": getattr(pi, 'id', 'unknown')}, 
                                         exception=e)
                        data["product_ingredients"] = pi_data
                except Exception as e:
                    log_error(f"Error processing product_ingredients for Product {self.product_id}", 
                             {"product_id": self.product_id}, exception=e)
                    data["product_ingredients"] = []
            
            # Process sales
            if include_sales:
                try:
                    if self.sales is None:
                        data["sales"] = []
                    else:
                        sales_data = []
                        for sale in self.sales:
                            if sale is None:
                                continue
                            try:
                                sales_data.append(sale.to_dict())
                            except Exception as e:
                                log_error(f"Error converting sale to dict for Product {self.product_id}", 
                                         {"product_id": self.product_id, "sale_id": getattr(sale, 'sale_id', 'unknown')}, 
                                         exception=e)
                        data["sales"] = sales_data
                except Exception as e:
                    log_error(f"Error processing sales for Product {self.product_id}", 
                             {"product_id": self.product_id}, exception=e)
                    data["sales"] = []
            
            # Process toast rounds
            if include_toast_rounds:
                try:
                    if self.product_toast_rounds is None:
                        data["toast_rounds"] = []
                    else:
                        tr_data = []
                        for ptr in self.product_toast_rounds:
                            if ptr is None or ptr.toast_round is None:
                                continue
                            try:
                                tr_data.append(ptr.toast_round.to_dict())
                            except Exception as e:
                                log_error(f"Error converting toast_round to dict for Product {self.product_id}", 
                                         {"product_id": self.product_id, "toast_round_id": getattr(ptr.toast_round, 'toast_round_id', 'unknown')}, 
                                         exception=e)
                        data["toast_rounds"] = tr_data
                except Exception as e:
                    log_error(f"Error processing toast_rounds for Product {self.product_id}", 
                             {"product_id": self.product_id}, exception=e)
                    data["toast_rounds"] = []
            
            # Process product_toast_rounds
            if include_product_toast_rounds:
                try:
                    if self.product_toast_rounds is None:
                        data["product_toast_rounds"] = []
                    else:
                        ptr_data = []
                        for ptr in self.product_toast_rounds:
                            if ptr is None:
                                continue
                            try:
                                ptr_data.append(ptr.to_dict())
                            except Exception as e:
                                log_error(f"Error converting product_toast_round to dict for Product {self.product_id}", 
                                         {"product_id": self.product_id, "ptr_id": getattr(ptr, 'id', 'unknown')}, 
                                         exception=e)
                        data["product_toast_rounds"] = ptr_data
                except Exception as e:
                    log_error(f"Error processing product_toast_rounds for Product {self.product_id}", 
                             {"product_id": self.product_id}, exception=e)
                    data["product_toast_rounds"] = []
            
            log_debug(f"Successfully converted Product {self.product_id} to dict")
            return data
            
        except Exception as e:
            log_error(f"Critical error in Product.to_dict for product {getattr(self, 'product_id', 'unknown')}", 
                     {"product_id": getattr(self, 'product_id', None)}, exception=e)
            # Return minimal safe data on error
            return {
                "product_id": getattr(self, 'product_id', None),
                "name": getattr(self, 'name', 'Unknown'),
                "category": getattr(self, 'category', 'unknown'),
                "price_per_unit": 0.0,
                "cost_per_unit": 0.0,
                "profit_per_unit": 0.0,
                "stock_quantity": 0,
                "toaster_space": 0,
                "pfand": 0.0,
                "ingredients": [] if include_ingredients else None,
                "product_ingredients": [] if include_product_ingredients else None,
                "sales": [] if include_sales else None,
                "toast_rounds": [] if include_toast_rounds else None,
                "product_toast_rounds": [] if include_product_toast_rounds else None
            }

