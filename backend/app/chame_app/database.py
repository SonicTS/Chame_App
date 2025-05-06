from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Create a database engine (for SQLite, we use sqlite:///file.db)
DATABASE_URL = "sqlite:///./kassensystem.db"  # Change to your database location

# Create an engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # SQLite-specific argument

# Create a base class for models
Base = declarative_base()

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
