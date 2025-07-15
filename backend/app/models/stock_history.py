from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from chame_app.database import Base

class StockHistory(Base):
    __tablename__ = "stock_history"

    history_id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.ingredient_id"))
    amount = Column(Float)
    timestamp = Column(String)  # For simplicity, this can be a string (you can use datetime for a more complex setup)
    comment = Column(String, nullable=True)  # Optional comment for the transaction
    
    # Relationship to ingredient
    ingredient = relationship("Ingredient", back_populates="stock_history")
    
    def __init__(self, ingredient_id: int, amount: float, timestamp: str, comment: str = None):
        self.ingredient_id = ingredient_id
        self.amount = amount
        self.comment = comment
        self.timestamp = timestamp
        
    def __repr__(self):
        return f"<Transaction(history_id={self.history_id}, ingredient={self.ingredient_id}, amount={self.amount}, timestamp={self.timestamp}, comment={self.comment})>"
    
    def to_dict(self, include_ingredient=False):
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "history_id": self.history_id,
            "ingredient_id": self.ingredient_id,
            "amount": _round(self.amount),
            "timestamp": self.timestamp,
            "comment": self.comment
        }
        
        if include_ingredient and self.ingredient:
            data["ingredient_name"] = self.ingredient.name
        
        return data
