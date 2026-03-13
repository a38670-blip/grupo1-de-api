**import sqlite3
import random
import re
import urllib.parse
import urllib.request
import json
from datetime import datetime

# -----------------------
# BASE DE DADOS
# -----------------------

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    nome TEXT,
    apelido TEXT,
    email TEXT UNIQUE,
    telefone TEXT UNIQUE,
    pais TEXT,
    username TEXT UNIQUE,
    password TEXT,
    perfil_publico INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    simbolo TEXT,
    tipo TEXT,
    pais TEXT,
    moeda TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contas (
    user_id TEXT PRIMARY KEY,
    saldo REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    tipo TEXT,
    valor REAL,
    descricao TEXT,
    criado_em TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    asset_id INTEGER,
    quantidade REAL,
    preco_compra REAL,
    data_compra TEXT,
    moeda_compra TEXT
)
""")

conn.commit()

# -----------------------
# PAÍSES
# -----------------------

paises = {
    "1": ("Portugal", "+351"),
    "2": ("Brasil", "+55"),
    "3": ("Espanha", "+34"),
    "4": ("Estados Unidos", "+1"),
    "5": ("Reino Unido", "+44")
}

# -----------------------
# CATÁLOGO SIMPLES
# -----------------------

CATALOGO = {
    "Estados Unidos": {
        "Tecnologia": [
            "Apple",
            "Microsoft",
            "Alphabet",
            "Nvidia"
        ],
        "Saúde": [
            "Johnson & Johnson",
            "Pfizer",
            "UnitedHealth Group"
        ]
    },
    "Global": {
        "Criptomoedas": [
            "Bitcoin",
            "Ethereum"
        ]
    }
}

SIMBOLOS_SUGERIDOS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet": "GOOGL",
    "Nvidia": "NVDA",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "UnitedHealth Group": "UNH"
}

MOEDAS_DISPONIVEIS = [
    "USD","EUR","GBP","BRL","CAD","CHF","JPY"
]

# -----------------------
# FUNÇÕES BASE
# -----------------------

def gerar_id():
    return str(random.randint(100000,999999))


def validar_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(padrao,email)


def valor_float(msg):

    while True:

        texto=input(msg).strip().replace(",",".")
        if texto=="0":
            return None

        try:
            val=float(texto)

            if val<0:
                print("Valor não pode ser negativo.")
                continue

            return val

        except ValueError:
            print("Valor inválido.")


def garantir_conta(user_id):
    cursor.execute("INSERT OR IGNORE INTO contas (user_id,saldo) VALUES (?,0)",(user_id,))
    conn.commit()


def saldo_atual(user_id):

    garantir_conta(user_id)

    cursor.execute(
        "SELECT saldo FROM contas WHERE user_id=?",
        (user_id,)
    )

    return float(cursor.fetchone()[0])


# -----------------------
# PREÇO EM TEMPO REAL
# -----------------------

def preco_tempo_real(simbolo):

    if not simbolo:
        return None

    try:

        query=urllib.parse.quote(simbolo)

        url=f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={query}"

        with urllib.request.urlopen(url,timeout=5) as resp:

            data=json.loads(resp.read().decode("utf-8"))

        result=data["quoteResponse"]["result"]

        if not result:
            return None

        return result[0]["regularMarketPrice"]

    except:
        return None


# -----------------------
# ESCOLHER PAÍS
# -----------------------

def escolher_pais():

    while True:

        print("\nEscolhe o país:")

        for k,v in paises.items():
            print(k,"-",v[0],v[1])

        escolha=input("Escolha (ou 0 para voltar): ")

        if escolha=="0":
            return None,None

        if escolha in paises:
            return paises[escolha]

        print("Opção inválida.")


# -----------------------
# REGISTO
# -----------------------

def registar():

    user_id=gerar_id()

    nome=input("Nome (0 para voltar): ")
    if nome=="0":
        return

    apelido=input("Apelido (0 para voltar): ")
    if apelido=="0":
        return

    pais,prefixo=escolher_pais()
    if pais is None:
        return

    while True:

        telefone=input(f"Número de telemóvel ({prefixo}) ou 0 para voltar: ")

        if telefone=="0":
            return

        telefone_completo=prefixo+telefone

        cursor.execute(
            "SELECT * FROM users WHERE telefone=?",
            (telefone_completo,)
        )

        if cursor.fetchone():
            print("Este número já foi utilizado.")
        else:
            break

    while True:

        email=input("Email (0 para voltar): ")

        if email=="0":
            return

        if not validar_email(email):
            print("Email inválido.")
            continue

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        if cursor.fetchone():
            print("Este email já está registado.")
        else:
            break

    username=input("Username: ")

    password=input("Password (min 6 caracteres): ")

    if len(password)<6:
        print("Password demasiado curta.")
        return

    perfil=input("Perfil público? (s/n): ")
    perfil_publico=1 if perfil.lower()=="s" else 0

    cursor.execute(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id,nome,apelido,email,telefone_completo,pais,username,password,perfil_publico)
    )

    conn.commit()

    garantir_conta(user_id)

    print("\nConta criada com sucesso!")
    print("O teu ID é:",user_id)


# -----------------------
# LOGIN
# -----------------------

def login():

    print("\n=== LOGIN ===")

    user=input("Username ou ID: ")

    password=input("Password: ")

    cursor.execute(
        """
        SELECT * FROM users
        WHERE (username=? OR id=?)
        AND password=?
        """,
        (user,user,password)
    )

    result=cursor.fetchone()

    if result:
        print("Login feito com sucesso!")
        menu_user(result)
    else:
        print("Dados incorretos.")


# -----------------------
# SALDO
# -----------------------

def ver_saldo(user_id):
    print(f"Saldo atual: {saldo_atual(user_id):.2f}")


def inserir_saldo(user_id):

    valor=valor_float("Valor a inserir (0 para voltar): ")

    if valor is None:
        return

    saldo=saldo_atual(user_id)+valor

    cursor.execute(
        "UPDATE contas SET saldo=? WHERE user_id=?",
        (saldo,user_id)
    )

    conn.commit()

    print("Saldo atualizado com sucesso.")


# -----------------------
# MENU UTILIZADOR
# -----------------------

def menu_user(user):

    garantir_conta(user[0])

    while True:

        print("\n=== MENU ===")

        print("1 - Ver saldo")
        print("2 - Inserir saldo")
        print("3 - Ver moedas disponíveis")
        print("0 - Logout")

        op=input("Escolha: ")

        if op=="1":
            ver_saldo(user[0])

        elif op=="2":
            inserir_saldo(user[0])

        elif op=="3":
            print(", ".join(MOEDAS_DISPONIVEIS))

        elif op=="0":
            break


# -----------------------
# MENU PRINCIPAL
# -----------------------

while True:

    print("\n=== APP INVEST ===")

    print("1 - Login")
    print("2 - Criar conta")
    print("0 - Sair")

    op=input("Escolha: ")

    if op=="1":
        login()

    elif op=="2":
        registar()

    elif op=="0":
        break

conn.close()**
