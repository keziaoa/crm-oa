# CRM Comercial ÔA — Guia do Projeto (CLAUDE.md)

> Este arquivo é a "fonte da verdade" do projeto. Ele registra as **regras de
> negócio** que o CRM deve seguir, o **roteiro de fases** e as **decisões de
> arquitetura**. Toda tela ou funcionalidade nova deve respeitar o que está
> aqui. As regras vêm do **Master Kit Comercial ÔA — v6 (26/10/2026)**.

**Responsável comercial:** Kézia (André como apoio).
**Lema da marca:** "Respire. A gestão é com a gente."

---

## 1. O que é este sistema

CRM Comercial da ÔA: um sistema web que roda **só no computador local**
(localhost), para organizar a prospecção e a venda da ÔA Gestão Especializada
para hamburguerias. No futuro será integrado ao **cohab-control** (o sistema
operacional da ÔA) — ver seção "Integração futura com o cohab-control".

- **Linguagem:** Python 3
- **Framework web:** Flask
- **Banco de dados (hoje):** SQLite (arquivo local, em `instance/crm_oa.db`)
- **Banco de dados (futuro):** PostgreSQL (sem refazer o sistema)

---

## 2. ICP — Cliente ideal

- **Segmento:** hamburguerias e **pizzarias independentes**, inclusive com
  **2+ unidades** (multiunidade), com 1 a 3 marcas.
- **Faturamento:** de **R$ 100 mil a R$ 500 mil por mês** (decisão P1, 26/10/2026).
- Redes, franquias e duplicidades **não** entram no ICP.
- **Multiunidade e pizzarias (decisão P4 — DECIDIDO 27/10/2026): SIM, entram
  no ICP**, desde que independentes. Uma conta multiunidade independente pode
  receber **Aderência 2** (não fica mais travada em 1). Só **rede/franquia**
  desqualifica (Aderência 0).
- iFood (nota e avaliações) mede só a "vitrine", **não** comprova faturamento.
  Enquanto não confirmado, faturamento = "A investigar". **Nunca inventar receita.**

---

## 3. Os 17 status do funil (na ordem da aba "Como Usar")

A ÔA não escolhe o status à toa: ele reflete em que ponto a conta está.

### Pipeline (14 status)
1. **Pesquisa** — Pré-contato. Conta encontrada (iFood, Maps, indicação); sem dados confirmados.
2. **Verificar Rede** — Pré-contato. Checando CNPJ, nº de unidades, se é rede/franquia/duplicidade.
3. **Qualificar Porte** — Pré-contato. Independência ok; estimando faturamento e estrutura.
4. **Encontrar Decisor** — Pré-contato. Porte compatível; buscando nome/contato do dono/sócio.
5. **Em Cadência** — Fase 1 · Entrada e qualificação. D0 enviado; cadência D3·D7·D12 em andamento.
6. **Qualificado** — Fase 1. Prioridade A ou B e o decisor aceitou conversar.
7. **Diagnóstico Agendado** — Fase 2 · Diagnóstico comercial. Reunião marcada com data.
8. **Diagnóstico Realizado** — Fase 2. Reunião feita e Ficha de Diagnóstico preenchida.
9. **Proposta Enviada** — Fase 3 · Proposta e negociação. Validade de 10 dias úteis.
10. **Proposta Aceita** — Fase 4 · Aceite e cadastro. Cliente aceitou — ainda NÃO libera nada para a Operação.
11. **Contrato Enviado** — Fase 5 · Contrato. Enviado para assinatura (DocuSign).
12. **Contrato Assinado** — Fase 5. Todas as partes assinaram.
13. **Pagamento Confirmado** — Fase 6 · Cobrança de entrada. Financeiro confirmou Setup / 1ª mensalidade.
14. **Liberado p/ Setup** — Fases 7–8 · Passagem + Gate. Gate com os 8 itens "Sim". **Só aqui a Operação recebe o cliente.**

