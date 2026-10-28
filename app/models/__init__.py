"""
Modelos = as tabelas do banco de dados, descritas em Python.

Importamos aqui para que, ao criar o banco, o SQLAlchemy conheça todas as
tabelas de uma vez.
"""
from app.models.atividade import Atividade  # noqa: F401
from app.models.cadencia import Cadencia  # noqa: F401
from app.models.cliente import Cliente  # noqa: F401
from app.models.diagnostico import Diagnostico  # noqa: F401
from app.models.gate import Gate  # noqa: F401
from app.models.pos_venda import PosVenda  # noqa: F401
from app.models.proposta import Proposta  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
