"""
Modelos = as tabelas do banco de dados, descritas em Python.

Importamos aqui para que, ao criar o banco, o SQLAlchemy conheça todas as
tabelas de uma vez.
"""
from app.models.cliente import Cliente  # noqa: F401
