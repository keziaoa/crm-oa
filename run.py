"""
Ponto de partida do CRM Comercial ÔA.

Para abrir o sistema, rode no terminal (dentro da pasta crm-oa):

    python run.py

Depois abra o navegador em: http://localhost:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # host 127.0.0.1 = só o seu computador tem acesso (localhost).
    # debug=True mostra erros de forma clara enquanto desenvolvemos.
    app.run(host="127.0.0.1", port=5000, debug=True)
