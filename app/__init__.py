"""
Fábrica da aplicação Flask.

A função create_app() monta o site: carrega a configuração, liga o banco de
dados, registra as páginas (rotas) e cria as tabelas na primeira execução.
"""
from flask import Flask

from app.config import Config
from app.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Liga o banco de dados ao app.
    db.init_app(app)

    # Registra as páginas do site.
    from app.routes.main import bp as main_bp
    from app.routes.contas import bp as contas_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(contas_bp)

    # Na primeira vez, cria o arquivo do banco e as tabelas (ex.: clientes).
    with app.app_context():
        from app import models  # garante que os modelos sejam conhecidos
        db.create_all()
        _garantir_colunas_sqlite()

    return app


def _garantir_colunas_sqlite():
    """Adiciona ao banco colunas novas que o modelo passou a ter, SEM recriar
    o banco nem apagar dados.

    Isto é uma "mini-migração" só para o SQLite local, que roda no computador
    da usuária. Quando o sistema for para o PostgreSQL (cohab-control), a
    evolução do banco passa a ser feita com Flask-Migrate/Alembic.
    """
    from sqlalchemy import inspect, text

    from app.models.cliente import Cliente

    if db.engine.dialect.name != "sqlite":
        return  # no servidor (PostgreSQL) usamos migrações de verdade

    existentes = {c["name"] for c in inspect(db.engine).get_columns("clientes")}
    novas = [col for col in Cliente.__table__.columns if col.name not in existentes]
    if not novas:
        return
    with db.engine.begin() as conn:
        for col in novas:
            tipo = col.type.compile(db.engine.dialect)
            conn.execute(text(f'ALTER TABLE clientes ADD COLUMN "{col.name}" {tipo}'))
