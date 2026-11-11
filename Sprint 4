UNIVERSIDADE FEDERAL DO TOCANTINS
Bacharelado Interdisciplinar em Inteligência Artificial — BIINAR
Eixo II — Projeto Integrador: Inteligência Tributária (Sefin Palmas) | 2026/2
TAREFA DO PROJETO INTEGRADOR
SPRINT 4 — MODELO DE IA E MVP
Predição de inadimplência, scoring de recuperabilidade e painel
Período: 29/10 a 11/11/2026  |  Entrega: Quarta-feira, 11/11/2026, até as 23h59 (encerramento do Módulo 6)
Coordenação: Prof. Dr. David Nadler Prata  |  Apoio: docentes dos módulos âncora do Eixo II
  1. Identificação  

Projeto	Sistema de Inteligência Tributária — priorização da cobrança da dívida ativa de Palmas-TO (Opção D)
Sprint	SPRINT 4 — MODELO DE IA E MVP (29/10 a 11/11/2026)
Módulo(s) âncora	Módulo 6 — Introdução à Inteligência Artificial
Entrega	Quarta-feira, 11/11/2026, até as 23h59 (encerramento do Módulo 6)
Modalidade	Em equipe — 5 integrantes (equipes formalizadas na Sprint 0)
Como entregar	Repositório Git da equipe (branch da sprint mesclada) + modelo serializado em /models; link enviado à coordenação
Peso	O Projeto Integrador corresponde a 30% da nota final do Eixo II

  2. Objetivo da sprint  

Transformar dados preparados em inteligência: treinar e avaliar o modelo de predição de inadimplência e o scoring de recuperabilidade da dívida ativa, e expor os resultados num MVP interativo que um analista da Sefin consiga usar.

  3. Entregáveis  

E1 — Metodologia de treino. Divisão treino/teste/validação com split temporal sem vazamento de dados, documentada no notebook, e modelos baseline (Regressão Logística, Árvore de Decisão) treinados como referência.
E2 — Modelos finais avaliados. Modelo de classificação de inadimplência (ex.: Random Forest/XGBoost) com tunagem de hiperparâmetros e métricas completas — acurácia, precisão, recall, F1 e matriz de confusão — mais o modelo complementar de scoring de recuperabilidade (faixas alta/média/baixa), com justificativa das escolhas algorítmicas.
E3 — Notebook documentado + modelo serializado. Notebook Jupyter com a trilha completa (EDA → pré-processamento → treinamento → avaliação) e o modelo salvo (.pkl/.joblib) versionado em /models.
E4 — MVP com interface. Painel Streamlit (ou equivalente) funcional: ranking de devedores por score de recuperabilidade, mapa de calor de inadimplência por setor e projeção de arrecadação potencial — demonstrável ao vivo.

  4. Marcos semanais (cronograma do PI)  

Semana	Marco
02/11 a 06/11	Split temporal definido + baselines treinados e registrados no notebook
09/11 a 11/11	ENTREGA Sprint 4: modelo avaliado com métricas documentadas + MVP com ranking de risco

  5. Critérios de avaliação (rubrica)  

Critério	O que será observado	Peso
Metodologia (E1)	Split temporal correto, sem vazamento; baselines como referência	25%
Modelos e métricas (E2)	Escolhas justificadas; métricas completas e interpretadas	30%
Notebook e artefatos (E3)	Trilha reprodutível; modelo serializado e versionado	15%
MVP (E4)	Painel funcional e demonstrável, conectado ao pipeline real	30%

  6. Orientações e combinados  

•	A entrega é por equipe (5 integrantes); a participação individual é conferida pelo histórico de commits, pelos pull requests e pelo diário de bordo.
•	Atenção ao vazamento temporal: nada do futuro pode informar o passado no treino — a banca vai perguntar.
•	Guardem as métricas POR SUBGRUPO (faixa de renda, região): a Sprint 5 fará a análise de fairness sobre elas.
•	Se a camada individual do dado for sintética, declarem isso já no notebook: a acurácia obtida demonstra que o pipeline funciona, não que o modelo funciona no mundo real.
•	Ética na coleta e no tratamento, sempre: fontes oficiais, robots.txt respeitado, delays nas requisições, nenhum dado pessoal além do necessário e anonimização antes do armazenamento (LGPD).
•	Atrasos: entregas após o prazo recebem desconto de 20% por dia útil, salvo justificativa acordada previamente com a coordenação.

Por que esta sprint importa
É aqui que o Eixo II inteiro se encontra: matemática, engenharia, dados e IA num produto só.
Mas um modelo sem as métricas honestas da Sprint 5 é só metade da entrega — sigam com o RIA em mente.

