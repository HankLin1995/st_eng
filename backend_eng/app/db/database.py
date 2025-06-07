from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get database URL from environment variable or use default
# SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:password@db:3306/mydatabase")

# Ensure data directory exists for SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///") and not SQLALCHEMY_DATABASE_URL.startswith("sqlite:///:memory:"):
    # Extract the path part after sqlite:///
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    # Get the directory name
    db_dir = os.path.dirname(os.path.abspath(db_path))
    # Create the directory
    os.makedirs(db_dir, exist_ok=True)

# Create engine with the appropriate connect_args for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#def create_tables():
 #   """Create all tables in the database"""
    # The directory creation is now handled when the module is loaded
    # Create all tables
   # Base.metadata.create_all(bind=engine,checkfirst=True)
def create_tables():
   """Create all tables in the database."""
   try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
   except Exception as e:
       print(f"[WARNING] Skipping table creation due to error: {e}")
