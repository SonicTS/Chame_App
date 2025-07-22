from sqlalchemy import Column, Integer, String, Float
from chame_app.database import Base
from sqlalchemy.orm import relationship
from models.enhanced_soft_delete_mixin import EnhancedSoftDeleteMixin, SoftDeleteCascadeRule, HardDeleteCascadeRule
from passlib.context import CryptContext
from utils.firebase_logger import log_debug, log_error

class User(Base, EnhancedSoftDeleteMixin):
    __tablename__ = "users"  # Name of the table in the database

    # Define cascade rules for users
    _cascade_rules = [
        SoftDeleteCascadeRule(
            "sales", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep sales history
        ),
        SoftDeleteCascadeRule(
            "donated_sales", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep donation history
        ),
        SoftDeleteCascadeRule(
            "pfand_history", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep pfand history
        )
    ]
    
    # Define hard delete rules for users
    _hard_delete_rules = [
        HardDeleteCascadeRule(
            "sales",
            HardDeleteCascadeRule.CASCADE_NULLIFY,  # Nullify consumer_id in sales
            cascade_order=1
        ),
        HardDeleteCascadeRule(
            "donated_sales",
            HardDeleteCascadeRule.CASCADE_NULLIFY,  # Nullify donator_id in sales
            cascade_order=1
        ),
        HardDeleteCascadeRule(
            "pfand_history",
            HardDeleteCascadeRule.CASCADE_NULLIFY,  # Nullify user_id in pfand history
            cascade_order=1
        )
    ]

    user_id = Column(Integer, primary_key=True, index=True)  # Primary Key
    name = Column(String, index=True)  # Name column
    balance = Column(Float, default=0)  # User balance
    password_hash = Column(String)  # Store the hashed password
    role = Column(String, default="user")  # Role (e.g., 'admin', 'wrirt')
    pwd_ctx = CryptContext(
        schemes=["argon2"],
        deprecated="auto",
        argon2__memory_cost=2**16,   # 64 MiB
        argon2__time_cost=3,         # 3 iterations
        argon2__parallelism=1,       # single-threaded
    )

    donated_sales = relationship("Sale", back_populates="donator", foreign_keys="Sale.donator_id")
    pfand_history = relationship("PfandHistory", back_populates="user")
    sales = relationship("Sale", back_populates="consumer", foreign_keys="Sale.consumer_id")
    
    def __init__(self, name: str, balance: float = 0.0, password_hash: str = "", role: str = "user"):
        self.name = name
        self.balance = balance
        self.password_hash = self.hash_password(password_hash)
        self.role = role
        
    def __repr__(self):
        return f"<User(name={self.name}, balance={self.balance}, role={self.role})>"

    def to_dict(self, include_sales=False):
        try:
            #log_debug(f"Converting User {self.user_id} to dict", {"user_id": self.user_id, "include_sales": include_sales})
            
            def _round(val):
                return round(val, 2) if isinstance(val, float) and val is not None else val
            
            data = {
                "user_id": self.user_id,
                "name": self.name,
                "balance": _round(self.balance),
                "role": self.role,
                # Add soft delete fields for restore functionality
                "is_deleted": getattr(self, 'is_deleted', False),
                "deleted_at": self.deleted_at.isoformat() if getattr(self, 'deleted_at', None) else None,
                "deleted_by": getattr(self, 'deleted_by', None),
                "is_disabled": getattr(self, 'is_disabled', False),
                "disabled_reason": getattr(self, 'disabled_reason', None),
            }
            
            if include_sales:
                try:
                    if self.sales is None:
                        #log_debug(f"User {self.user_id} has None sales relationship")
                        data["sales"] = []
                    else:
                        sales_data = []
                        for sale in self.sales:
                            if sale is None:
                                #log_debug(f"Found None sale in User {self.user_id} sales relationship")
                                continue
                            try:
                                sales_data.append(sale.to_dict(include_salesman=False))
                            except Exception as e:
                                log_error(f"Error converting sale to dict for User {self.user_id}", 
                                         {"user_id": self.user_id, "sale_id": getattr(sale, 'sale_id', 'unknown')}, 
                                         exception=e)
                        data["sales"] = sales_data
                except Exception as e:
                    log_error(f"Error processing sales for User {self.user_id}", 
                             {"user_id": self.user_id}, 
                             exception=e)
                    data["sales"] = []
            
            #log_debug(f"Successfully converted User {self.user_id} to dict")
            return data
            
        except Exception as e:
            log_error(f"Critical error in User.to_dict for user {getattr(self, 'user_id', 'unknown')}", 
                     {"user_id": getattr(self, 'user_id', None)}, 
                     exception=e)
            # Return minimal safe data on error
            return {
                "user_id": getattr(self, 'user_id', None),
                "name": getattr(self, 'name', 'Unknown'),
                "balance": 0.0,
                "role": getattr(self, 'role', 'user'),
                "sales": [] if include_sales else None
            }
    
    def hash_password(self, plain_password: str) -> str:
        """
        Returns an encoded hash, embedding salt & parameters:
        $argon2id$v=19$m=65536,t=3,p=1$<base64salt>$<base64hash>
        """
        if plain_password == "":
            plain_password = "default"
        return self.pwd_ctx.hash(plain_password)
    
    def verify_password(self, plain_password: str) -> bool:
        """Returns True if the password matches the given hash."""
        if self.role.lower == 'User':
            # Normal users should not be able to login
            return False
        if plain_password == "":
            plain_password = "default"
        return self.pwd_ctx.verify(plain_password, self.password_hash)




def main():
    pass
    # Create the database tables
    # Base.metadata.create_all(bind=engine)

    # # Create a new session
    # session = SessionLocal()

    # # Check if an admin user already exists
    # admin_user = session.query(User).filter_by(role="admin").first()
    # if not admin_user:
    #     # Add an admin user
    #     admin_user = User(name="admin", balance=0, password_hash="12345678", role="admin")
    #     session.add(admin_user)
    #     session.commit()
    #     print("Admin user created.")
    # else:
    #     print("Admin user already exists.")

    # # Close the session
    # session.close()
if __name__ == "__main__":
    main()
