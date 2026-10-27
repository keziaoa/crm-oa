"""
Configuração central do CRM Comercial ÔA.

Aqui fica a decisão de QUAL banco de dados usar. Hoje é o SQLite (um arquivo
local, sem instalar nada). No futuro, para integrar ao cohab-control, basta
definir a variável de ambiente DATABASE_URL apontando para o PostgreSQL — o
resto do sistema NÃO muda, porque todo o acesso aos dados passa pelo
SQLAlchemy e pela camada de repositórios.
"""
import os
from pathlib import Path

# Pasta onde este projeto vive (a pasta crm-oa).
BASE_DIR = Path(__file__).resolve().parent.parent

# A pasta "instance" guarda dados locais (o arquivo do banco SQLite).
# Fica fora do controle de versão (git) para não subir dados de clientes.
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


def _database_url() -> str:
    """Decide o endereço do banco de dados.

    - Se existir a variável de ambiente DATABASE_URL (ex.: no dia da
      integração com o cohab-control), usamos ela (PostgreSQL).
    - Senão, usamos um arquivo SQLite local em instance/crm_oa.db.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # Alguns serviços entregam a URL começando com "postgres://";
        # o SQLAlchemy moderno espera "postgresql://". Normalizamos aqui.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{INSTANCE_DIR / 'crm_oa.db'}"


class Config:
    # Chave usada pelo Flask para proteger sessões. Em produção, defina
    # SECRET_KEY no ambiente; o valor abaixo serve só para o uso local.
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-no-futuro")

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Identidade visual da marca ÔA (cores oficiais), disponível para as telas.
    BRAND_COLORS = {
        "verde_escuro": "#0E423A",
        "areia": "#EFE9DD",
        "dourado": "#C58E2A",
        "verde_claro": "#5C7C5A",
        "quase_preto": "#16130E",
    }
