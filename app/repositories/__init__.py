"""
Camada de repositórios = o ÚNICO lugar que conversa com o banco de dados.

Por que isso importa para o futuro: as telas e as regras nunca escrevem
comandos de banco diretamente. Elas chamam métodos como
`clientes.buscar_por_cnpj(...)`. No dia da troca para PostgreSQL (integração
com o cohab-control), nada disso muda — só muda o endereço do banco em
config.py. Se um dia o cohab-control expuser os clientes por uma API em vez
de uma tabela, basta reescrever este repositório, sem tocar no resto.
"""
from app.repositories.cliente_repo import ClienteRepository

clientes = ClienteRepository()

__all__ = ["clientes", "ClienteRepository"]
