from sqlalchemy import Column, Integer, String, Float
from chame_app.database import Base, engine, SessionLocal
from sqlalchemy.orm import relationship
from models.sales_table import Sale

class User(Base):
    __tablename__ = "users"  # Name of the table in the database

    user_id = Column(Integer, primary_key=True, index=True)  # Primary Key
    name = Column(String, index=True)  # Name column
    balance = Column(Float, default=0)  # User balance
    password_hash = Column(String)  # Store the hashed password
    role = Column(String, default="user")  # Role (e.g., 'admin', 'wrirt')

    sales = relationship("Sale", back_populates="user")

    def __repr__(self):
        return f"<User(name={self.name}, balance={self.balance}, role={self.role})>"




def main():
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Create a new session
    session = SessionLocal()

    # Check if an admin user already exists
    admin_user = session.query(User).filter_by(role="admin").first()
    if not admin_user:
        # Add an admin user
        admin_user = User(name="admin", balance=0, password_hash="12345678", role="admin")
        session.add(admin_user)
        session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")

    # Close the session
    session.close()
if __name__ == "__main__":
    main()
