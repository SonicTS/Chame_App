from typing import Optional
from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship
from chame_app.database import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    consumer_id = Column(Integer, ForeignKey("users.user_id"))
    donator_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, default=1)
    total_price = Column(Float)
    timestamp = Column(String)  # This can be a datetime field, but we'll keep it simple for now
    salesman_id = Column(Integer, ForeignKey("users.user_id"))  # Optional sales person
    toast_round_id = Column(Integer, ForeignKey("toast_round.toast_round_id"), nullable=True)  # Make optional

    # Relationships
    consumer = relationship("User", back_populates="sales", foreign_keys=[consumer_id])
    donator = relationship("User", back_populates="donated_sales", foreign_keys=[donator_id])
    product = relationship("Product", back_populates="sales")
    toast_round = relationship("ToastRound", back_populates="sales")
    salesman = relationship('User', foreign_keys=[salesman_id])

    def __init__(self, consumer_id: int, product_id: int, quantity: int, total_price: float, timestamp: str, salesman_id: int, toast_round_id: int = None, donator_id: Optional[int] = None,):
        self.consumer_id = consumer_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = total_price
        self.timestamp = timestamp
        self.toast_round_id = toast_round_id
        self.donator_id = donator_id
        self.salesman_id = salesman_id

    def __repr__(self):
        return f"<Sale(consumer_id={self.consumer_id}, product_id={self.product_id}, quantity={self.quantity}, total_price={self.total_price}, timestamp={self.timestamp}, toast_round_id={self.toast_round_id}, donator_id={self.donator_id}, salesman_id={self.salesman_id})>"

    def to_dict(self, include_user=False, include_product=False, include_toast_round=False, show_deleted_entities=False, include_salesman=True):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        
        data = {
            "sale_id": self.sale_id,
            "consumer_id": self.consumer_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": _round(self.total_price),
            "timestamp": self.timestamp,
            "toast_round_id": self.toast_round_id,
            "donator_id": self.donator_id,
            "salesman_id": self.salesman_id
        }
        if include_salesman:
            data["salesman"] = self.salesman.to_dict(include_sales=False) if self.salesman else None
        if include_user:
            self._add_user_data(data)
        
        if include_product:
            self._add_product_data(data)
        
        if include_toast_round:
            self._add_toast_round_data(data)

        return data
        

    def _add_user_data(self, data: dict):
        """Add user data with availability status"""
        # Handle consumer
        data.update(self._get_entity_data("consumer", self.consumer, required=True))
        # Handle donator  
        data.update(self._get_entity_data("donator", self.donator, required=False))

    def _add_product_data(self, data: dict):
        """Add product data with availability status"""
        data.update(self._get_entity_data("product", self.product, required=True))

    def _add_toast_round_data(self, data: dict):
        """Add toast round data with availability status"""
        data.update(self._get_entity_data("toast_round", self.toast_round, required=False))

    def _get_entity_data(self, entity_name: str, entity_obj, required: bool = True):
        """Get entity data with availability status"""
        result = {}
        
        if entity_obj:
            is_available = getattr(entity_obj, 'is_available', True)
            
            # Call to_dict with parameters that avoid accessing unloaded relationships
            if entity_name == "product":
                # For products, don't include sales or other relationships that weren't eagerly loaded
                result[entity_name] = entity_obj.to_dict(include_ingredients=False, include_sales=False, include_toast_rounds=False, include_product_ingredients=False)
            elif entity_name == "toast_round":
                # For toast rounds, don't include sales or salesman that weren't eagerly loaded
                result[entity_name] = entity_obj.to_dict(include_sales=False, include_salesman=False)
            elif entity_name in ["consumer", "donator"]:
                # For users, don't include their sales or other relationships
                result[entity_name] = entity_obj.to_dict(include_sales=False)
            else:
                # For other entities, use default parameters
                result[entity_name] = entity_obj.to_dict()
                    
            result[f"{entity_name}_available"] = is_available
            
            if not is_available:
                is_deleted = getattr(entity_obj, 'is_deleted', False)
                result[f"{entity_name}_status"] = "deleted" if is_deleted else "disabled"
                
                # Add reason for unavailability if available
                disabled_reason = getattr(entity_obj, 'disabled_reason', None)
                if disabled_reason:
                    result[f"{entity_name}_unavailable_reason"] = disabled_reason
        else:
            result[entity_name] = None
            result[f"{entity_name}_available"] = not required  # Missing optional entities are "available"
            if required:
                result[f"{entity_name}_status"] = "not_found"
        
        return result
