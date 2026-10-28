"""
Fábrica da aplicação Flask.

A função create_app() monta o site: carrega a configuração, liga o banco de
dados, registra as páginas (rotas) e cria as tabelas na primeira execução.
"""
from flask import Flask

from app.config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def carregar_usuario(user_id):
        from app.models.usuario import Usuario
        return db.session.get(Usuario, int(user_id))

    from app.routes.main import bp as main_bp
    from app.routes.contas import bp as contas_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.cadencia import bp as cadencia_bp
    from app.routes.diagnostico import bp as diagnostico_bp
    from app.routes.gate import bp as gate_bp
    from app.routes.pos_venda import bp as pos_venda_bp
    from app.routes.painel import bp as painel_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cadencia_bp)
    app.register_blueprint(diagnostico_bp)
    app.register_blueprint(gate_bp)
    app.register_blueprint(pos_venda_bp)
    app.register_blueprint(painel_bp)

    with app.app_context():
        from app import models  # noqa: F401 — registra as tabelas no SQLAlchemy

        if db.engine.dialect.name == "sqlite":
            db.create_all()
            _garantir_colunas_sqlite()
        # PostgreSQL: as tabelas são criadas via "flask db upgrade" (Alembic).

        try:
            _criar_usuario_padrao()
        except Exception:
            db.session.rollback()

    return app


def _criar_usuario_padrao():
    """Cria o usuário admin na primeira execução, se não existir."""
    from app.models.usuario import Usuario

    if not Usuario.query.filter_by(login="admin").first():
        u = Usuario(nome="Administrador", login="admin")
        u.definir_senha("oa2026")
        db.session.add(u)
        db.session.commit()


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
