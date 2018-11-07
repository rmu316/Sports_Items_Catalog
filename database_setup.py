#!/usr/bin/env python2
# Created by Richard Mu
# FSND Items Catalog Project
#
# Import all necessary libraries
# Standard imports for SQL Alchemy Library,
# see http://flask.pocoo.org/docs/1.0/patterns/sqlalchemy/
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


# Define tables in ONE command!
Base = declarative_base()


# The User table for keeping track of...you guessed it,
# other users! We keep track specifically of:
# - Their id (unique id assign by this table)
# - Their name (provided by 3rd party authentication service)
# - Their email (provided by 3rd party authentication service)
# - Their picture (provided by 3rd party authentication service)
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


# The category table for keeping track of the sports types
# in this catalog. Static table which will not be modified
# by user input
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)

    # Make our object serilizable for easy JSON output
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
        }


# The item table which will keep track of all the individual items
# in the catalog. Users will be able to modify individual items
# in the database, specifically:
# - Item title
# - Item description
# - The category that the item belongs to
# Also, every item is tied to a user based on their id so that we
# can authorize the right user for editing or deleting the item
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    desc = Column(String(65536), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Make our object serilizable for easy JSON output
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'desc': self.desc,
            'category_id': self.category_id,
        }


engine = create_engine('sqlite:///itemcatalog.db')


Base.metadata.create_all(engine)
