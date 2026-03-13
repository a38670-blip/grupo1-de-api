import sqlite3
import random
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime

DB_NAME = "app_invest.db"

# -----------------------
# BASE DE DADOS
# -----------------------

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    apelido TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    telefone TEXT UNIQUE NOT NULL,
    pais TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    perfil_publico INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contas (
    user_id TEXT PRIMARY KEY,
    saldo REAL DEFAULT 0,
    moeda_base TEXT DEFAULT 'EUR',
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    valor REAL NOT NULL,
    moeda TEXT NOT NULL,
    descricao TEXT,
    criado_em TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    simbolo TEXT,
    tipo TEXT NOT NULL,
    pais TEXT NOT NULL,
    moeda TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    asset_id INTEGER NOT NULL,
    quantidade REAL NOT NULL,
    preco_compra REAL NOT NULL,
    moeda_compra TEXT NOT NULL,
    data_compra TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(asset_id) REFERENCES assets(id)
)
""")

conn.commit()

# -----------------------
# DADOS
# -----------------------

PAISES = {
    "1": ("Portugal", "+351"),
    "2": ("Brasil", "+55"),
    "3": ("Espanha", "+34"),
    "4": ("Estados Unidos", "+1"),
    "5": ("Reino Unido", "+44"),
    "6": ("Canadá", "+1"),
    "7": ("Alemanha", "+49"),
    "8": ("França", "+33"),
    "9": ("Itália", "+39"),
    "10": ("Suíça", "+41")
}

MOEDAS_DISPONIVEIS = [
    "EUR", "USD", "GBP", "BRL", "CAD", "CHF", "JPY", "AUD",
    "NZD", "SEK", "NOK", "DKK", "PLN", "CNY", "HKD", "SGD"
]

CATALOGO = {
    "Estados Unidos": {
        "Ações - Tecnologia": [
            "Apple", "Microsoft", "Alphabet", "Nvidia", "Meta Platforms", "Amazon", "Tesla",
            "Adobe", "Oracle", "Salesforce", "Cisco Systems", "Intel", "AMD", "Qualcomm",
            "IBM", "Palantir", "Snowflake", "ServiceNow", "CrowdStrike", "Datadog", "MongoDB"
        ],
        "Ações - Bancos": [
            "JPMorgan Chase", "Bank of America", "Wells Fargo", "Citigroup", "Goldman Sachs",
            "Morgan Stanley", "American Express", "Visa", "Mastercard", "PayPal", "BlackRock"
        ],
        "Ações - Saúde": [
            "Johnson & Johnson", "Pfizer", "Merck", "AbbVie", "Eli Lilly", "Amgen",
            "Gilead Sciences", "Moderna", "UnitedHealth Group", "Humana", "Boston Scientific"
        ],
        "Ações - Energia": [
            "Exxon Mobil", "Chevron", "ConocoPhillips", "Occidental Petroleum",
            "Marathon Petroleum", "Valero Energy", "Kinder Morgan", "Halliburton"
        ]
    },
    "Europa": {
        "Ações": [
            "Banco Santander", "BBVA", "Deutsche Bank", "Siemens", "Volkswagen", "BMW",
            "SAP", "BNP Paribas", "Airbus", "LVMH", "HSBC", "Barclays", "Shell",
            "UBS Group", "Nestlé", "ASML", "Nokia"
        ]
    },
    "Brasil": {
        "Ações": [
            "Itaú Unibanco", "Banco Bradesco", "Banco do Brasil", "Petrobras",
            "Eletrobras", "Totvs", "StoneCo", "PagSeguro"
        ]
    },
    "Portugal": {
        "Ações": [
            "Banco Comercial Português (Millennium BCP)", "Banco BPI", "Banco Santander Totta",
            "EDP – Energias de Portugal", "Galp Energia", "Jerónimo Martins", "Sonae SGPS"
        ]
    },
    "Global": {
        "Criptomoedas": [
            "Bitcoin", "Ethereum", "Tether", "BNB", "Solana", "XRP", "Cardano",
            "Dogecoin", "Polkadot", "Litecoin", "Chainlink", "Avalanche"
        ],
        "Matérias-primas": [
            "Ouro", "Prata", "Platina", "Paládio", "Cobre", "Petróleo Brent",
            "Petróleo WTI", "Gás Natural", "Milho", "Trigo", "Café", "Cacau"
        ],
        "Índices": [
            "S&P 500", "NASDAQ 100", "Dow Jones Industrial Average", "Russell 2000",
            "DAX 40", "CAC 40", "FTSE 100", "IBEX 35", "Euro Stoxx 50"
        ]
    }
}

SIMBOLOS_SUGERIDOS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet": "GOOGL",
    "Nvidia": "NVDA",
    "Meta Platforms": "META",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Adobe": "ADBE",
    "Oracle": "ORCL",
    "Salesforce": "CRM",
    "Cisco Systems": "CSCO",
    "Intel": "INTC",
    "AMD": "AMD",
    "Qualcomm": "QCOM",
    "IBM": "IBM",
    "Palantir": "PLTR",
    "Snowflake": "SNOW",
    "ServiceNow": "NOW",
    "CrowdStrike": "CRWD",
    "Datadog": "DDOG",
    "MongoDB": "MDB",

    "JPMorgan Chase": "JPM",
    "Bank of America": "BAC",
    "Wells Fargo": "WFC",
    "Citigroup": "C",
    "Goldman Sachs": "GS",
    "Morgan Stanley": "MS",
    "American Express": "AXP",
    "Visa": "V",
    "Mastercard": "MA",
    "PayPal": "PYPL",
    "BlackRock": "BLK",

    "Johnson & Johnson": "JNJ",
    "Pfizer": "PFE",
    "Merck": "MRK",
    "AbbVie": "ABBV",
    "Eli Lilly": "LLY",
    "Amgen": "AMGN",
    "Gilead Sciences": "GILD",
    "Moderna": "MRNA",
    "UnitedHealth Group": "UNH",
    "Humana": "HUM",
    "Boston Scientific": "BSX",

    "Exxon Mobil": "XOM",
    "Chevron": "CVX",
    "ConocoPhillips": "COP",
    "Occidental Petroleum": "OXY",
    "Marathon Petroleum": "MPC",
    "Valero Energy": "VLO",
    "Kinder Morgan": "KMI",
    "Halliburton": "HAL",

    "Banco Santander": "SAN",
    "BBVA": "BBVA",
    "Deutsche Bank": "DB",
    "Siemens": "SIEGY",
    "Volkswagen": "VWAGY",
    "BMW": "BMWYY",
    "SAP": "SAP",
    "BNP Paribas": "BNPQY",
    "Airbus": "EADSY",
    "LVMH": "LVMUY",
    "HSBC": "HSBC",
    "Barclays": "BCS",
    "Shell": "SHEL",
    "UBS Group": "UBS",
    "Nestlé": "NSRGY",
    "ASML": "ASML",
    "Nokia": "NOK",

    "Itaú Unibanco": "ITUB",
    "Banco Bradesco": "BBD",
    "Banco do Brasil": "BDORY",
    "Petrobras": "PBR",
    "Eletrobras": "EBR",
    "Totvs": "TOTS3.SA",
    "StoneCo": "STNE",
    "PagSeguro": "PAGS",

    "Banco Comercial Português (Millennium BCP)": "BCP.LS",
    "Banco BPI": "",
    "Banco Santander Totta": "",
    "EDP – Energias de Portugal": "EDPFY",
    "Galp Energia": "GLPEY",
    "Jerónimo Martins": "JRONY",
    "Sonae SGPS": "",

    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Tether": "USDT-USD",
    "BNB": "BNB-USD",
    "Solana": "SOL-USD",
    "XRP": "XRP-USD",
    "Cardano": "ADA-USD",
    "Dogecoin": "DOGE-USD",
    "Polkadot": "DOT-USD",
    "Litecoin": "LTC-USD",
    "Chainlink": "LINK-USD",
    "Avalanche": "AVAX-USD",

    "Ouro": "GC=F",
    "Prata": "SI=F",
    "Platina": "PL=F",
    "Paládio": "PA=F",
    "Cobre": "HG=F",
    "Petróleo Brent": "BZ=F",
    "Petróleo WTI": "CL=F",
    "Gás Natural": "NG=F",
    "Milho": "ZC=F",
    "Trigo": "ZW=F",
    "Café": "KC=F",
    "Cacau": "CC=F",

    "S&P 500": "^GSPC",
    "NASDAQ 100": "^NDX",
    "Dow Jones Industrial Average": "^DJI",
    "Russell 2000": "^RUT",
    "DAX 40": "^GDAXI",
    "CAC 40": "^FCHI",
    "FTSE 100": "^FTSE",
    "IBEX 35": "^IBEX",
    "Euro Stoxx 50": "^STOXX50E"
}

# -----------------------
# FUNÇÕES BASE
# -----------------------

def gerar_id():
    return str(random.randint(100000, 999999))

def validar_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

def input_password(msg="Password: "):
    return input(msg)

def agora_iso():
    return datetime.now().isoformat(timespec="seconds")

def valor_float(msg):
    while True:
        texto = input(msg).strip().replace(",", ".")
        if texto == "0":
            return None
        try:
            val = float(texto)
            if val < 0:
                print("Valor não pode ser negativo.")
                continue
            return val
        except ValueError:
            print("Valor inválido.")

def garantir_conta(user_id):
    cursor.execute("INSERT OR IGNORE INTO contas (user_id, saldo, moeda_base) VALUES (?, 0, 'EUR')", (user_id,))
    conn.commit()

def saldo_atual(user_id):
    garantir_conta(user_id)
    cursor.execute("SELECT saldo FROM contas WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return float(row[0]) if row else 0.0

def moeda_base_user(user_id):
    garantir_conta(user_id)
    cursor.execute("SELECT moeda_base FROM contas WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else "EUR"

def set_moeda_base(user_id, moeda):
    cursor.execute("UPDATE contas SET moeda_base=? WHERE user_id=?", (moeda, user_id))
    conn.commit()

def format_money(valor, moeda):
    return f"{valor:,.2f} {moeda}".replace(",", "X").replace(".", ",").replace("X", ".")

# -----------------------
# APIs
# -----------------------

def fetch_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def preco_tempo_real(simbolo):
    if not simbolo:
        return None
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(simbolo)}"
    data = fetch_json(url)
    if not data:
        return None
    try:
        result = data["quoteResponse"]["result"]
        if not result:
            return None
        return result[0].get("regularMarketPrice")
    except Exception:
        return None

def fx_rate(base, target):
    base = base.upper()
    target = target.upper()
    if base == target:
        return 1.0

    url = f"https://api.exchangerate.host/convert?from={urllib.parse.quote(base)}&to={urllib.parse.quote(target)}&amount=1"
    data = fetch_json(url)
    if data:
        result = data.get("result")
        if isinstance(result, (int, float)) and result > 0:
            return float(result)

    url2 = f"https://open.er-api.com/v6/latest/{urllib.parse.quote(base)}"
    data2 = fetch_json(url2)
    if data2 and data2.get("rates", {}).get(target):
        return float(data2["rates"][target])

    return None

def converter_moeda(valor, moeda_origem, moeda_destino):
    rate = fx_rate(moeda_origem, moeda_destino)
    if rate is None:
        return None
    return valor * rate

# -----------------------
# SEED DE ASSETS
# -----------------------

def semear_assets_iniciais():
    cursor.execute("SELECT COUNT(*) FROM assets")
    total = cursor.fetchone()[0]
    if total > 0:
        return

    inseridos = 0
    for pais, grupos in CATALOGO.items():
        for tipo, nomes in grupos.items():
            for nome in nomes:
                simbolo = SIMBOLOS_SUGERIDOS.get(nome, "")
                moeda = "USD" if pais in ["Estados Unidos", "Global", "Europa"] else "EUR"
                if pais == "Brasil":
                    moeda = "BRL"
                elif pais == "Portugal":
                    moeda = "EUR"
                cursor.execute("""
                    INSERT INTO assets (nome, simbolo, tipo, pais, moeda)
                    VALUES (?, ?, ?, ?, ?)
                """, (nome, simbolo, tipo, pais, moeda))
                inseridos += 1

    conn.commit()
    print(f"Catálogo inicial carregado: {inseridos} ativos.")

# -----------------------
# REGISTO / LOGIN
# -----------------------

def escolher_pais():
    while True:
        print("\nEscolhe o país:")
        for k, v in PAISES.items():
            print(f"{k} - {v[0]} {v[1]}")
        escolha = input("Escolha (ou 0 para voltar): ").strip()
        if escolha == "0":
            return None, None
        if escolha in PAISES:
            return PAISES[escolha]
        print("Opção inválida.")

def registar():
    user_id = gerar_id()

    nome = input("Nome (0 para voltar): ").strip()
    if nome == "0":
        return

    apelido = input("Apelido (0 para voltar): ").strip()
    if apelido == "0":
        return

    pais, prefixo = escolher_pais()
    if pais is None:
        return

    while True:
        telefone = input(f"Número de telemóvel ({prefixo}) ou 0 para voltar: ").strip()
        if telefone == "0":
            return
        telefone_completo = prefixo + telefone

        cursor.execute("SELECT 1 FROM users WHERE telefone=?", (telefone_completo,))
        if cursor.fetchone():
            print("Este número já foi utilizado.")
        else:
            break

    while True:
        email = input("Email (0 para voltar): ").strip()
        if email == "0":
            return
        if not validar_email(email):
            print("Email inválido.")
            continue
        cursor.execute("SELECT 1 FROM users WHERE email=?", (email,))
        if cursor.fetchone():
            print("Este email já está registado.")
        else:
            break

    while True:
        username = input("Username: ").strip()
        if not username:
            print("Username inválido.")
            continue
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            print("Esse username já existe.")
        else:
            break

    password = input_password("Password (min 6 caracteres): ")
    if len(password) < 6:
        print("Password demasiado curta.")
        return

    perfil = input("Perfil público? (s/n): ").strip().lower()
    perfil_publico = 1 if perfil == "s" else 0

    moeda = input("Moeda base da conta (Enter=EUR): ").strip().upper()
    if not moeda:
        moeda = "EUR"
    if moeda not in MOEDAS_DISPONIVEIS:
        print("Moeda inválida. Vai ficar EUR.")
        moeda = "EUR"

    try:
        cursor.execute("""
            INSERT INTO users (id, nome, apelido, email, telefone, pais, username, password, perfil_publico)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, nome, apelido, email, telefone_completo, pais, username, password, perfil_publico))

        cursor.execute("""
            INSERT INTO contas (user_id, saldo, moeda_base)
            VALUES (?, 0, ?)
        """, (user_id, moeda))

        conn.commit()
        print("\nConta criada com sucesso!")
        print("O teu ID é:", user_id)
    except Exception as e:
        print("Erro ao criar conta:", e)

