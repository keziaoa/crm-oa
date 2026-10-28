"""
Script de emergência para redefinir a senha do admin.
Use quando ninguém conseguir mais entrar no sistema.

Uso:
  .venv\Scripts\python.exe resetar_senha.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    admin = Usuario.query.filter_by(login="admin").first()
    if not admin:
        print("Usuário 'admin' não encontrado. Criando...")
        admin = Usuario(nome="Administrador", login="admin")
        db.session.add(admin)

    admin.definir_senha("oa2026")
    admin.ativo = True
    db.session.commit()
    print("Senha do admin redefinida para: oa2026")
    print("Faça login e troque a senha imediatamente.")
