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
    app.register_blueprint(main_bp)

    # Na primeira vez, cria o arquivo do banco e as tabelas (ex.: clientes).
    with app.app_context():
        from app import models  # garante que os modelos sejam conhecidos
        db.create_all()

    return app