def login():
    print("\n=== LOGIN ===")
    user = input("Username ou ID: ").strip()
    password = input_password("Password: ")

    cursor.execute("""
        SELECT * FROM users
        WHERE (username=? OR id=?)
        AND password=?
    """, (user, user, password))

    result = cursor.fetchone()
    if result:
        print("Login feito com sucesso!")
        menu_user(result)
    else:
        print("Dados incorretos.")

# -----------------------
# UTILIZADORES
# -----------------------

def ver_utilizadores():
    cursor.execute("""
        SELECT username, pais
        FROM users
        WHERE perfil_publico=1
        ORDER BY username
    """)
    rows = cursor.fetchall()
    if not rows:
        print("Sem utilizadores públicos.")
        return
    for u in rows:
        print(f"{u[0]} | {u[1]}")

def pesquisar_user():
    nome = input("Pesquisar username: ").strip()
    cursor.execute("""
        SELECT username, pais
        FROM users
        WHERE username LIKE ?
        AND perfil_publico=1
        ORDER BY username
    """, ('%' + nome + '%',))
    rows = cursor.fetchall()
    if not rows:
        print("Sem resultados.")
        return
    for r in rows:
        print(f"{r[0]} | {r[1]}")

# -----------------------
# EDITAR PERFIL
# -----------------------

