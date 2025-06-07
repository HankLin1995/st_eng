import pytest
from sqlalchemy import text
from app.db.database import Base
from app.tests.conftest import engine, db

def test_database_connection(db):
    """Test that we can connect to the database and execute a simple query (in-memory)"""
    result = db.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1

def test_create_tables(db):
    """Test that we can create database tables (in-memory)"""
    # Tables should already be created by the fixture
    result = db.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ))
    tables = [row[0] for row in result]
    assert "projects" in tables
    assert "construction_inspections" in tables
    assert "inspection_photos" in tables
