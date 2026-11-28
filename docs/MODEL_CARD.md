# Model Card — Modelo de Inadimplência e Recuperabilidade (Sefin Palmas)

> Formato: Mitchell et al. (2019). Projeto Integrador — BIINAR/UFT Palmas (Eixo II, 2026/2).

## 1. Detalhes do modelo
- **Nome:** Modelo de Inadimplência (dívida ativa) + scoring de recuperabilidade (faixas alta/média/baixa).
- **Versão / data:** v1.0 — 25/11/2026.
- **Tipo:** dois classificadores de **regressão logística** (`scikit-learn 1.6.1`, `SEMENTE = 42`, treino em 15–16/11/2026):
  - **Modelo 1:** prevê `inadimplente_proximo_exercicio` (uso diagnóstico, limiar operacional `0,35`). Comparação na validação temporal (`TimeSeriesSplit`, 4 dobras, ROC-AUC médio ± DP): Regressão Logística (**0,7119 ± 0,0116**, vencedora), Random Forest tunado (`0,7068 ± 0,0132`), Árvore de Decisão (`0,6884 ± 0,0165`) e Classificador Trivial (`0,5000 ± 0,0000`).
  - **Modelo 2:** prevê `divida_recuperada_12m` entre contribuintes com `valor_divida_consolidada > 0` e ordena a fila em faixas alta (`> 0,66`), média (`0,33–0,66`) e baixa (`< 0,33`). Comparação na validação temporal: Regressão Logística (**0,6717 ± 0,0113**, vencedora), Random Forest (`0,6601 ± 0,0130`) e Árvore de Decisão (`0,6404 ± 0,0264`).
- **Artefatos:** `models/modelo_inadimplencia.joblib`, `models/modelo_recuperabilidade.joblib`, `models/metadados_modelos.json`; painel de demonstração (Streamlit): https://paineltributariosintetico.streamlit.app (código em `app/painel_app.py`).
- **Desenvolvido por:** equipe 5 do BIINAR/UFT Palmas — Davi Pereira, Laura Nicolle, Márcio Araújo, Matheus Felipe, Marcus Vinicius. Orientação: Prof. Dr. David Nadler Prata.
- **Licença / status:** projeto acadêmico, **não** é sistema em produção da Prefeitura.

## 2. Uso pretendido
- **Uso principal:** apoiar a Sefin a **priorizar a ordem** de ações de cobrança da dívida ativa (ISS/IPTU), concentrando esforço onde a recuperação é mais provável.
- **Usuários:** auditores e analistas da Sefin, sempre com revisão humana.
- **Fora do escopo / usos proibidos:**
  1. Decidir sozinho (sem revisão humana) protesto, penhora, negativação ou qualquer sanção.
  2. Incluir beneficiários do IPTU Social (idosos, aposentados, pensionistas, PcD de baixa renda) em ações preditivas de cobrança.
  3. Usar o score para negar serviços públicos, benefícios ou crédito.
  4. Usar o modelo em outro município/tributo sem nova validação.
  5. Reidentificar pessoas ou cruzar com bases externas sem base legal.

## 3. Fatores relevantes
- **Grupos/fatores avaliados:** faixa de renda do setor (`baixa`, `media`, `alta`) e setor urbano (`setor_urbano`).
- **Atributos sensíveis:** o modelo **não** usa idade, deficiência, raça ou gênero. Setor e renda podem funcionar como *proxy* de vulnerabilidade — por isso são auditados. Atributos de entrada (12): `tipo_imovel`, `setor_urbano`, `area_construida_m2`, `valor_venal`, `valor_iptu_anual`, `distancia_centro_km`, `exercicios_inadimplentes_5a`, `tempo_inadimplencia_dias`, `valor_divida_consolidada`, `qtd_parcelamentos_anteriores`, `parcelamento_rompido`, `qtd_notificacoes`. `iptu_social` e `faixa_renda_setor` **não** são atributos de entrada; mas `setor_urbano` e `distancia_centro_km` podem carregar informação de renda do território (*proxy*), motivando a auditoria por faixa de renda.
- **Ambiente:** dados tabulares de carteira de contribuintes; desempenho pode variar com mudança de legislação, crise econômica ou campanhas de regularização.

