# CRM Comercial ÔA

Sistema web que roda **só no seu computador** (localhost) para organizar a
prospecção e a venda da ÔA Gestão Especializada para hamburguerias.

## Como abrir o sistema (passo a passo)

1. Abra o **Terminal** e entre na pasta do projeto:
   ```bash
   cd crm-oa
   ```
2. Ligue o "ambiente" do projeto (onde o Flask está instalado):
   - **Linux ou Mac:** `source .venv/bin/activate`
   - **Windows:** `.venv\Scripts\activate`
3. Inicie o sistema:
   ```bash
   python run.py
   ```
4. Abra o navegador (Chrome, Edge...) e acesse:
   **http://localhost:5000**

Para desligar o sistema, volte ao Terminal e aperte **Ctrl + C**.

## Primeira vez (só se o Flask ainda não estiver instalado)

```bash
cd crm-oa
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Onde estão as regras do negócio

Tudo o que o CRM deve seguir (os 17 status, as 5 notas, a cadência, o Gate,
preços e o roteiro das fases) está no arquivo **`CLAUDE.md`**.