def editar_perfil(user):
    user_id = user[0]
    while True:
        print("\n=== EDITAR PERFIL ===")
        print("1 - Alterar nome")
        print("2 - Alterar telefone")
        print("3 - Alterar país")
        print("4 - Alterar password")
        print("5 - Público / Privado")
        print("6 - Alterar moeda base")
        print("0 - Voltar")

        op = input("Escolha: ").strip()

        if op == "1":
            novo = input("Novo nome: ").strip()
            cursor.execute("UPDATE users SET nome=? WHERE id=?", (novo, user_id))

        elif op == "2":
            novo = input("Novo telefone completo com prefixo: ").strip()
            cursor.execute("SELECT 1 FROM users WHERE telefone=? AND id<>?", (novo, user_id))
            if cursor.fetchone():
                print("Esse telefone já existe.")
                continue
            cursor.execute("UPDATE users SET telefone=? WHERE id=?", (novo, user_id))

        elif op == "3":
            novo = input("Novo país: ").strip()
            cursor.execute("UPDATE users SET pais=? WHERE id=?", (novo, user_id))

        elif op == "4":
            novo = input_password("Nova password: ")
            if len(novo) < 6:
                print("Password demasiado curta.")
                continue
            cursor.execute("UPDATE users SET password=? WHERE id=?", (novo, user_id))

        elif op == "5":
            novo = input("1 público / 0 privado: ").strip()
            if novo not in ("0", "1"):
                print("Valor inválido.")
                continue
            cursor.execute("UPDATE users SET perfil_publico=? WHERE id=?", (int(novo), user_id))

        elif op == "6":
            nova = input("Nova moeda base: ").strip().upper()
            if nova not in MOEDAS_DISPONIVEIS:
                print("Moeda inválida.")
                continue
            set_moeda_base(user_id, nova)

        elif op == "0":
            break

        else:
            print("Opção inválida.")
            continue

        conn.commit()
        print("Perfil atualizado.")

