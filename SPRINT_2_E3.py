import sqlite3
import random
import os

# ----------------------------------------------------------------------
# 1. BANCO DE DADOS (banco.py) - CRIAÇÃO E SCHEMA RELACIONAL
# ----------------------------------------------------------------------
DB_NAME = "tributos_piloto.db"

def inicializar_banco():
    """Cria as tabelas do banco de dados relacional para a SEFIN Palmas."""
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)  # Reinicia o banco para garantia de testes limpos
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela Contribuinte
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contribuinte (
            id_cidadao TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            idade INTEGER NOT NULL,
            categoria_social TEXT CHECK(categoria_social IN ('NENHUMA', 'IDOSO', 'APOSENTADO', 'PENSIONISTA', 'PCD')),
            renda_salarios_minimos REAL NOT NULL,
            qtd_imoveis INTEGER DEFAULT 1
        )
    ''')
    
    # Tabela Dívida Ativa / Registros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS divida_ativa (
            id_registro TEXT PRIMARY KEY,
            id_cidadao TEXT NOT NULL,
            tipo_registro TEXT CHECK(tipo_registro IN ('IMOVEL', 'EMPRESA')),
            valor_imposto REAL NOT NULL,
            ufip_valor REAL NOT NULL,
            anos_atraso INTEGER NOT NULL,
            ajuizada INTEGER CHECK(ajuizada IN (0, 1)),
            isento_iptu_social INTEGER CHECK(isento_iptu_social IN (0, 1)),
            FOREIGN KEY(id_cidadao) REFERENCES contribuinte(id_cidadao)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"-> Banco de dados '{DB_NAME}' inicializado com sucesso!")

# ----------------------------------------------------------------------
# 2. REGRAS DE NEGÓCIO - IPTU SOCIAL (Art. 20 CTM Palmas)
# ----------------------------------------------------------------------
VALOR_UFIP = 4.50  # Valor simulado de 1 UFIP em BRL

def verificar_isencao_iptu_social(idade, categoria, renda, ufip_calculado, qtd_imoveis):
    """
    Regra de Isenção do IPTU Social de Palmas:
    - Isenção Automática: IPTU < 50 UFIPs e imóvel único.
    - Isenção Condicional Social: IPTU < 150 UFIPs, imóvel único, renda <= 2 SM 
      e pertencer a grupo vulnerável (Idoso > 65, Aposentado, Pensionista, PCD).
    """
    if qtd_imoveis > 1:
        return 0  # Não elegível se possuir mais de um imóvel

    # Regra 1: Automática (< 50 UFIP)
    if ufip_calculado < 50:
        return 1

    # Regra 2: Social (< 150 UFIP + Vulnerabilidade)
    if ufip_calculado < 150 and renda <= 2.0:
        if idade >= 65 or categoria in ['APOSENTADO', 'PENSIONISTA', 'PCD']:
            return 1

    return 0

# ----------------------------------------------------------------------
# 3. CARGA DE DADOS SIMULADOS (INGESTÃO)
# ----------------------------------------------------------------------
def popular_banco_dados(num_cidadaos=1000):
    """Gera dados simulados e persiste no banco SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    categorias = ['NENHUMA', 'NENHUMA', 'NENHUMA', 'IDOSO', 'APOSENTADO', 'PENSIONISTA', 'PCD']
    
    total_registros = 0
    total_isentos = 0
    
    for i in range(1, num_cidadaos + 1):
        id_cidadao = f"CPF_{i:07d}"
        nome = f"Contribuinte {i}"
        idade = random.randint(18, 85)
        categoria = random.choice(categorias)
        renda = round(random.uniform(0.8, 8.0), 2)
        
        # Simula probabilidade de múltiplos imóveis (10% a 25%)
        qtd_imoveis = 1 if random.random() > 0.15 else random.randint(2, 3)
        
        cursor.execute('''
            INSERT INTO contribuinte VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_cidadao, nome, idade, categoria, renda, qtd_imoveis))
        
        # Gerar registros de dívida/imóvel para o cidadão
        for r in range(qtd_imoveis):
            total_registros += 1
            id_registro = f"REG_{total_registros:07d}"
            tipo = "IMOVEL" if random.random() > 0.3 else "EMPRESA"
            
            # Valor do IPTU/Taxa em UFIPs (Distribuição log-normal)
            ufip_calc = round(random.lognormvariate(4.2, 0.8), 2)
            valor_brl = round(ufip_calc * VALOR_UFIP, 2)
            anos_atraso = random.randint(1, 8)
            ajuizada = 1 if anos_atraso >= 4 else 0
            
            # Aplica regra de isenção se for imóvel
            if tipo == "IMOVEL":
                isento = verificar_isencao_iptu_social(idade, categoria, renda, ufip_calc, qtd_imoveis)
            else:
                isento = 0
                
            if isento == 1:
                total_isentos += 1
                
            cursor.execute('''
                INSERT INTO divida_ativa VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_registro, id_cidadao, tipo, valor_brl, ufip_calc, anos_atraso, ajuizada, isento))

    conn.commit()
    conn.close()
    
    print(f"-> Ingestão concluída com sucesso!")
    print(f"   - Contribuintes cadastrados: {num_cidadaos}")
    print(f"   - Total de registros (dívidas/imóveis): {total_registros}")
    print(f"   - Total de imóveis isentos (IPTU Social): {total_isentos} ({((total_isentos/total_registros)*100):.1f}%)")

# ----------------------------------------------------------------------
# 4. CONSULTA E VALIDAÇÃO DA ENTREGA 3
# ----------------------------------------------------------------------
def consultar_resumo():
    """Executa consultas de verificação no banco SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("\n=== RESUMO EXECUTIVO (SQLite - tributos_piloto.db) ===")
    
    cursor.execute("SELECT COUNT(*) FROM contribuinte")
    print(f"Total de Contribuintes: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*), SUM(valor_imposto) FROM divida_ativa WHERE isento_iptu_social = 0")
    qtd_cobravel, total_divida = cursor.fetchone()
    print(f"Registros Elegíveis para Cobrança: {qtd_cobravel}")
    print(f"Montante Total em Dívida Ativa Cobrável: R$ {total_divida:,.2f}")
    
    conn.close()

if __name__ == "__main__":
    inicializar_banco()
    popular_banco_dados(num_cidadaos=1000)
    consultar_resumo()
