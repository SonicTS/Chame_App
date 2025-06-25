from sqlalchemy import Column, Integer, String, Float
from chame_app.database import Base
from sqlalchemy.orm import relationship
from models.sales_table import Sale
from passlib.context import CryptContext

class User(Base):
    __tablename__ = "users"  # Name of the table in the database

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
        def _round(val):
            return round(val, 2) if isinstance(val, float) and val is not None else val
        data = {
            "user_id": self.user_id,
            "name": self.name,
            "balance": _round(self.balance),
            "role": self.role,
        }
        if include_sales:
            data["sales"] = [sale.to_dict() for sale in self.sales]
        return data
    
    def hash_password(self, plain_password: str) -> str:
        """
        Returns an encoded hash, embedding salt & parameters:
        $argon2id$v=19$m=65536,t=3,p=1$<base64salt>$<base64hash>
        """
        return self.pwd_ctx.hash(plain_password)
    
    def verify_password(self, plain_password: str) -> bool:
        """Returns True if the password matches the given hash."""
        if self.role.lower == 'User':
            # Normal users should not be able to login
            return False
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