# -----------------------
# ASSETS
# -----------------------

def ver_assets():
    cursor.execute("""
        SELECT id, nome, simbolo, tipo, pais, moeda
        FROM assets
        ORDER BY pais, tipo, nome
    """)
    rows = cursor.fetchall()
    if not rows:
        print("Sem ativos.")
        return
    for a in rows:
        print(f"{a[0]} | {a[1]} | {a[2] or 'SEM_SÍMBOLO'} | {a[3]} | {a[4]} | {a[5]}")

def pesquisar_asset():
    nome = input("Nome do ativo: ").strip()
    cursor.execute("""
        SELECT id, nome, simbolo, tipo, pais, moeda
        FROM assets
        WHERE nome LIKE ?
        ORDER BY nome
    """, ('%' + nome + '%',))
    rows = cursor.fetchall()
    if not rows:
        print("Sem resultados.")
        return
    for a in rows:
        print(f"{a[0]} | {a[1]} | {a[2] or 'SEM_SÍMBOLO'} | {a[3]} | {a[4]} | {a[5]}")

def adicionar_asset():
    nome = input("Nome: ").strip()
    simbolo = input("Símbolo: ").strip().upper()
    tipo = input("Tipo: ").strip()
    pais = input("País: ").strip()
    moeda = input("Moeda: ").strip().upper()

    if moeda not in MOEDAS_DISPONIVEIS:
        print("Moeda inválida.")
        return

    cursor.execute("""
        INSERT INTO assets (nome, simbolo, tipo, pais, moeda)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, simbolo, tipo, pais, moeda))
    conn.commit()
    print("Ativo adicionado.")

def ver_catalogo_por_grupo():
    print("\n=== CATÁLOGO ===")
    for pais, grupos in CATALOGO.items():
        print(f"\n[{pais}]")
        for tipo, nomes in grupos.items():
            print(f"  - {tipo}: {len(nomes)} ativos")

# -----------------------
# SALDO / MOVIMENTOS
# -----------------------

def ver_saldo(user_id):
    moeda = moeda_base_user(user_id)
    print(f"Saldo atual: {format_money(saldo_atual(user_id), moeda)}")

def inserir_saldo(user_id):
    moeda = moeda_base_user(user_id)
    valor = valor_float(f"Valor a inserir em {moeda} (0 para voltar): ")
    if valor is None:
        return
    saldo = saldo_atual(user_id) + valor
    cursor.execute("UPDATE contas SET saldo=? WHERE user_id=?", (saldo, user_id))
    cursor.execute("""
        INSERT INTO movimentos (user_id, tipo, valor, moeda, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "entrada", valor, moeda, "Depósito manual", agora_iso()))
    conn.commit()
    print("Saldo atualizado com sucesso.")

