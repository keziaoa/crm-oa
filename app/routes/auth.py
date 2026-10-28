"""
Rotas de autenticação e gestão de usuários.

Rotas:
  GET  /login                    -> tela de login
  POST /login                    -> autenticar
  GET  /logout                   -> encerrar sessão
  GET  /minha-conta              -> alterar minha senha
  POST /minha-conta              -> salvar minha senha
  GET  /usuarios                 -> lista de usuários
  GET  /usuarios/novo            -> formulário de novo usuário
  POST /usuarios/novo            -> cria o usuário
  GET  /usuarios/<id>/editar     -> editar nome/login/ativo
  POST /usuarios/<id>/editar     -> salvar edição
  POST /usuarios/<id>/redefinir  -> redefinir senha de outro usuário
  GET  /esqueci-senha            -> instruções de recuperação
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models.usuario import Usuario

bp = Blueprint("auth", __name__)


# --------------------------------------------------------------------------
# Login / Logout
# --------------------------------------------------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        login_val = (request.form.get("login") or "").strip()
        senha = request.form.get("senha") or ""

        usuario = Usuario.query.filter_by(login=login_val).first()

        if usuario and usuario.ativo and usuario.verificar_senha(senha):
            login_user(usuario)
            proximo = request.args.get("next")
            return redirect(proximo or url_for("main.index"))

        flash("Login ou senha incorretos.", "erro")

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada.", "ok")
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------
# Esqueci a senha (instruções de recuperação)
# --------------------------------------------------------------------------
@bp.route("/esqueci-senha")
def esqueci_senha():
    return render_template("auth/esqueci_senha.html")


# --------------------------------------------------------------------------
# Minha conta (alterar própria senha)
# --------------------------------------------------------------------------
@bp.route("/minha-conta", methods=["GET", "POST"])
@login_required
def minha_conta():
    if request.method == "POST":
        senha_atual = request.form.get("senha_atual") or ""
        nova_senha = (request.form.get("nova_senha") or "").strip()
        confirmar = (request.form.get("confirmar_senha") or "").strip()

        if not current_user.verificar_senha(senha_atual):
            flash("Senha atual incorreta.", "erro")
        elif len(nova_senha) < 4:
            flash("A nova senha deve ter pelo menos 4 caracteres.", "erro")
        elif nova_senha != confirmar:
            flash("A nova senha e a confirmação não coincidem.", "erro")
        else:
            current_user.definir_senha(nova_senha)
            db.session.commit()
            flash("Senha alterada com sucesso.", "ok")
            return redirect(url_for("auth.minha_conta"))

    return render_template("auth/minha_conta.html")


# --------------------------------------------------------------------------
# Gestão de usuários
# --------------------------------------------------------------------------
@bp.route("/usuarios")
@login_required
def usuarios():
    lista = Usuario.query.order_by(Usuario.id).all()
    return render_template("auth/usuarios.html", usuarios=lista)


@bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
def novo_usuario():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        login_val = (request.form.get("login") or "").strip()
        senha = (request.form.get("senha") or "").strip()

        erros = []
        if not nome:
            erros.append("O nome é obrigatório.")
        if not login_val:
            erros.append("O login é obrigatório.")
        elif Usuario.query.filter_by(login=login_val).first():
            erros.append(f"Já existe um usuário com o login \"{login_val}\".")
        if len(senha) < 4:
            erros.append("A senha deve ter pelo menos 4 caracteres.")

        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("auth/form_usuario.html", modo="novo",
                                   valores={"nome": nome, "login": login_val})

        u = Usuario(nome=nome, login=login_val)
        u.definir_senha(senha)
        db.session.add(u)
        db.session.commit()
        flash(f"Usuário \"{login_val}\" criado com sucesso.", "ok")
        return redirect(url_for("auth.usuarios"))

    return render_template("auth/form_usuario.html", modo="novo", valores={})


@bp.route("/usuarios/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_usuario(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        abort(404)

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        login_val = (request.form.get("login") or "").strip()
        ativo = request.form.get("ativo") == "1"

        erros = []
        if not nome:
            erros.append("O nome é obrigatório.")
        if not login_val:
            erros.append("O login é obrigatório.")
        else:
            existente = Usuario.query.filter_by(login=login_val).first()
            if existente and existente.id != usuario.id:
                erros.append(f"Já existe outro usuário com o login \"{login_val}\".")

        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("auth/form_usuario.html", modo="editar",
                                   usuario=usuario,
                                   valores={"nome": nome, "login": login_val, "ativo": ativo})

        usuario.nome = nome
        usuario.login = login_val
        usuario.ativo = ativo
        db.session.commit()
        flash(f"Usuário \"{login_val}\" atualizado.", "ok")
        return redirect(url_for("auth.usuarios"))

    return render_template("auth/form_usuario.html", modo="editar",
                           usuario=usuario,
                           valores={"nome": usuario.nome, "login": usuario.login,
                                    "ativo": usuario.ativo})


@bp.route("/usuarios/<int:id>/redefinir", methods=["POST"])
@login_required
def redefinir_senha(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        abort(404)

    nova_senha = (request.form.get("nova_senha") or "").strip()
    if len(nova_senha) < 4:
        flash("A nova senha deve ter pelo menos 4 caracteres.", "erro")
        return redirect(url_for("auth.editar_usuario", id=id))

    usuario.definir_senha(nova_senha)
    db.session.commit()
    flash(f"Senha do usuário \"{usuario.login}\" redefinida.", "ok")
    return redirect(url_for("auth.usuarios"))
