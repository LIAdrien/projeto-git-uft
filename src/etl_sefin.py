import os
import sys
import time
import json
import random
import logging
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# CONFIGURAÇÃO DE LOGS E DIRETÓRIOS (E1 / E4)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ETL_Sefin_Palmas")

# Estrutura de Pastas Exigida (data/bruto, data/limpo, data/pronto, docs)
for pasta in ['data/bruto', 'data/limpo', 'data/pronto', 'docs']:
    os.makedirs(pasta, exist_ok=True)

logger.info("Diretórios de trabalho e logging inicializados com sucesso.")

# ==========================================
# ENTREGÁVEL E1: COLETA AUTOMATIZADA E SIMULAÇÃO DE API REST
# ==========================================
class ColetorAPISefin:
    """
    Simula e consome a API REST da Prefeitura de Palmas (Sefin) e IBGE.
    Trata autenticação (JWT), Paginação e Rate-Limiting.
    """
    def __init__(self, base_url="https://api.palmas.to.gov.br/v1/arrecadacao", rate_limit_delay=0.2):
        self.base_url = base_url
        self.delay = rate_limit_delay
        self.headers = {"Authorization": "Bearer TOKEN_JWT_MOCK_SEFIN_2026"}

    def buscar_debitos_paginados(self, total_registros=1200, limite_por_pagina=200):
        logger.info(f"Iniciando coleta via API com limite de {limite_por_pagina} reg/pág...")
        todos_dados = []
        paginas = (total_registros // limite_por_pagina) + (1 if total_registros % limite_por_pagina != 0 else 0)

        # Setores Urbanos Fictícios de Palmas-TO para geolocalização e IBGE
        setores_palmas = ['Plano Diretor Sul', 'Plano Diretor Norte', 'Taquaralto', 'Aureny III', 'Aureny I', 'Buritirana']

        for pag in range(1, paginas + 1):
            time.sleep(self.delay)  # Respeita o Rate-Limiting da API / robots.txt
            logger.info(f"Consumindo Endpoint: {self.base_url}/divida-ativa?page={pag}&limit={limite_por_pagina} [HTTP 200 OK]")
            
            # Simulação do payload retornado pela API oficial
            for i in range(limite_por_pagina if pag < paginas else total_registros - len(todos_dados)):
                idx = len(todos_dados) + 1
                dt_vencimento = datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1800))
                eh_imovel = random.random() < 0.7
                isento = eh_imovel and (random.random() < 0.20) # IPTU Social ~20%
                
                registro = {
                    "id_transacao": f"TRX-{idx:06d}",
                    "cpf_cnpj": f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99):02d}",
                    "contribuinte": f"Contribuinte Palma_{idx}",
                    "inscricao_municipal": f"INS-TO-{idx:05d}",
                    "tipo_registro": "IMOVEL" if eh_imovel else "EMPRESA",
                    "setor_urbano": random.choice(setores_palmas),
                    "valor_original": round(random.uniform(300, 45000), 2),
                    "data_vencimento": dt_vencimento.strftime("%Y-%m-%d"),
                    "isento_iptu_social": 1 if isento else 0,
                    "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                todos_dados.append(registro)

        # Preserva e data os dados brutos em data/bruto/
        data_hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_bruto = f"data/bruto/divida_ativa_bruto_{data_hoje}.json"
        with open(caminho_bruto, "w", encoding="utf-8") as f:
            json.dump(todos_dados, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[E1 OK] Dados brutos preservados com sucesso em '{caminho_bruto}'. Total: {len(todos_dados)} registros.")
        return caminho_bruto
