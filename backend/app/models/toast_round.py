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