## 4. Métricas de avaliação
- **Globais (conjunto de teste, `metadados_modelos.json`):**

| | ROC-AUC | Acurácia | Precisão | Recall | F1 |
|---|---|---|---|---|---|
| Modelo 1 — inadimplência (limiar 0,35) | 0,7069 | 0,6113 | 0,5758 | 0,8658 | 0,6916 |
| Modelo 2 — recuperabilidade | 0,6842 | 0,6367 | 0,6423 | 0,7154 | 0,6769 |

  O Modelo 1 usa limiar baixo (`0,35`): privilegia recall (`0,87`) à custa de precisão (`0,58`), sinalizando um volume amplo de contribuintes para fins estritamente preventivos/diagnósticos. Desempenho moderado é esperado em dados sintéticos com ruído (AUC-PR não utilizada como critério principal devido ao equilíbrio natural das classes na carteira: ~51% positivas).
- **Por subgrupo (renda e setor):** taxa de seleção (paridade demográfica) e TPR (igualdade de oportunidade), detalhadas em `docs/fairness_resultados.md`. Resumo por faixa de renda do setor (baixa / média / alta): **Modelo 1** — seleção 89,8% / 78,7% / 45,6% (razão `0,51`) e TPR 94,8% / 89,2% / 60,6%; **Modelo 2** (faixa alta) — seleção 13,5% / 18,4% / 26,0% (razão `0,52`) e TPR 18,8% / 25,1% / 33,7%. Por setor, a razão é `0,50` (Modelo 1) e `0,23` (Modelo 2).
- **Por que essas métricas:** o custo de errar não é simétrico — falso positivo onera quem não devia ser abordado; falso negativo deixa de arrecadar recursos públicos.

## 5. Dados
- **Treino/validação/teste:** após a exclusão prévia dos 1.393 beneficiários do IPTU Social (restam 18.607 elegíveis), foi criado um eixo temporal sintético de competência mensal (`jan/2024` a `out/2026`, sorteado de forma independente dos atributos com `SEMENTE = 42`, pois a carteira original não possui coluna de data). Aplicou-se corte temporal em `01/04/2026`: **treino** de `jan/2024` a `mar/2026` (14.877 registros, 80%; 12.289 com dívida para o Modelo 2) e **teste** de `abr/2026` a `out/2026` (3.730 registros, 20%; 3.072 com dívida para o Modelo 2), com validação interna via `TimeSeriesSplit(n_splits=4)`.
- **Origem:** `carteira_contribuintes.csv` (20.000 linhas, 17 colunas, 1.393 do IPTU Social) do repositório de referência da disciplina. **A carteira é sintética** (calibrada por agregados oficiais da Sefin, sem dado pessoal): conclusões de fairness descrevem o comportamento do modelo nesses dados, **não** a realidade dos contribuintes de Palmas.
- **Pré-processamento:** encapsulado em `Pipeline` (`ColumnTransformer`) ajustado exclusivamente no treino: variáveis categóricas (`tipo_imovel`, `setor_urbano`) codificadas via `OneHotEncoder(handle_unknown="ignore")` e numéricas imputadas pela mediana (`SimpleImputer(strategy="median")`) e padronizadas com média zero e variância unitária (`StandardScaler()`), gerando 22 colunas transformadas.
- **Taxas observadas na carteira (20.000 registros):** `inadimplente_proximo_exercicio` = 51,2% no total; 59,6% em setores de renda baixa, 47,4% média e 37,8% alta; por setor, de 37,2% (Setor Comercial Central) a 62,8% (Taquari). Beneficiários do IPTU Social: 6,97% da carteira, com taxa de 57,2% contra 50,7% nos demais.
- **Sub-representações:** setores pequenos — Área de Expansão (1.001 registros), Setor Comercial Central (1.187), Jardim Aureny IV (1.380) e Taquari (1.596) — contra Plano Diretor Sul (4.460); faixa de renda alta tem 3.955 registros contra 9.204 da baixa; terrenos (1.409) e imóveis industriais (590) são poucos. Métricas desses subgrupos são mais instáveis. Os 1.393 do IPTU Social foram removidos da população-alvo do modelo.

