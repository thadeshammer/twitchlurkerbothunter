"""
Base declarative class for SQLAlchemy models.

This module defines the base class for all SQLAlchemy ORM models in the application.
By using this base class, models will be automatically registered with SQLAlchemy's
metadata, which is essential for creating and managing database tables.

Usage:
    - Import the `Base` class in your SQLAlchemy model definitions.
    - Define your models as subclasses of `Base`.

Example:
    from sqlalchemy import Column, Integer, String
    from .base import Base

    class Foo(Base):
        __tablename__ = 'foo'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        foovalue = Column(Integer)

Dependencies:
    - SQLAlchemy: The SQL toolkit and Object-Relational Mapping (ORM) library for Python.

Note:
    Ensure that this module is imported in any module where SQLAlchemy models are defined
    so that the models are registered with the `Base` metadata.
"""
from sqlalchemy.ext.declarative import declarative_base

# Create a base class for all declarative models to inherit from.
Base = declarative_base()