### Saída (3 status)
15. **Nutrição (60 dias)** — Prioridade C, ou cadência encerrada sem resposta. Retorno em 60 dias.
16. **Perdido** — Era viável, mas não fechou (preço, concorrente, sem prioridade). Registrar motivo.
17. **Desqualificado** — Prioridade D, rede/franquia, duplicada ou fora de escopo. Registrar motivo.

> No código, esta lista está em `app/domain.py` → `STATUS_FUNIL`.

---

## 4. Qualificação — 5 notas (0 a 2) e regra A/B/C/D

Você **não escolhe a letra**: dá 5 notas de 0 a 2 e a soma vira a letra.

| Critério | Pergunta | Nota 0 | Nota 1 | Nota 2 |
|---|---|---|---|---|
| **Aderência** ⚠ | Cabe no que a ÔA faz? | Rede/franquia, tesouraria, contábil fiscal, RH/DP | Dúvida real (ainda falta confirmar independência ou escopo) | Independente (hamburgueria ou pizzaria), inclusive multiunidade, 1–3 marcas |
| **Dor** | O dono sente o problema? | Diz que está tudo ótimo | Admite confusão, sem exemplo | Conta um caso real |
| **Acesso ao decisor** | Fala com quem decide? | Só com funcionário | Com intermediário | Direto com dono/sócio |
| **Viabilidade** ⚠ | Fatura na faixa da ÔA? | Abaixo de R$ 100 mil, ou não quer investir | Não sei (ou acima de R$ 500 mil — validar) | Confirmado entre R$ 100 mil e R$ 500 mil/mês |
| **Colaboração** | Vai mandar os documentos? | Se recusa | Promete, mas desorganizado | Compromete-se a enviar e seguir rotina |

**A soma (máx. 10) vira a letra:**

- **8 a 10 → A** (conta quente): marcar diagnóstico em até 2 dias úteis.
- **5 a 7 → B** (potencial): mais uma conversa curta (geralmente dor ou faturamento).
- **1 a 4 → C** (não é o momento): nutrição, voltar em 60 dias.
- **0 → D** (fora do perfil): descartar e registrar motivo.

**Regra do descarte (eliminatória):** se **Aderência = 0 OU Viabilidade = 0**, a
conta é **D**, mesmo que a soma seja alta. Ex.: dono animado que quer que a ÔA
pague fornecedores → Aderência 0 → D (o dinheiro nunca sai das mãos do dono).

> No código: `app/domain.py` → `calcular_prioridade(...)` e `CRITERIOS_QUALIFICACAO`.

---

## 5. Cadência de prospecção — D0, D3, D7, D12 (dias úteis)

Decisão P5 (26/10/2026): cadência em **dias úteis**. 4 contatos a partir do D0:

- **D0** (dia útil 0) — WhatsApp/Instagram. Abertura com contexto real. Status = Em Cadência.
- **D3** (3º dia útil) — WhatsApp/E-mail. Pergunta direta sobre a dor de rotina.
- **D7** (7º dia útil) — WhatsApp. Prova de valor com exemplo prático (DRE, margem por canal).
- **D12** (12º dia útil) — WhatsApp/E-mail. Encerramento respeitoso → Nutrição (60 dias), motivo "Sem resposta na cadência".

Se responder em qualquer contato: marcar "Respondeu? = Sim", sair da cadência,
seguir pela Próxima Ação.

> No código: `app/domain.py` → `CADENCIA_DIAS_UTEIS` e `proximos_contatos(...)`
> (pula sábados e domingos; feriados ainda não tratados — fase futura).

---

## 6. Ficha de Passagem (Gate) — 8 itens

Só muda para **"Liberado p/ Setup"** quando os **8 itens** estiverem "Sim":

1. **Proposta aprovada** — final enviada e alinhada à tabela oficial (ou exceção do André).
2. **Contrato assinado** — via DocuSign por todas as partes.
3. **Condição financeira** — Setup e 1ª mensalidade confirmados pelo Financeiro.
4. **Cadastro completo** — CNPJ, razão social, contatos financeiro e operacional preenchidos.
5. **Escopo e limites** — Ficha de Diagnóstico anexada, com dor, produto e exclusões claras.
6. **Aceite da Operação** — dossiê revisado no handoff e entrada aceita.
7. **Responsável definido** — analista de implantação designado, com agenda.
8. **Data de kickoff** — data e horário confirmados com o cliente.