## 6. Análise de viés
- **Testes:** paridade demográfica (razão ≥ 0,8 como referência da regra dos 80%) e igualdade de oportunidade, por faixa de renda e setor.
- **Achados:** nenhum dos modelos atinge a razão de 0,80 por renda ou por setor. O Modelo 1 sinaliza 90% dos contribuintes de setores de renda baixa contra 46% nos de renda alta (em parte por diferença real de inadimplência: 59,8% contra 37,8%), mas também deixa escapar mais inadimplentes de setores ricos (TPR 61% contra 95%). No Modelo 2, as taxas reais de recuperação são parecidas entre as faixas (50% a 55%), porém dívidas de setores de baixa renda caem menos na faixa de prioridade alta (13,5% contra 26,0%): o modelo parece subestimar a recuperabilidade desses setores. A explicação mostra que o setor pesa pouco e que o fator dominante é `tempo_inadimplencia_dias`; a hipótese é que as variáveis de comportamento da dívida se distribuam de forma diferente entre as faixas de renda. Detalhes e limites em `docs/RIA.md`, seção 2.
- **Mitigações:** exclusão formal do IPTU Social (sem ela, 1.250 dos 1.393 beneficiários entrariam na fila); uso do Modelo 1 apenas como diagnóstico; experimento de corte por faixa de renda no Modelo 2 (`src/sprint5_mitigacao.py`): razão de paridade demográfica `0,52 → 1,00` (por construção) e diferença máxima de TPR `0,149 → 0,002`, com precisão `0,703 → 0,709` e recall `0,239 → 0,241`, ou seja, sem perda de eficiência; testado nos mesmos dados e em carteira sintética, e o corte por território exigiria análise jurídica antes de uso real (ver `docs/RIA.md`); comparar a distribuição de `tempo_inadimplencia_dias` e das variáveis de parcelamento por faixa de renda e avaliar retreino sem proxies (`src/sprint5_retreino_sem_proxies.py`).
- **Limitações do que foi feito:** métricas de grupo não garantem justiça individual; dois critérios de fairness não podem ser maximizados juntos quando as taxas-base diferem.

## 7. Considerações éticas e riscos
- Cobrança mal direcionada pode recair sobre pessoas vulneráveis; mitigado por exclusão do IPTU Social e revisão humana.
- Risco de *feedback loop*: quem é mais cobrado gera mais dados de cobrança. Recomenda-se reavaliar periodicamente.
- Tratamento regido pela LGPD (ver `docs/RIA.md`).

## 8. Recomendações
- Revisão humana obrigatória; registrar a decisão humana e o motivo.
- Reavaliar fairness a cada novo ciclo de dados (sugestão: semestral) e antes de qualquer uso real.
- Validar com dados reais anonimizados e com o encarregado (DPO) da Prefeitura antes de adoção.

## 9. Contato e contestação
- Contribuinte que discordar de uma priorização pode pedir **revisão por pessoa natural** (Art. 20 LGPD) e explicação dos critérios.
- **Canal de atendimento e contestação:** Ouvidoria Geral do Município de Palmas / Atendimento Presencial Resolve Palmas e canal de suporte do projeto acadêmico (repositório oficial `github.com/pereiradavi-creator/projeto-git-uft` — Equipe 5 BIINAR/UFT).
- **Prazo-alvo de resposta:** até 15 dias corridos para fornecimento de explicação clara dos critérios e revisão administrativa por servidor humano (em alinhamento ao Art. 19, II e Art. 20 da LGPD).
