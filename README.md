# CRM Comercial ÔA

Sistema web que roda **só no seu computador** (localhost) para organizar a
prospecção e a venda da ÔA Gestão Especializada para hamburguerias.

## Como abrir o sistema

### Windows — jeito fácil (duplo-clique)
1. Instale o Python uma única vez: https://www.python.org/downloads/
   (na instalação, marque **"Add Python to PATH"**).
2. Dê **duplo-clique** no arquivo **`iniciar.bat`** dentro da pasta `crm-oa`.
   - Na primeira vez ele prepara tudo sozinho (pode levar 1–2 minutos).
3. Abra o navegador (Chrome, Edge...) em **http://localhost:5000**.
4. Para desligar, feche a janela preta ou aperte **Ctrl + C**.

### Pelo Terminal (Windows, Mac ou Linux)
1. Entre na pasta do projeto: `cd crm-oa`
2. Ligue o "ambiente": `.venv\Scripts\activate` (Windows) ou `source .venv/bin/activate` (Mac/Linux)
3. Inicie: `python run.py`
4. Abra **http://localhost:5000** no navegador.

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