> No código: `app/domain.py` → `GATE_ITENS` e `gate_liberado(...)`.

---

## 7. Pós-venda e saúde da conta — marcos a partir do kickoff

Contatos curtos da Comercial (WhatsApp/ligação ~10 min), em **dias corridos**
a partir do kickoff. Só entram contas "Liberado p/ Setup".

| Marco | Nome | Quando | Objetivo |
|---|---|---|---|
| **D+7** | Boas-vindas | 7 dias após kickoff | Kickoff ocorreu? Acessos e documentos chegando? Dúvidas? |
| **D+21** | Pós-diagnóstico | 21 dias | Entendeu o diagnóstico e o plano de Setup? Expectativa fora do escopo? |
| **D+45** | Meio do Setup | 45 dias | Treinamentos/cadastros andando? Algum incômodo antes de virar problema? |
| **D+90** | Fim do Setup | 90 dias | Recebeu 1º fechamento e reunião de gestão? Percebe valor? Pedir depoimento. |
| **D+150** | Renovação | 150 dias | 30 dias antes do fim da fidelidade: continua? Loja/marca extra? Pedir indicação. |

> No código: `app/domain.py` → `MARCOS_POS_VENDA` e `datas_pos_venda(...)`.

---

## 8. Matriz de Oferta & Preços (tabela vigente — 26/10/2026)

| Produto / Serviço | Escopo | Setup (R$) | Mensalidade (R$) | Fidelidade |
|---|---|---|---|---|
| **ÔA Completo** | Financeiro + operacional: DRE, estoque, fichas técnicas, CMV, margem por canal, POPs | 5.000 | 4.200 | 6 meses |
| **ÔA Meu Financeiro** | Financeiro: lançamentos, DRE gerencial, contas a pagar, ponto de equilíbrio | 2.000 | 2.100 | 6 meses |
| **Adicional loja extra** | Unidade física adicional do mesmo grupo | A consultar | 1.200 | mesma do contrato |
| **Adicional marca extra** | Marca virtual extra no mesmo CNPJ/loja | A consultar | 700 | mesma do contrato |

**Regras:** proposta válida por **10 dias úteis**; **sem** desconto promocional
nem mês grátis; escopo só dentro dos 7 pilares; preço de tabela é decisão do
Comercial — qualquer desconto/parcelamento/escopo extra exige **aprovação do André**.

> No código: `app/domain.py` → `PRODUTOS` e `REGRAS_PROPOSTA`.

---

## 9. Identidade visual — cores da marca

| Cor | Código | Uso sugerido |
|---|---|---|
| Verde escuro | `#0E423A` | Cor principal, cabeçalho |
| Areia | `#EFE9DD` | Fundo claro |
| Dourado | `#C58E2A` | Destaques, logo |
| Verde claro | `#5C7C5A` | Apoio, "ok/em dia" |
| Quase preto | `#16130E` | Texto |

> No código: `app/config.py` → `BRAND_COLORS` e `app/static/css/style.css`.

---

## 10. Roteiro das fases do projeto

- [x] **Fase 0 — Fundação (CONCLUÍDA).** Estrutura Python/Flask/SQLite, regras
  de negócio em código (`domain.py`), modelo Cliente com CNPJ único, camada de
  repositórios, página inicial, git iniciado.
- [ ] **Fase 1 — Cadastro de clientes.** Telas para criar/editar/listar contas
  (Conta ID, CNPJ, razão social, contatos financeiro e operacional).
- [ ] **Fase 2 — Importação da Base.** Carregar as 37 contas da triagem iFood
  da planilha para o banco.
- [ ] **Fase 3 — Funil (Kanban).** Mover contas pelos 17 status; validar as
  transições permitidas.
