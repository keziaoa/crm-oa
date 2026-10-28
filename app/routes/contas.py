"""
Telas de cadastro de contas (Fase 1) e Funil Kanban (Fase 3).

Rotas:
  GET  /contas                 -> lista com busca e filtros
  GET  /contas/nova            -> formulário de nova conta
  POST /contas/nova            -> cria a conta
  GET  /contas/<id>            -> detalhe da conta
  GET  /contas/<id>/editar     -> formulário de edição
  POST /contas/<id>/editar     -> salva a edição
  POST /contas/<id>/arquivar   -> arquiva (nunca apaga)
  POST /contas/<id>/desarquivar-> reativa uma conta arquivada
  GET  /contas/funil           -> visão Kanban do funil (Fase 3)
  POST /contas/<id>/mover      -> mover conta de status (Fase 3)
"""
from flask import (Blueprint, abort, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import login_required

from app import domain
from app.importacao import carregar_contas_iniciais, importar_contas_iniciais
from app.models.atividade import TIPOS_ATIVIDADE
from app.models.cliente import Cliente, so_digitos
from app.repositories import atividades, clientes

bp = Blueprint("contas", __name__, url_prefix="/contas")


@bp.before_request
@login_required
def _exigir_login():
    pass


# ----------------------------------------------------------------------------
# Helpers para ler o formulário com segurança
# ----------------------------------------------------------------------------
def _texto(form, campo):
    valor = (form.get(campo) or "").strip()
    return valor or None


def _inteiro(form, campo):
    bruto = (form.get(campo) or "").strip()
    # aceita "180.000" ou "180000"
    bruto = bruto.replace(".", "").replace(" ", "")
    return int(bruto) if bruto.isdigit() else None


def _decimal(form, campo):
    bruto = (form.get(campo) or "").strip().replace(",", ".")
    if not bruto:
        return None
    try:
        return float(bruto)
    except ValueError:
        return None


def _data(form, campo):
    """Lê uma data de um campo <input type=date> (formato AAAA-MM-DD)."""
    from datetime import date
    bruto = (form.get(campo) or "").strip()
    if not bruto:
        return None
    try:
        return date.fromisoformat(bruto)
    except ValueError:
        return None


def _ler_form(form) -> dict:
    """Lê todos os campos do formulário e devolve um dicionário pronto para o
    modelo, já convertendo números."""
    return {
        "nome_fantasia": _texto(form, "nome_fantasia"),
        "cnpj": _texto(form, "cnpj"),
        "razao_social": _texto(form, "razao_social"),
        "confianca_identificacao": _texto(form, "confianca_identificacao"),
        "cidade": _texto(form, "cidade"),
        "segmento": _texto(form, "segmento"),
        "origem": _texto(form, "origem"),
        "triagem_ifood": _texto(form, "triagem_ifood"),
        "nota_ifood": _decimal(form, "nota_ifood"),
        "avaliacoes_ifood": _inteiro(form, "avaliacoes_ifood"),
        "rede_independencia": _texto(form, "rede_independencia"),
        "unidades": _inteiro(form, "unidades"),
        "marcas": _inteiro(form, "marcas"),
        "canais": _texto(form, "canais"),
        "faturamento_estimado": _inteiro(form, "faturamento_estimado"),
        "fonte_faturamento": _texto(form, "fonte_faturamento"),
        "gatilho": _texto(form, "gatilho"),
        "nome_decisor": _texto(form, "nome_decisor"),
        "cargo_decisor": _texto(form, "cargo_decisor"),
        "decisor_confirmado": _texto(form, "decisor_confirmado"),
        "telefone_decisor": _texto(form, "telefone_decisor"),
        "instagram_site": _texto(form, "instagram_site"),
        "email_decisor": _texto(form, "email_decisor"),
        "plano_contratado": _texto(form, "plano_contratado"),
        "data_inicio": _data(form, "data_inicio"),
        "responsavel": _texto(form, "responsavel"),
        "status": _texto(form, "status") or "Pesquisa",
        "proxima_acao": _texto(form, "proxima_acao"),
        "observacoes": _texto(form, "observacoes"),
    }


def _validar(dados, cliente_atual=None) -> list[str]:
    """Devolve a lista de erros (vazia = tudo certo)."""
    erros = []
    if not dados.get("nome_fantasia"):
        erros.append("O nome da empresa / marca é obrigatório.")

    # CNPJ: se preenchido, precisa ter 14 dígitos e ser único.
    cnpj = so_digitos(dados.get("cnpj"))
    if dados.get("cnpj") and (cnpj is None or len(cnpj) != 14):
        erros.append("O CNPJ deve ter 14 dígitos (ex.: 12.225.988/0001-76).")
    elif cnpj:
        existente = clientes.buscar_por_cnpj(cnpj)
        if existente and (cliente_atual is None or existente.id != cliente_atual.id):
            erros.append(f"Já existe uma conta com este CNPJ ({existente.conta_id} — "
                         f"{existente.nome_fantasia}).")

    nota = dados.get("nota_ifood")
    if nota is not None and not (0 <= nota <= 5):
        erros.append("A nota do iFood deve ficar entre 0 e 5.")
    return erros


def _contexto_form():
    """Dados comuns que os formulários precisam (as listas suspensas)."""
    return {"listas": domain.LISTAS}


# ----------------------------------------------------------------------------
# Lista de contas
# ----------------------------------------------------------------------------
@bp.route("/")
def lista():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    prioridade = request.args.get("prioridade", "").strip()
    cidade = request.args.get("cidade", "").strip()
    arquivadas = request.args.get("arquivadas") == "1"
    visao = request.args.get("visao", "").strip()  # "", "ativos" ou "prospeccao"

    contas = clientes.listar(
        q=q or None, status=status or None, prioridade=prioridade or None,
        cidade=cidade or None, incluir_arquivadas=arquivadas,
        visao=visao or None,
    )
    return render_template(
        "contas/lista.html",
        contas=contas,
        q=q, status=status, prioridade=prioridade, cidade=cidade,
        arquivadas=arquivadas, visao=visao,
        total_ativos=clientes.contar_ativos(),
        status_opcoes=domain.STATUS_NOMES,
        prioridade_opcoes=domain.PRIORIDADES,
        cidades=clientes.cidades(),
        status_tipo=domain.STATUS_TIPO,
    )


# ----------------------------------------------------------------------------
# Nova conta
# ----------------------------------------------------------------------------
@bp.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        dados = _ler_form(request.form)
        erros = _validar(dados)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("contas/form.html", valores=dados,
                                   modo="nova", **_contexto_form())
        cliente = clientes.criar(dados)
        flash(f"Conta {cliente.conta_id} criada com sucesso.", "ok")
        return redirect(url_for("contas.detalhe", id=cliente.id))

    # GET: formulário em branco, com um Conta ID de prévia.
    return render_template("contas/form.html", valores={}, modo="nova",
                           proximo_id=clientes.proximo_conta_id(),
                           **_contexto_form())


# ----------------------------------------------------------------------------
# Detalhe
# ----------------------------------------------------------------------------
@bp.route("/<int:id>")
def detalhe(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    from app.repositories import cadencias, diagnosticos, gates, pos_vendas
    cad_ativa = cadencias.cadencia_ativa(cliente.id)
    diag = diagnosticos.buscar_por_cliente(cliente.id)
    gate_obj = gates.buscar_por_cliente(cliente.id)
    pv = pos_vendas.buscar_por_cliente(cliente.id)
    from datetime import date
    lista_atividades = atividades.listar_por_cliente(cliente.id)
    return render_template("contas/detalhe.html", c=cliente,
                           status_tipo=domain.STATUS_TIPO,
                           status_fase=domain.STATUS_FASE,
                           cadencia_ativa=cad_ativa,
                           diagnostico_obj=diag,
                           gate_obj=gate_obj,
                           pos_venda_obj=pv,
                           atividades_lista=lista_atividades,
                           tipos_atividade=TIPOS_ATIVIDADE,
                           hoje=date.today().isoformat())


# ----------------------------------------------------------------------------
# Editar
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    if request.method == "POST":
        dados = _ler_form(request.form)
        erros = _validar(dados, cliente_atual=cliente)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("contas/form.html", valores=dados,
                                   modo="editar", cliente=cliente,
                                   **_contexto_form())
        clientes.atualizar(cliente, dados)
        flash(f"Conta {cliente.conta_id} atualizada.", "ok")
        return redirect(url_for("contas.detalhe", id=cliente.id))

    return render_template("contas/form.html", valores=cliente.para_dict(),
                           modo="editar", cliente=cliente, **_contexto_form())


# ----------------------------------------------------------------------------
# Arquivar / Desarquivar (nunca apagar)
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/arquivar", methods=["POST"])
def arquivar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    clientes.arquivar(cliente)
    flash(f"Conta {cliente.conta_id} arquivada. Ela não aparece mais na lista, "
          f"mas continua guardada.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))


@bp.route("/<int:id>/desarquivar", methods=["POST"])
def desarquivar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    clientes.desarquivar(cliente)
    flash(f"Conta {cliente.conta_id} reativada.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id))


# ----------------------------------------------------------------------------
# Importar as contas iniciais (as 37 da triagem iFood do kit)
# ----------------------------------------------------------------------------
@bp.route("/importar", methods=["GET", "POST"])
def importar():
    if request.method == "POST":
        resumo = importar_contas_iniciais()
        if resumo["importadas"]:
            flash(f"{resumo['importadas']} conta(s) importada(s) com sucesso.", "ok")
        if resumo["puladas"]:
            flash(f"{resumo['puladas']} conta(s) já existiam e foram puladas "
                  f"(não duplicamos nada).", "ok")
        if not resumo["importadas"] and not resumo["puladas"]:
            flash("Nada para importar.", "ok")
        return redirect(url_for("contas.lista"))

    disponiveis = len(carregar_contas_iniciais())
    return render_template("contas/importar.html",
                           disponiveis=disponiveis,
                           total_atual=clientes.contar(incluir_arquivadas=True))


# ----------------------------------------------------------------------------
# Funil Kanban (Fase 3)
# ----------------------------------------------------------------------------
@bp.route("/funil")
def funil():
    agrupado = clientes.agrupar_por_status()
    transicoes = {nome: domain.transicoes_validas(nome) for nome in domain.STATUS_NOMES}
    proximo = {nome: domain.proximo_status(nome) for nome in domain.STATUS_NOMES}
    return render_template(
        "contas/funil.html",
        status_funil=domain.STATUS_FUNIL,
        agrupado=agrupado,
        status_tipo=domain.STATUS_TIPO,
        status_fase=domain.STATUS_FASE,
        transicoes=transicoes,
        proximo=proximo,
    )


@bp.route("/<int:id>/mover", methods=["POST"])
def mover(id):
    """Muda o status de uma conta. Aceita tanto form POST quanto JSON (AJAX)."""
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    eh_json = request.is_json
    novo_status = (request.json or {}).get("status") if eh_json else request.form.get("status")

    if not novo_status:
        msg = "Status de destino não informado."
        return (jsonify({"erro": msg}), 400) if eh_json else (flash(msg, "erro"), redirect(url_for("contas.funil")))[1]

    validos = domain.transicoes_validas(cliente.status)
    if novo_status not in validos:
        msg = f"Não é possível mover de \"{cliente.status}\" para \"{novo_status}\"."
        if eh_json:
            return jsonify({"erro": msg}), 400
        flash(msg, "erro")
        return redirect(url_for("contas.funil"))

    status_anterior = cliente.status
    clientes.alterar_status(cliente, novo_status)

    if eh_json:
        return jsonify({
            "ok": True,
            "conta_id": cliente.conta_id,
            "nome": cliente.nome_fantasia,
            "de": status_anterior,
            "para": novo_status,
        })

    flash(f"{cliente.conta_id} movida de \"{status_anterior}\" para \"{novo_status}\".", "ok")
    return redirect(url_for("contas.funil"))


# ----------------------------------------------------------------------------
# Qualificação (Fase 4) — registrar as 5 notas e calcular A/B/C/D
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/qualificar", methods=["GET", "POST"])
def qualificar(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    criterios = domain.CRITERIOS_QUALIFICACAO

    if request.method == "POST":
        notas = {}
        erros = []
        for c in criterios:
            campo = f"nota_{c['chave']}"
            bruto = (request.form.get(campo) or "").strip()
            if bruto == "":
                erros.append(f"A nota de {c['nome']} é obrigatória.")
                continue
            val = int(bruto)
            if val not in (0, 1, 2):
                erros.append(f"A nota de {c['nome']} deve ser 0, 1 ou 2.")
                continue
            notas[campo] = val

        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template(
                "contas/qualificar.html", c=cliente, criterios=criterios,
                valores={f"nota_{cr['chave']}": request.form.get(f"nota_{cr['chave']}")
                         for cr in criterios},
            )

        resultado = domain.calcular_prioridade(
            notas["nota_aderencia"], notas["nota_dor"],
            notas["nota_acesso_decisor"], notas["nota_viabilidade"],
            notas["nota_colaboracao"],
        )

        clientes.salvar_qualificacao(cliente, notas, resultado["letra"])

        flash(f"{cliente.conta_id} qualificada: {resultado['letra']} "
              f"(soma {resultado['soma']}/10). {resultado['significado']}", "ok")
        return redirect(url_for("contas.detalhe", id=cliente.id))

    valores = {f"nota_{c['chave']}": getattr(cliente, f"nota_{c['chave']}")
               for c in criterios}
    return render_template(
        "contas/qualificar.html", c=cliente, criterios=criterios,
        valores=valores,
    )


# ----------------------------------------------------------------------------
# Histórico de Atividades
# ----------------------------------------------------------------------------
@bp.route("/<int:id>/atividade", methods=["POST"])
def nova_atividade(id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)

    data = _data(request.form, "data")
    tipo = _texto(request.form, "tipo")
    resumo = _texto(request.form, "resumo")

    erros = []
    if not data:
        erros.append("A data da atividade é obrigatória.")
    if not tipo or tipo not in TIPOS_ATIVIDADE:
        erros.append("Selecione o tipo da atividade.")
    if not resumo:
        erros.append("O resumo é obrigatório.")

    if erros:
        for e in erros:
            flash(e, "erro")
        return redirect(url_for("contas.detalhe", id=cliente.id) + "#atividades")

    atividades.criar(cliente.id, data, tipo, resumo)
    flash("Atividade registrada.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id) + "#atividades")


@bp.route("/<int:id>/atividade/<int:atv_id>/excluir", methods=["POST"])
def excluir_atividade(id, atv_id):
    cliente = clientes.buscar_por_id(id)
    if not cliente:
        abort(404)
    atv = atividades.obter(atv_id)
    if not atv or atv.cliente_id != cliente.id:
        abort(404)
    atividades.excluir(atv)
    flash("Atividade excluída.", "ok")
    return redirect(url_for("contas.detalhe", id=cliente.id) + "#atividades")
