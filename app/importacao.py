"""
Importação das contas iniciais (as 37 da triagem iFood do Master Kit).

Os dados foram extraídos uma vez da planilha e guardados em
app/data/contas_iniciais.json. Isto evita depender do Excel ou de instalar
bibliotecas extras no computador da usuária — a importação é um clique.

A importação é SEGURA: se rodar de novo, não duplica. Ela pula contas cujo
Conta ID (CT-00x) ou CNPJ já existem no banco.
"""
import json
from pathlib import Path

from app.extensions import db
from app.models.cliente import Cliente, so_digitos

ARQUIVO = Path(__file__).parent / "data" / "contas_iniciais.json"


def carregar_contas_iniciais() -> list[dict]:
    with open(ARQUIVO, encoding="utf-8") as f:
        return json.load(f)


def importar_contas_iniciais() -> dict:
    """Insere as contas iniciais que ainda não existem. Devolve um resumo."""
    dados = carregar_contas_iniciais()

    existentes_id = {c for (c,) in
                     Cliente.query.with_entities(Cliente.conta_id).all()}
    existentes_cnpj = {c for (c,) in
                       Cliente.query.with_entities(Cliente.cnpj).all() if c}

    novos, importadas, puladas = [], 0, 0
    for linha in dados:
        cnpj = so_digitos(linha.get("cnpj"))
        ja_existe = (linha["conta_id"] in existentes_id
                     or (cnpj and cnpj in existentes_cnpj))
        if ja_existe:
            puladas += 1
            continue
        campos = dict(linha)
        campos["cnpj"] = cnpj
        novos.append(Cliente(**campos))
        if cnpj:
            existentes_cnpj.add(cnpj)
        existentes_id.add(linha["conta_id"])
        importadas += 1

    if novos:
        db.session.add_all(novos)
        db.session.commit()

    return {"total": len(dados), "importadas": importadas, "puladas": puladas}
