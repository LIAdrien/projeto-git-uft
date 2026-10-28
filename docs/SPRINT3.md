# Relatório da Sprint 3 — Pipeline ETL e Análise Exploratória

## 1. Instruções de Execução (Reprodutibilidade)
1. Instale as dependências: `pip install -r requirements.txt`
2. Execute o pipeline: `python src/etl_sefin.py`
3. Os dados brutos extraídos serão armazenados em `data/bruto/`.
4. O arquivo enriquecido final será persistido em `data/pronto/divida_ativa_enriquecida.csv`.
5. Os gráficos e mapas serão exportados para `docs/painel_eda_sefin.png`.

## 2. Divisão de Trabalho entre os 5 Integrantes
- **Integrante 1:** Desenvolvimento do script de consumo da API (E1), paginação e tratamento de rate-limiting.
- **Davi Pereira Borges:** Construção da limpeza de dados, anonimização LGPD e regras do IPTU Social.
- **Integrante 3:** Enriquecimento socioeconômico com dados do IBGE e engenharia de atributos (Faixas, Sazonalidade, Score).
- **Integrante 4:** Elaboração do painel de EDA, geração dos gráficos e mapa geoespacial por setor urbano (E3).
- **Integrante 5:** Estruturação dos logs de execução, validação da reprodutibilidade e escrita da documentação/README (E4).
