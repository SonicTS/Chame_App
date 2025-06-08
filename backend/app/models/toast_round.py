from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from chame_app.database import Base
from .sales_table import Sale
from .product_table import Product
import datetime

class ToastRound(Base):
    __tablename__ = 'toast_round'

    toast_round_id = Column(Integer, primary_key=True, autoincrement=True)
    date_time = Column(String)  # This can be a datetime field, but we'll keep it simple for now
    # Relationship to link multiple sales to a single toast round
    toast_round_products = relationship('ProductToastround', back_populates='toast_round')
    sales = relationship('Sale', back_populates='toast_round')

    def __init__(self, date_time: str = str(datetime.datetime.now())):
        self.date_time = date_time

    def to_dict(self, include_products=False, include_sales=False):
        data = {
            "toast_round_id": self.toast_round_id,
            "date_time": self.date_time,
        }
        if include_products:
            data["products"] = [ptr.product.to_dict() for ptr in self.toast_round_products]
        if include_sales:
            data["sales"] = [sale.to_dict(include_product=True, include_user=True) for sale in self.sales]
        return data