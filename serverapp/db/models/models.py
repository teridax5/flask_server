# импортируем объекты для построения метаданных таблиц и взаимосвязей,
# а так же подготовка для сериализации данных
from sqlalchemy import Column, Integer, ForeignKey, VARCHAR, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from marshmallow import Schema

Base = declarative_base()


class Author(Base):
    """Таблица автора"""
    __tablename__ = 'authors'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    author_name = Column(VARCHAR(50), nullable=True)
    short_biography = Column(VARCHAR(100), nullable=True)
    email = Column(VARCHAR(60), nullable=True)
    # уникальные значения
    UniqueConstraint(author_name, name='author')
    UniqueConstraint(email, name='email')


class AuthorSchema(Schema):
    """Схема сериализации для таблицы авторов"""
    class Meta:
        """В данном случае, достаточно выводить лишь некоторые поля"""
        fields = ('author_name', 'email')


class Book(Base):
    """Таблица книг"""
    __tablename__ = 'books'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    author_id = Column(
        Integer,
        ForeignKey(f'authors.id'),
        nullable=False
    )
    book_name = Column(VARCHAR(50), nullable=True)
    description = Column(VARCHAR(100), nullable=True)
    author = relationship('Author', backref='list_of_books')


class BookSchema(Schema):
    """Аналогично AuthorSchema"""
    class Meta:
        fields = ('book_name', 'description')
