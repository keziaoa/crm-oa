"""
Extensões do Flask criadas em um único lugar, para evitar importações
circulares. Por enquanto só temos o banco de dados (SQLAlchemy).
"""
from flask_sqlalchemy import SQLAlchemy

# "db" é a porta de entrada para o banco. Todos os modelos (tabelas) e
# repositórios usam este mesmo objeto. Trocar SQLite por PostgreSQL não
# muda nada aqui — só muda o endereço em config.py.
db = SQLAlchemy()
