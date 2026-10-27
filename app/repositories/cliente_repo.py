"""
Repositório de Clientes: operações de leitura e escrita no banco, sempre
através do SQLAlchemy. Nenhuma tela fala com o banco direto — fala com aqui.
"""
from app.extensions import db
from app.models.cliente import Cliente, so_digitos


class ClienteRepository:
    def listar(self) -> list[Cliente]:
        return Cliente.query.order_by(Cliente.conta_id).all()

    def contar(self) -> int:
        return Cliente.query.count()

    def buscar_por_id(self, id_: int) -> Cliente | None:
        return db.session.get(Cliente, id_)

    def buscar_por_conta_id(self, conta_id: str) -> Cliente | None:
        return Cliente.query.filter_by(conta_id=conta_id).first()

    def buscar_por_cnpj(self, cnpj: str) -> Cliente | None:
        """Busca sempre pelo CNPJ só com dígitos — a chave de integração."""
        return Cliente.query.filter_by(cnpj=so_digitos(cnpj)).first()

    def criar(self, **dados) -> Cliente:
        # Garante que o CNPJ entre sempre padronizado (só dígitos).
        if "cnpj" in dados:
            dados["cnpj"] = so_digitos(dados["cnpj"])
        cliente = Cliente(**dados)
        db.session.add(cliente)
        db.session.commit()
        return cliente

    def salvar(self) -> None:
        """Confirma no banco alterações feitas em objetos já carregados."""
        db.session.commit()
