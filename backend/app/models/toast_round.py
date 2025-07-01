from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from chame_app.database import Base
from .product_table import Product
import datetime
from utils.firebase_logger import log_debug, log_error

class ToastRound(Base):
    __tablename__ = 'toast_round'

    toast_round_id = Column(Integer, primary_key=True, autoincrement=True)
    date_time = Column(String)  # This can be a datetime field, but we'll keep it simple for now
    # Relationship to link multiple sales to a single toast round
    sales = relationship('Sale', back_populates='toast_round')

    def __init__(self, date_time: str = str(datetime.datetime.now())):
        self.date_time = date_time

    def to_dict(self, include_products=False, include_sales=False):
        try:
            log_debug(f"Converting ToastRound {self.toast_round_id} to dict", {
                "toast_round_id": self.toast_round_id,
                "include_products": include_products,
                "include_sales": include_sales
            })
            
            data = {
                "toast_round_id": self.toast_round_id,
                "date_time": self.date_time,
            }
            
            if include_products:
                try:
                    if self.toast_round_products is None:
                        log_debug(f"ToastRound {self.toast_round_id} has None toast_round_products relationship")
                        data["products"] = []
                    else:
                        products_data = []
                        for ptr in self.toast_round_products:
                            if ptr is None:
                                log_debug(f"Found None product_toast_round in ToastRound {self.toast_round_id}")
                                continue
                            if ptr.product is None:
                                log_error(f"ToastRound {self.toast_round_id} has product_toast_round with None product", 
                                         {"toast_round_id": self.toast_round_id, "ptr_id": getattr(ptr, 'id', 'unknown')})
                                continue
                            try:
                                products_data.append(ptr.product.to_dict())
                            except Exception as e:
                                log_error(f"Error converting product to dict for ToastRound {self.toast_round_id}", 
                                         {"toast_round_id": self.toast_round_id, "product_id": getattr(ptr.product, 'product_id', 'unknown')}, 
                                         exception=e)
                        data["products"] = products_data
                except Exception as e:
                    log_error(f"Error processing products for ToastRound {self.toast_round_id}", 
                             {"toast_round_id": self.toast_round_id}, exception=e)
                    data["products"] = []
            
            if include_sales:
                try:
                    if self.sales is None:
                        log_debug(f"ToastRound {self.toast_round_id} has None sales relationship")
                        data["sales"] = []
                    else:
                        sales_data = []
                        for sale in self.sales:
                            if sale is None:
                                log_debug(f"Found None sale in ToastRound {self.toast_round_id}")
                                continue
                            try:
                                sales_data.append(sale.to_dict(include_product=True, include_user=True))
                            except Exception as e:
                                log_error(f"Error converting sale to dict for ToastRound {self.toast_round_id}", 
                                         {"toast_round_id": self.toast_round_id, "sale_id": getattr(sale, 'sale_id', 'unknown')}, 
                                         exception=e)
                        data["sales"] = sales_data
                except Exception as e:
                    log_error(f"Error processing sales for ToastRound {self.toast_round_id}", 
                             {"toast_round_id": self.toast_round_id}, exception=e)
                    data["sales"] = []
            
            log_debug(f"Successfully converted ToastRound {self.toast_round_id} to dict")
            return data
            
        except Exception as e:
            log_error(f"Critical error in ToastRound.to_dict for toast_round {getattr(self, 'toast_round_id', 'unknown')}", 
                     {"toast_round_id": getattr(self, 'toast_round_id', None)}, exception=e)
            # Return minimal safe data on error
            return {
                "toast_round_id": getattr(self, 'toast_round_id', None),
                "date_time": getattr(self, 'date_time', str(datetime.datetime.now())),
                "products": [] if include_products else None,
                "sales": [] if include_sales else None
            }