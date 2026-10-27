"""
Regras de negócio do CRM Comercial ÔA, em um único lugar.

Este arquivo NÃO desenha telas. Ele apenas guarda, em formato de código, as
regras que vieram do Master Kit Comercial (planilha). As telas das próximas
fases vão importar daqui, para que a regra exista uma vez só e nunca saia do
combinado com o Manual Comercial.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# ICP — cliente ideal
# ---------------------------------------------------------------------------
ICP = {
    "segmento": "Hamburguerias e pizzarias independentes (inclui multiunidade)",
    "faturamento_min_mensal": 100_000,  # R$ 100 mil/mês
    "faturamento_max_mensal": 500_000,  # R$ 500 mil/mês
    # Decisão P4 (27/10/2026): contas com 2+ unidades e pizzarias ENTRAM no ICP,
    # desde que independentes (não rede/franquia). Multiunidade independente
    # pode receber Aderência 2 (não fica mais travada em 1).
    "observacao": ("P4 (27/10/2026): multiunidade e pizzarias independentes "
                   "entram no ICP. Só rede/franquia desqualifica."),
}

# ---------------------------------------------------------------------------
# Os 17 status do funil, NA ORDEM da aba "Como Usar".
# 14 status numerados do pipeline + 3 status de saída.
# ---------------------------------------------------------------------------
STATUS_FUNIL = [
    # (ordem, nome, fase, "pipeline" ou "saida")
    (1, "Pesquisa", "Pré-contato", "pipeline"),
    (2, "Verificar Rede", "Pré-contato", "pipeline"),
    (3, "Qualificar Porte", "Pré-contato", "pipeline"),
    (4, "Encontrar Decisor", "Pré-contato", "pipeline"),
    (5, "Em Cadência", "Fase 1 · Entrada e qualificação", "pipeline"),
    (6, "Qualificado", "Fase 1 · Entrada e qualificação", "pipeline"),
    (7, "Diagnóstico Agendado", "Fase 2 · Diagnóstico comercial", "pipeline"),
    (8, "Diagnóstico Realizado", "Fase 2 · Diagnóstico comercial", "pipeline"),
    (9, "Proposta Enviada", "Fase 3 · Proposta e negociação", "pipeline"),
    (10, "Proposta Aceita", "Fase 4 · Aceite e cadastro", "pipeline"),
    (11, "Contrato Enviado", "Fase 5 · Contrato", "pipeline"),
    (12, "Contrato Assinado", "Fase 5 · Contrato", "pipeline"),
    (13, "Pagamento Confirmado", "Fase 6 · Cobrança de entrada", "pipeline"),
    (14, "Liberado p/ Setup", "Fases 7–8 · Passagem + Gate", "pipeline"),
    (15, "Nutrição (60 dias)", "Saída", "saida"),
    (16, "Perdido", "Saída", "saida"),
    (17, "Desqualificado", "Saída", "saida"),
]

# Lista simples só com os nomes, na ordem — útil para menus suspensos.
STATUS_NOMES = [nome for _, nome, _, _ in STATUS_FUNIL]

# ---------------------------------------------------------------------------
# As 5 notas de qualificação (cada uma de 0 a 2).
# Aderência e Viabilidade são "eliminatórias": 0 em qualquer uma delas = D.
# ---------------------------------------------------------------------------
CRITERIOS_QUALIFICACAO = [
    {"chave": "aderencia", "nome": "Aderência", "elimina_se_zero": True},
    {"chave": "dor", "nome": "Dor", "elimina_se_zero": False},
    {"chave": "acesso_decisor", "nome": "Acesso ao decisor", "elimina_se_zero": False},
    {"chave": "viabilidade", "nome": "Viabilidade", "elimina_se_zero": True},
    {"chave": "colaboracao", "nome": "Colaboração", "elimina_se_zero": False},
]


def calcular_prioridade(aderencia: int, dor: int, acesso_decisor: int,
                        viabilidade: int, colaboracao: int) -> dict:
    """Recebe as 5 notas (0 a 2) e devolve a soma e a letra A/B/C/D.

    Regra do descarte: se Aderência OU Viabilidade for 0, a conta é D,
    mesmo que a soma seja alta.
    """
    notas = [aderencia, dor, acesso_decisor, viabilidade, colaboracao]
    for n in notas:
        if n not in (0, 1, 2):
            raise ValueError("Cada nota deve ser 0, 1 ou 2.")

    soma = sum(notas)

    if aderencia == 0 or viabilidade == 0:
        letra = "D"
    elif soma >= 8:
        letra = "A"
    elif soma >= 5:
        letra = "B"
    elif soma >= 1:
        letra = "C"
    else:  # soma == 0
        letra = "D"

    significado = {
        "A": "Conta quente — marcar diagnóstico em até 2 dias úteis.",
        "B": "Tem potencial — mais uma conversa curta para tirar dúvidas.",
        "C": "Ainda não é o momento — nutrição, voltar em 60 dias.",
        "D": "Fora do perfil — descartar e registrar o motivo.",
    }[letra]

    return {"soma": soma, "letra": letra, "significado": significado}


# ---------------------------------------------------------------------------
# Cadência de prospecção fria: 4 contatos em DIAS ÚTEIS a partir do D0.
# ---------------------------------------------------------------------------
CADENCIA_DIAS_UTEIS = [0, 3, 7, 12]  # D0, D3, D7, D12


def proximos_contatos(data_d0, dias_uteis=CADENCIA_DIAS_UTEIS):
    """A partir da data do D0, calcula as datas de D3, D7 e D12 em DIAS ÚTEIS
    (pula sábados e domingos). Devolve uma lista de (rótulo, data).

    Observação: feriados ainda não são tratados — isso entra numa fase futura.
    """
    from datetime import timedelta

    def soma_dias_uteis(inicio, n):
        if n == 0:
            return inicio
        d = inicio
        restantes = n
        while restantes > 0:
            d = d + timedelta(days=1)
            if d.weekday() < 5:  # 0=segunda ... 4=sexta
                restantes -= 1
        return d

    return [(f"D{n}", soma_dias_uteis(data_d0, n)) for n in dias_uteis]


# ---------------------------------------------------------------------------
# Ficha de Passagem (Gate): os 8 itens obrigatórios.
# Só vira "Liberado p/ Setup" quando os 8 estiverem "Sim".
# ---------------------------------------------------------------------------
GATE_ITENS = [
    "Proposta aprovada — final enviada e alinhada à tabela (ou exceção do André).",
    "Contrato assinado — via DocuSign por todas as partes.",
    "Condição financeira — Setup e 1ª mensalidade confirmados pelo Financeiro.",
    "Cadastro completo — CNPJ, razão social, contatos financeiro e operacional.",
    "Escopo e limites — Ficha de Diagnóstico anexada, com dor, produto e exclusões.",
    "Aceite da Operação — dossiê revisado no handoff e entrada aceita.",
    "Responsável definido — analista de implantação designado, com agenda.",
    "Data de kickoff — data e horário confirmados com o cliente.",
]


def gate_liberado(itens_marcados: list[bool]) -> bool:
    """Devolve True só quando os 8 itens do Gate estiverem marcados como Sim."""
    return len(itens_marcados) == len(GATE_ITENS) and all(itens_marcados)


# ---------------------------------------------------------------------------
# Pós-venda e saúde da conta: marcos contados a partir do kickoff.
# ---------------------------------------------------------------------------
MARCOS_POS_VENDA = [
    {"marco": "D+7", "dias": 7, "nome": "Boas-vindas"},
    {"marco": "D+21", "dias": 21, "nome": "Pós-diagnóstico"},
    {"marco": "D+45", "dias": 45, "nome": "Meio do Setup"},
    {"marco": "D+90", "dias": 90, "nome": "Fim do Setup"},
    {"marco": "D+150", "dias": 150, "nome": "Renovação"},
]


def datas_pos_venda(data_kickoff):
    """A partir da data de kickoff, devolve as datas dos marcos de pós-venda.
    São dias CORRIDOS (diferente da cadência de prospecção, que é dias úteis).
    """
    from datetime import timedelta

    return [
        {**m, "data_prevista": data_kickoff + timedelta(days=m["dias"])}
        for m in MARCOS_POS_VENDA
    ]


# ---------------------------------------------------------------------------
# Matriz de Oferta & Preços (tabela vigente — decidida em 26/10/2026).
# ---------------------------------------------------------------------------
PRODUTOS = [
    {
        "nome": "ÔA Completo",
        "escopo": ("Gestão financeira + operacional integrada: DRE, estoque, "
                   "fichas técnicas, CMV, margem por canal, POPs."),
        "setup": 5000, "mensalidade": 4200, "fidelidade_meses": 6,
        "status": "Liberado (preço de tabela)",
    },
    {
        "nome": "ÔA Meu Financeiro",
        "escopo": ("Organização financeira: lançamentos, DRE gerencial, "
                   "contas a pagar, ponto de equilíbrio."),
        "setup": 2000, "mensalidade": 2100, "fidelidade_meses": 6,
        "status": "Liberado (preço de tabela)",
    },
    {
        "nome": "Adicional loja extra",
        "escopo": "Unidade física adicional do mesmo grupo.",
        "setup": None, "mensalidade": 1200, "fidelidade_meses": 6,
        "status": "Liberado (P4 decidida). Validar capacidade com a Operação antes de propor.",
    },
    {
        "nome": "Adicional marca extra",
        "escopo": "Marca virtual extra no mesmo CNPJ/loja.",
        "setup": None, "mensalidade": 700, "fidelidade_meses": 6,
        "status": "Validar com Operação antes de propor.",
    },
]

# Regras comerciais fixas da proposta.
REGRAS_PROPOSTA = [
    "Proposta válida por 10 dias úteis.",
    "Sem desconto promocional nem mês grátis.",
    "Proposta só com escopo dentro dos 7 pilares.",
    "Qualquer desconto, parcelamento ou escopo extra = aprovação do André.",
]