- [ ] **Fase 4 — Qualificação.** Registrar as 5 notas e calcular A/B/C/D
  automaticamente (com a regra eliminatória).
- [ ] **Fase 5 — Cadência.** Agenda de D0/D3/D7/D12 em dias úteis; "próxima ação"
  e alertas de contato atrasado.
- [ ] **Fase 6 — Diagnóstico e Proposta.** Ficha de Diagnóstico (10 blocos) e
  geração de proposta pela Matriz de Oferta.
- [ ] **Fase 7 — Gate (Ficha de Passagem).** Checklist dos 8 itens; só libera
  "Liberado p/ Setup" com os 8 "Sim".
- [ ] **Fase 8 — Pós-venda.** Agenda dos marcos D+7/D+21/D+45/D+90/D+150 e
  saúde da conta.
- [ ] **Fase 9 — Painel e indicadores.** Resumo automático (funil por status,
  prioridades, conversões, por responsável/origem).
- [ ] **Fase 10 — Integração com o cohab-control.** Migração para PostgreSQL e
  conexão de dados pelo CNPJ (ver seção abaixo).

---

## 11. Integração futura com o cohab-control

O cohab-control é o sistema operacional da ÔA. Este CRM será integrado a ele.
As decisões abaixo foram tomadas **desde a Fase 0** para que a integração não
exija refazer o sistema.

### Decisões de identidade e dados
- **CNPJ é o identificador único de negócio** do cliente, além do Conta ID
  legível (CT-001). A busca e a futura ligação com o cohab-control usam o CNPJ.
- O **CNPJ é guardado só com os 14 dígitos** (sem pontos, barra ou traço), para
  casar com o cohab-control sem ambiguidade. A exibição formatada
  (`00.000.000/0000-00`) é calculada na hora (`Cliente.cnpj_formatado`).
- **Razão social** e **contatos financeiro e operacional** ficam em campos
  próprios e padronizados (nome, e-mail, telefone separados), não em texto
  livre — exatamente os dados que o Gate (item 4) e a Operação exigem.
- Telefones também são normalizados por `so_digitos(...)`.

### Decisões de arquitetura (troca de banco sem refazer o sistema)
- Todo acesso ao banco passa pelo **SQLAlchemy** (`app/extensions.py`) e por uma
  **camada de repositórios** (`app/repositories/`). Nenhuma tela escreve SQL direto.
- O banco é escolhido por **configuração**, não por código: a variável de
  ambiente `DATABASE_URL` (ver `app/config.py`). Sem ela, usa SQLite local; com
  ela, usa PostgreSQL. Trocar de banco = mudar essa variável, nada mais.
- No dia da integração, se o cohab-control expuser clientes por uma **API** em
  vez de uma tabela, basta reescrever `ClienteRepository` — o resto do sistema
  (telas, regras) continua igual.
- Para evoluir o esquema do banco sem perder dados, está previsto adotar
  **Flask-Migrate/Alembic** quando a Fase 1 começar.

---

## 12. Como rodar o projeto

```bash
cd crm-oa
source .venv/bin/activate      # Linux/Mac   (no Windows: .venv\Scripts\activate)
python run.py
```

Depois abra o navegador em **http://localhost:5000**.

### Estrutura de pastas
```
crm-oa/
├── app/
│   ├── __init__.py        # monta o Flask (fábrica)
│   ├── config.py          # configuração + escolha do banco (SQLite/PostgreSQL)
│   ├── extensions.py      # o objeto do banco (SQLAlchemy)
│   ├── domain.py          # REGRAS DE NEGÓCIO (status, notas, cadência, gate, preços)
│   ├── models/            # tabelas do banco (Cliente)
│   ├── repositories/      # único lugar que fala com o banco
│   ├── routes/            # páginas do site
│   ├── templates/         # HTML das páginas
│   └── static/            # CSS (cores da marca)
├── instance/              # banco SQLite local (fora do git)
├── run.py                 # inicia o sistema
├── requirements.txt       # bibliotecas necessárias
├── .env.example           # modelo de variáveis de ambiente
└── CLAUDE.md              # este arquivo
```