def inserir_despesa(user_id):
    moeda = moeda_base_user(user_id)
    valor = valor_float(f"Valor da despesa em {moeda} (0 para voltar): ")
    if valor is None:
        return
    if valor > saldo_atual(user_id):
        print("Saldo insuficiente.")
        return
    desc = input("Descrição da despesa: ").strip()
    saldo = saldo_atual(user_id) - valor
    cursor.execute("UPDATE contas SET saldo=? WHERE user_id=?", (saldo, user_id))
    cursor.execute("""
        INSERT INTO movimentos (user_id, tipo, valor, moeda, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "despesa", valor, moeda, desc, agora_iso()))
    conn.commit()
    print("Despesa registada.")

def ver_movimentos(user_id):
    cursor.execute("""
        SELECT tipo, valor, moeda, descricao, criado_em
        FROM movimentos
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 30
    """, (user_id,))
    rows = cursor.fetchall()
    if not rows:
        print("Sem movimentos.")
        return
    for m in rows:
        print(f"{m[4]} | {m[0]} | {format_money(m[1], m[2])} | {m[3]}")

# -----------------------
# INVESTIMENTOS
# -----------------------

def comprar_ativo(user_id):
    pesquisar_asset()
    asset_id = input("ID do ativo para comprar (0 para voltar): ").strip()
    if asset_id == "0":
        return

    cursor.execute("SELECT id, nome, simbolo, moeda FROM assets WHERE id=?", (asset_id,))
    ativo = cursor.fetchone()
    if not ativo:
        print("Ativo não encontrado.")
        return

    qtd = valor_float("Quantidade (0 para voltar): ")
    if qtd is None or qtd <= 0:
        return

    manual = input("Preço manual? (s/n): ").strip().lower()

    if manual == "s":
        preco = valor_float("Preço de compra manual (0 para voltar): ")
        if preco is None:
            return
    else:
        preco = preco_tempo_real(ativo[2])
        if preco is None:
            print("Não foi possível buscar preço em tempo real. Introduz preço manual.")
            preco = valor_float("Preço de compra manual (0 para voltar): ")
            if preco is None:
                return

    data_compra = input("Data de compra (YYYY-MM-DD, Enter=hoje): ").strip()
    if not data_compra:
        data_compra = datetime.now().strftime("%Y-%m-%d")

    moeda_base = moeda_base_user(user_id)
    custo_total_ativo = qtd * preco

    if ativo[3] != moeda_base:
        custo_convertido = converter_moeda(custo_total_ativo, ativo[3], moeda_base)
        if custo_convertido is None:
            print("Falha na conversão de moeda.")
            return
    else:
        custo_convertido = custo_total_ativo

    if custo_convertido > saldo_atual(user_id):
        print("Saldo insuficiente para a compra.")
        return

    cursor.execute("""
        INSERT INTO portfolio (user_id, asset_id, quantidade, preco_compra, moeda_compra, data_compra)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, ativo[0], qtd, preco, ativo[3], data_compra))

    cursor.execute("UPDATE contas SET saldo=saldo-? WHERE user_id=?", (custo_convertido, user_id))

    cursor.execute("""
        INSERT INTO movimentos (user_id, tipo, valor, moeda, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, "investimento", custo_convertido, moeda_base,
        f"Compra de {ativo[1]} ({qtd})", agora_iso()
    ))

    conn.commit()
    print(f"Compra registada: {ativo[1]} x{qtd} por {preco:.4f} {ativo[3]}.")
    print(f"Custo debitado: {format_money(custo_convertido, moeda_base)}")

def ver_portfolio(user_id):
    moeda_base = moeda_base_user(user_id)
    cursor.execute("""
        SELECT p.id, a.nome, a.simbolo, a.moeda, p.quantidade, p.preco_compra, p.data_compra, p.moeda_compra
        FROM portfolio p
        JOIN assets a ON a.id = p.asset_id
        WHERE p.user_id=?
        ORDER BY p.id DESC
    """, (user_id,))
    rows = cursor.fetchall()

    if not rows:
        print("Portfólio vazio.")
        return

    total_base = 0.0

    print("\n=== PORTFÓLIO ===")
    for p in rows:
        pos_id, nome, simbolo, moeda_ativo, qtd, preco_compra, data_compra, moeda_compra = p
        preco_atual = preco_tempo_real(simbolo)
        if preco_atual is None:
            print(f"{pos_id} | {nome} | {qtd} | sem preço atual")
            continue

        valor_atual_ativo = qtd * preco_atual
        valor_base = converter_moeda(valor_atual_ativo, moeda_ativo, moeda_base) if moeda_ativo != moeda_base else valor_atual_ativo
        if valor_base is None:
            print(f"{pos_id} | {nome} | falha na conversão")
            continue

        total_base += valor_base
        print(
            f"{pos_id} | {nome} ({simbolo or 'SEM'}) | Qtd: {qtd} | Compra: {preco_compra:.4f} {moeda_compra} | "
            f"Atual: {preco_atual:.4f} {moeda_ativo} | Valor atual: {format_money(valor_base, moeda_base)} | "
            f"Data: {data_compra}"
        )

    print(f"\nValor total do portfólio: {format_money(total_base, moeda_base)}")

def ver_lucro_prejuizo(user_id):
    moeda_base = moeda_base_user(user_id)
    cursor.execute("""
        SELECT p.id, a.nome, a.simbolo, a.moeda, p.quantidade, p.preco_compra, p.moeda_compra
        FROM portfolio p
        JOIN assets a ON a.id = p.asset_id
        WHERE p.user_id=?
        ORDER BY p.id DESC
    """, (user_id,))
    posicoes = cursor.fetchall()

    if not posicoes:
        print("Não tens posições no portfólio.")
        return

    total_investido = 0.0
    total_atual = 0.0

    print("\n=== LUCRO / PREJUÍZO ===")
    for p in posicoes:
        pos_id, nome, simbolo, moeda_ativo, quantidade, preco_compra, moeda_compra = p
        preco_atual = preco_tempo_real(simbolo)

        if preco_atual is None:
            print(f"{pos_id} | {nome} ({simbolo or 'SEM'}) - sem preço em tempo real")
            continue

        investido = quantidade * preco_compra
        atual = quantidade * preco_atual

        investido_base = converter_moeda(investido, moeda_compra, moeda_base) if moeda_compra != moeda_base else investido
        atual_base = converter_moeda(atual, moeda_ativo, moeda_base) if moeda_ativo != moeda_base else atual

        if investido_base is None or atual_base is None:
            print(f"{pos_id} | {nome} - sem conversão")
            continue

        pl = atual_base - investido_base
        perc = (pl / investido_base * 100) if investido_base else 0

        total_investido += investido_base
        total_atual += atual_base

        print(
            f"{pos_id} | {nome} | Investido: {format_money(investido_base, moeda_base)} | "
            f"Atual: {format_money(atual_base, moeda_base)} | "
            f"P/L: {format_money(pl, moeda_base)} ({perc:.2f}%)"
        )

    pl_total = total_atual - total_investido
    perc_total = (pl_total / total_investido * 100) if total_investido else 0
    print("\n=== TOTAL ===")
    print(f"Investido total: {format_money(total_investido, moeda_base)}")
    print(f"Valor atual total: {format_money(total_atual, moeda_base)}")
    print(f"P/L total: {format_money(pl_total, moeda_base)} ({perc_total:.2f}%)")

# -----------------------
# CONVERSÃO
# -----------------------

def ver_moedas_disponiveis():
    print("Moedas disponíveis:")
    print(", ".join(MOEDAS_DISPONIVEIS))

def converter_interativo():
    print("\n=== CONVERSOR DE MOEDA ===")
    origem = input("Moeda origem: ").strip().upper()
    destino = input("Moeda destino: ").strip().upper()
    valor = valor_float("Valor (0 para voltar): ")
    if valor is None:
        return
    if origem not in MOEDAS_DISPONIVEIS or destino not in MOEDAS_DISPONIVEIS:
        print("Moeda inválida.")
        return
    convertido = converter_moeda(valor, origem, destino)
    if convertido is None:
        print("Falha na conversão.")
        return
    print(f"{format_money(valor, origem)} = {format_money(convertido, destino)}")

# -----------------------
# RESUMO / RANKING
# -----------------------

def resumo_financeiro(user_id):
    moeda_base = moeda_base_user(user_id)
    saldo = saldo_atual(user_id)

    cursor.execute("""
        SELECT a.nome, a.simbolo, p.quantidade, a.moeda
        FROM portfolio p
        JOIN assets a ON a.id = p.asset_id
        WHERE p.user_id=?
        ORDER BY a.nome
    """, (user_id,))
    rows = cursor.fetchall()

    total_portfolio = 0.0
    linhas = []

    for nome, simbolo, qtd, moeda_ativo in rows:
        preco = preco_tempo_real(simbolo)
        if preco is None:
            valor_base = None
        else:
            valor_ativo = qtd * preco
            valor_base = converter_moeda(valor_ativo, moeda_ativo, moeda_base) if moeda_ativo != moeda_base else valor_ativo
            if valor_base is not None:
                total_portfolio += valor_base

        linhas.append((nome, qtd, simbolo, valor_base))

    patrimonio = saldo + total_portfolio

    print("\n=== RESUMO FINANCEIRO ===")
    print(f"Tens {format_money(saldo, moeda_base)} em saldo.")
    print(f"Valor estimado do portfólio: {format_money(total_portfolio, moeda_base)}")
    print(f"Património total: {format_money(patrimonio, moeda_base)}")

    if not linhas:
        print("Não tens ativos comprados.")
        return

    print("\nAtivos detidos:")
    for nome, qtd, simbolo, valor_base in linhas:
        texto = f"- {qtd} de {nome}"
        if valor_base is not None:
            texto += f" | valor atual aprox.: {format_money(valor_base, moeda_base)}"
        if simbolo:
            texto += f" | símbolo: {simbolo}"
        print(texto)

def ranking_utilizadores():
    print("\n=== RANKING ===")
    cursor.execute("""
        SELECT id, username, perfil_publico
        FROM users
        ORDER BY username
    """)
    users = cursor.fetchall()

    ranking = []
    for user_id, username, publico in users:
        moeda_base = moeda_base_user(user_id)
        saldo = saldo_atual(user_id)
        total_portfolio = 0.0

        cursor.execute("""
            SELECT a.simbolo, a.moeda, p.quantidade
            FROM portfolio p
            JOIN assets a ON a.id = p.asset_id
            WHERE p.user_id=?
        """, (user_id,))
        ativos = cursor.fetchall()

        for simbolo, moeda_ativo, qtd in ativos:
            preco = preco_tempo_real(simbolo)
            if preco is None:
                continue
            valor = qtd * preco
            valor_base = converter_moeda(valor, moeda_ativo, moeda_base) if moeda_ativo != moeda_base else valor
            if valor_base is not None:
                total_portfolio += valor_base

        total = saldo + total_portfolio
        nome_visivel = username if publico == 1 else f"{username} (privado)"
        ranking.append((nome_visivel, total, moeda_base))

    ranking.sort(key=lambda x: x[1], reverse=True)

    for i, item in enumerate(ranking, start=1):
        print(f"{i}. {item[0]} | {format_money(item[1], item[2])}")

# -----------------------
# MENU
# -----------------------

def menu_user(user):
    user_id = user[0]
    garantir_conta(user_id)

    while True:
        print("\n=== MENU ===")
        print("1 - Ver utilizadores públicos")
        print("2 - Pesquisar utilizador")
        print("3 - Editar perfil")
        print("4 - Ver catálogo resumido")
        print("5 - Ver todos os ativos")
        print("6 - Pesquisar ativos")
        print("7 - Adicionar ativo")
        print("8 - Ver saldo")
        print("9 - Inserir saldo")
        print("10 - Inserir despesa")
        print("11 - Ver movimentos")
        print("12 - Comprar ativo")
        print("13 - Ver portfólio")
        print("14 - Ver lucro/prejuízo")
        print("15 - Ver moedas disponíveis")
        print("16 - Converter moeda")
        print("17 - Resumo financeiro")
        print("18 - Ranking de utilizadores")
        print("0 - Logout")

        op = input("Escolha: ").strip()

        if op == "1":
            ver_utilizadores()
        elif op == "2":
            pesquisar_user()
        elif op == "3":
            editar_perfil(user)
        elif op == "4":
            ver_catalogo_por_grupo()
        elif op == "5":
            ver_assets()
        elif op == "6":
            pesquisar_asset()
        elif op == "7":
            adicionar_asset()
        elif op == "8":
            ver_saldo(user_id)
        elif op == "9":
            inserir_saldo(user_id)
        elif op == "10":
            inserir_despesa(user_id)
        elif op == "11":
            ver_movimentos(user_id)
        elif op == "12":
            comprar_ativo(user_id)
        elif op == "13":
            ver_portfolio(user_id)
        elif op == "14":
            ver_lucro_prejuizo(user_id)
        elif op == "15":
            ver_moedas_disponiveis()
        elif op == "16":
            converter_interativo()
        elif op == "17":
            resumo_financeiro(user_id)
        elif op == "18":
            ranking_utilizadores()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

# -----------------------
# APP
# -----------------------

def main():
    semear_assets_iniciais()

    while True:
        print("\n=== APP INVEST ===")
        print("1 - Login")
        print("2 - Criar conta")
        print("0 - Sair")

        op = input("Escolha: ").strip()

        if op == "1":
            login()
        elif op == "2":
            registar()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

    conn.close()

if __name__ == "__main__":
    main()
