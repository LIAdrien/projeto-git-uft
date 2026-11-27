# Model Card — Modelo de Inadimplência e Recuperabilidade (Sefin Palmas)

> Formato: Mitchell et al. (2019). Campos **⟦PREENCHER⟧** dependem dos números da sua Sprint 4 / do script `src/sprint5_fairness.py`. Não invente valores: cole o que o notebook produziu.

## 1. Detalhes do modelo
- **Nome:** Modelo de Inadimplência (dívida ativa) + scoring de recuperabilidade (faixas alta/média/baixa).
- **Versão / data:** v1.0 — 25/11/2026.
- **Tipo:** dois classificadores de **regressão logística** (scikit-learn 1.6.1, semente 42, treino em 16/11/2026): Modelo 1 prevê `inadimplente_proximo_exercicio` (uso diagnóstico, limiar operacional 0,35); Modelo 2 prevê `divida_recuperada_12m` entre contribuintes com `valor_divida_consolidada > 0` e ordena a fila em faixas alta (> 0,66), média (0,33–0,66) e baixa (< 0,33). Baselines: ⟦PREENCHER: resultado da Árvore de Decisão / comparação da Sprint 4⟧.
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
- **Grupos/fatores avaliados:** faixa de renda (quartis), setor/bairro, tipo de tributo (ISS/IPTU).
- **Atributos sensíveis:** o modelo **não** deve usar idade, deficiência, raça, gênero. Setor e renda podem funcionar como *proxy* de vulnerabilidade — por isso são auditados. Atributos de entrada (12): `tipo_imovel`, `setor_urbano`, `area_construida_m2`, `valor_venal`, `valor_iptu_anual`, `distancia_centro_km`, `exercicios_inadimplentes_5a`, `tempo_inadimplencia_dias`, `valor_divida_consolidada`, `qtd_parcelamentos_anteriores`, `parcelamento_rompido`, `qtd_notificacoes`. `iptu_social` e `faixa_renda_setor` **não** são atributos de entrada; mas `setor_urbano` e `distancia_centro_km` podem carregar informação de renda do território (proxy), por isso a auditoria por faixa de renda.
- **Ambiente:** dados tabulares de carteira de contribuintes; desempenho pode variar com mudança de legislação, crise econômica ou campanhas de regularização.

## 4. Métricas de avaliação
- **Globais (conjunto de teste, `metadados_modelos.json`):**

| | ROC-AUC | Acurácia | Precisão | Recall | F1 |
|---|---|---|---|---|---|
| Modelo 1 — inadimplência (limiar 0,35) | 0,7069 | 0,6113 | 0,5758 | 0,8658 | 0,6916 |
| Modelo 2 — recuperabilidade | 0,6842 | 0,6367 | 0,6423 | 0,7154 | 0,6769 |

  O Modelo 1 usa limiar baixo (0,35): privilegia recall (0,87) à custa de precisão (0,58), isto é, sinaliza muita gente. Desempenho moderado é esperado em dados sintéticos com ruído; ⟦PREENCHER: AUC-PR, se calculada⟧.
- **Por subgrupo (renda e setor):** ⟦PREENCHER: tabelas de `docs/fairness_resultados.md`⟧ — taxa de seleção (paridade demográfica) e TPR (igualdade de oportunidade).
- **Por que essas métricas:** o custo de errar não é simétrico — falso positivo cobra quem não devia; falso negativo deixa de arrecadar.

## 5. Dados
- **Treino/validação/teste:** ⟦PREENCHER: descrever o split exatamente como foi feito na Sprint 4 (a carteira não tem coluna de data)⟧. Modelos treinados apenas com `iptu_social == 0`.
- **Origem:** `carteira_contribuintes.csv` (20.000 linhas, 17 colunas, 1.393 do IPTU Social) do repositório de referência da disciplina. **A carteira é sintética** (calibrada por agregados oficiais da Sefin, sem dado pessoal): conclusões de fairness descrevem o comportamento do modelo nesses dados, **não** a realidade dos contribuintes de Palmas.
- **Pré-processamento:** a carteira não tem valores nulos; variáveis categóricas (`tipo_imovel`, `setor_urbano`) codificadas e numéricas ⟦PREENCHER: escalonamento usado⟧.
- **Taxas observadas na carteira (20.000 registros):** `inadimplente_proximo_exercicio` = 51,2% no total; 59,6% em setores de renda baixa, 47,4% média e 37,8% alta; por setor, de 37,2% (Setor Comercial Central) a 62,8% (Taquari). Beneficiários do IPTU Social: 6,97% da carteira, com taxa de 57,2% contra 50,7% nos demais.
- **Sub-representações:** setores pequenos — Área de Expansão (1.001 registros), Setor Comercial Central (1.187), Jardim Aureny IV (1.380) e Taquari (1.596) — contra Plano Diretor Sul (4.460); faixa de renda alta tem 3.955 registros contra 9.204 da baixa; terrenos (1.409) e imóveis industriais (590) são poucos. Métricas desses subgrupos são mais instáveis. Os 1.393 do IPTU Social foram removidos da população-alvo do modelo.

## 6. Análise de viés
- **Testes:** paridade demográfica (razão ≥ 0,8 como referência da regra dos 80%) e igualdade de oportunidade, por faixa de renda e setor.
- **Achados:** ⟦PREENCHER com honestidade: onde há disparidade, tamanho, hipótese de causa⟧.
- **Mitigações:** exclusão formal do IPTU Social; ⟦PREENCHER: remoção de proxies, ajuste de limiar por grupo, reponderação — o que foi testado e o efeito⟧.
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
- Canal: ⟦PREENCHER: e-mail/ouvidoria da Sefin ou da equipe⟧. Prazo-alvo de resposta: ⟦PREENCHER⟧.
