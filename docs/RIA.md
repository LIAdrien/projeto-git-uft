# Relatório de Impacto Algorítmico (RIA) — Inteligência Tributária, Sefin Palmas

> Documento técnico acadêmico elaborado pela Equipe 5 (BIINAR/UFT Palmas — 2026/2), não constitui parecer jurídico vinculante. Bases legais e fluxos operacionais devem ser validados com o Encarregado de Proteção de Dados (DPO) e a Procuradoria do Município antes de qualquer implantação em produção.

## 1. Mapeamento de dados pessoais e sensíveis (LGPD)

| Dado | Tipo | Finalidade | Base legal (hipótese) | Armazenamento | Retenção |
|---|---|---|---|---|---|
| CPF/CNPJ | Pessoal | Identificar devedor | Art. 7º, II e III (obrigação legal; políticas públicas) — Art. 23 (poder público) | **Pseudonimizado (hash com salt)** antes de gravar | Enquanto durar o crédito tributário + 5 anos (prazo prescricional do CTN, Art. 174) |
| Nome, endereço | Pessoal | Localizar para notificação | Art. 7º, II/III | Fora da base do modelo; restrito à base transacional da Sefin | Idem |
| Renda estimada do setor, valor e histórico de dívida | Pessoal / Patrimonial | Feature do modelo | Art. 7º, III | Base analítica anonimizada | Idem |
| Idade, aposentado, pensionista, PcD (origem do benefício) | Pessoal / **sensível (saúde)** no caso de PcD | Identificar IPTU Social (proteção) | Art. 7º, III; para PcD, Art. 11, II, "b" (políticas públicas) | Na carteira do projeto só existe a flag `iptu_social` (0/1); nunca é atributo de entrada do modelo | Mínima necessária para o filtro de exclusão anual |
| Score de inadimplência/recuperabilidade | Derivado | Priorização | Art. 7º, III | Base analítica com controle de acesso | Reprocessável; manter log de versão do modelo pelo prazo de auditoria (5 anos) |

- **Minimização (Art. 6º, III):** o modelo não usa nome, endereço, idade nem condição de deficiência; apenas variáveis estritamente necessárias à priorização fiscal.
- **Anonimização/pseudonimização:** hash com *salt* guardado em cofre fora do repositório; nenhum dado pessoal real no Git. A carteira usada no projeto é **sintética**.
- **Segurança (Art. 46):** controle de acesso baseado em papéis (RBAC), log imutável de consultas ao ranking e repositório de código isolado de bases reais.

## 2. Análise de fairness

- **Teste 1 — Paridade demográfica:** taxa de contribuintes sinalizados para cobrança por faixa de renda e por setor. Referência: razão entre menor e maior taxa ≥ 0,80 (regra dos 80%).
- **Teste 2 — Igualdade de oportunidade:** entre os que de fato ficaram inadimplentes (ou recuperaram a dívida), proporção corretamente sinalizada (TPR) por faixa de renda e setor.
- **Resultados:** Avaliação sobre os 18.607 contribuintes elegíveis (sem IPTU Social); Modelo 2 sobre os 15.361 com dívida. Tabelas completas em `docs/fairness_resultados.md`. Resumo por faixa de renda do setor:

| Modelo | Teste | Renda baixa | Média | Alta | Resultado |
|---|---|---|---|---|---|
| 1 — inadimplência (limiar 0,35) | Paridade demográfica (taxa de seleção) | 89,8% | 78,7% | 45,6% | razão menor/maior **0,51** |
| 1 — inadimplência | Igualdade de oportunidade (TPR) | 94,8% | 89,2% | 60,6% | diferença **0,34** |
| 2 — recuperabilidade (faixa alta) | Paridade demográfica | 13,5% | 18,4% | 26,0% | razão **0,52** |
| 2 — recuperabilidade | Igualdade de oportunidade (TPR) | 18,8% | 25,1% | 33,7% | diferença **0,15** |

Por setor urbano: no Modelo 1 a razão é 0,50 (Plano Diretor Norte 45,5% × Taquari 91,4%); no Modelo 2 é 0,23 (Taquari 8,9% × Área de Expansão 38,4%) e a diferença de TPR chega a 0,33.
- **Discussão honesta dos vieses:**
  1. **Nenhum dos dois modelos atinge a razão de 0,80** em nenhum dos cortes (renda ou setor).
  2. **Modelo 1 (diagnóstico):** a cobrança recairia fortemente sobre os setores de baixa renda: 90% dos contribuintes deles são sinalizados contra 46% nos de renda alta. Parte disso reflete diferenças reais de inadimplência na carteira (59,8% nos setores de renda baixa, 47,4% na média e 37,8% na alta), então paridade perfeita nem seria o objetivo. Mas o TPR mostra algo além da taxa-base: o modelo encontra 95% dos inadimplentes dos setores pobres e só 61% dos setores ricos, ou seja, inadimplentes de setores de renda alta escapam com mais facilidade. Além disso, o limiar 0,35 sinaliza 76% de toda a carteira: o filtro é pouco seletivo, por isso o Modelo 1 é restrito a uso diagnóstico.
  3. **Modelo 2 (ordena a fila):** as taxas reais de recuperação são parecidas entre as faixas (50,5% baixa, 51,3% média, 54,6% alta), mas a chance de cair na faixa "alta" é 13,5% na renda baixa contra 26,0% na alta, e o TPR é 18,8% contra 33,7%. Como a taxa-base não explica essa diferença, ela sugere que o modelo subestima a recuperabilidade de dívidas em setores de baixa renda. A explicação (seção 3) mostra que, no Modelo 2, o setor tem peso individual pequeno e o que mais pesa é `tempo_inadimplencia_dias`, seguido de parcelamentos anteriores e parcelamento rompido.
  4. **A direção do dano depende da ação:** para o Modelo 1, ser selecionado significa mais exposição à cobrança (dano aos setores pobres). Para o Modelo 2, ser colocado em prioridade menor pode aliviar a pressão coercitiva sobre setores pobres, mas também é tratamento desigual (menor oferta de acordos/parcelamentos facilitados) e deixa de arrecadar dívidas recuperáveis. Decidir qual efeito é aceitável é papel da gestão da Sefin, não do algoritmo.
  5. **Grupos pequenos:** a Área de Expansão tem cerca de 800 registros com dívida e a maior taxa de seleção no Modelo 2 (38,4%); esse número é estatisticamente menos estável.
  6. **Efeito da exclusão do IPTU Social:** sem ela, 1.250 dos 1.393 beneficiários (89,7%) entrariam na fila de cobrança, contra 76,4% dos demais. A exclusão é indispensável.
  7. **Limites:** a avaliação usa toda a carteira elegível (inclui dados de treino); os dados são sintéticos; os grupos descrevem o setor e não a renda individual (risco de falácia ecológica); e, como as taxas-base de inadimplência diferem entre grupos, paridade demográfica e igualdade de oportunidade não podem ser satisfeitas ao mesmo tempo no Modelo 1.
- **Mitigação:**
  - *(a) Exclusão formal do IPTU Social:* implementada na camada de dados e auditada em código (`src/iptu_social.py` e `tests/`).
  - *(b) Uso restrito:* o Modelo 1 serve só para planejamento/diagnóstico preventivo e nunca para acionar cobrança.
  - *(c) Pós-processamento por faixa de renda no Modelo 2 (`src/sprint5_mitigacao.py`):* cada faixa de renda recebeu limiar calibrado para manter a mesma taxa de seleção geral (17,5%). Antes × depois: razão de paridade demográfica **0,52 → 1,00**; diferença máxima de TPR **0,149 → 0,002**; precisão da seleção `0,703 → 0,709`; recall geral `0,239 → 0,241` (sem perda de eficiência). Limite: exige parecer jurídico antes de uso real por aplicar corte diferenciado por território.
  - *(d) Retreino sem proxies (`src/sprint5_retreino_sem_proxies.py`):* script complementar avalia a remoção de `setor_urbano` e `distancia_centro_km` e decompõe o peso das variáveis comportamentais (`tempo_inadimplencia_dias` e parcelamentos).

## 3. Direito à explicação (Art. 20 da LGPD)
- **Direito:** o titular pode pedir revisão de decisão automatizada e informações claras sobre critérios e procedimentos (Art. 20, *caput* e §1º).
- **Técnica:** como os dois modelos são regressões logísticas, a explicação é a contribuição de cada variável ao *log-odds* relativa à média da carteira — equivalente ao valor SHAP exato para modelo linear (`src/sprint5_fairness.py`). Importância global: tabela gerada em `docs/explicacao_exemplo.md`.
- **Exemplo real:** ver `docs/explicacao_exemplo.md` (contribuintes sem identificação, os de maior score de cada modelo).
  - *Modelo 2 (fila de cobrança):* "Este contribuinte recebeu 0,90 de chance de recuperação da dívida (faixa alta). O fator que mais pesou foi o histórico de parcelamentos anteriores, seguido pelo tempo em que a dívida está em aberto. Parcelamento rompido, número de anos em atraso e valor da dívida pesaram pouco, e o bairro quase não influenciou."
  - *Modelo 1 (diagnóstico):* "Este contribuinte recebeu 0,95 de risco de inadimplência. O fator que mais pesou foi ter muitos exercícios em atraso nos últimos cinco anos; depois, ter rompido um parcelamento, o imóvel ser um terreno, o valor do imóvel e a localização, esses dois últimos com peso pequeno."
  - *Importância geral:* no Modelo 2, `tempo_inadimplencia_dias` pesa em média `0,52`, mais que o dobro da segunda (`qtd_parcelamentos_anteriores`, `0,19`); no Modelo 1, `exercicios_inadimplentes_5a` domina (`0,54`), seguido de `valor_venal` (`0,18`) e `valor_iptu_anual` (`0,14`).
- **Avaliação da explicação:**
  - *Coerência:* o histórico de atraso e de parcelamentos é o que pesa mais nos dois modelos, alinhado ao comportamento tributário passado. Nenhum atributo pessoal sensível entra no cálculo.
  - *Atenção a proxies:* `valor_venal` e `valor_iptu_anual` (Modelo 1) refletem capacidade econômica do imóvel; o setor aparece com peso pequeno, mas não nulo.
  - *Limites:* a contribuição descreve a associação estatística no modelo linear e não relação causal; é relativa à média da carteira; os exemplos ilustram os maiores scores (casos extremos).
- **Fluxo de contestação:** pedido do cidadão → protocolo e revisão obrigatória por analista humano da Sefin → resposta fundamentada com os fatores principais em linguagem acessível → registro auditável da decisão.

## 4. Impactos sociais e recomendações
- **Benefícios:** cobrança administrativa mais eficiente, redução de custo operacional e aumento da arrecadação própria para financiamento de serviços públicos municipais.
- **Riscos:** cobrança indevida a cidadãos em vulnerabilidade socioeconômica; opacidade decisória; *feedback loop* territorial; dependência excessiva do score (*automation bias*); vazamento de dados fiscais.
- **Proteção do IPTU Social:** idosos, aposentados, pensionistas e PcD de baixa renda ficam fora das ações preditivas. Critérios previstos na legislação tributária municipal de Palmas (Código Tributário Municipal — Lei Complementar nº 285/2013 e regulamentação vigente do programa IPTU Social): *concessão automática* — pessoa física, imóvel único no município, uso exclusivamente residencial e imposto lançado abaixo do limite em UFIP; *por requerimento* — idoso acima de 65 anos, aposentado, pensionista ou pessoa com deficiência incapacitada para o trabalho, renda familiar de até 2 salários mínimos, imóvel único residencial e imposto dentro do teto legal.
- **Como a exclusão foi implementada e provada:** no painel, `pontuar()` filtra `iptu_social == 0` (regra `exclusao_obrigatoria` dos metadados) antes de qualquer score ou ranking e lança erro (`RuntimeError` / `ProtecaoIPTUSocialError`) se algum beneficiário sobrar; os modelos também foram treinados só com `iptu_social == 0` e `iptu_social` não é atributo de entrada. Testes automatizados: `tests/test_painel_exclusao.py` (usa um modelo falso que atribui score `0,99` a todos; se a exclusão falhasse, os protegidos liderariam a fila) e `tests/test_iptu_social.py`.
- **Riscos específicos do painel:**
  1. *(i) Rotulagem preventiva:* a aba *Situação da carteira* mostra "Em dia com alerta de risco" para contribuintes sem dívida marcada pelo Modelo 1; embora o painel restrinja esse grupo a ações educativas e não coercitivas, rotular contribuintes adimplentes exige estrita observância à finalidade e revisão humana.
  2. *(ii) Viés de valor no ranking por retorno esperado:* como o ranking padrão ordena por `retorno_esperado = valor_divida_consolidada × P(recuperação)`, dívidas de alto valor concentradas em imóveis de maior valor venal tendem a ocupar o topo absoluto da fila financeira, enquanto dívidas de menor montante (mais frequentes em setores de renda baixa) ficam no final da fila de diligência — o que reduz pressão coercitiva sobre pequenos devedores, mas pode atrasar a oferta de regularização amigável para esse público se não houver trilhas separadas por faixa de valor.
  3. *(iii) Transparência de subgrupos:* o painel exibe médias por faixa de renda na aba *Modelos & Subgrupos*, complementadas pelos testes formais de paridade demográfica e igualdade de oportunidade documentados neste RIA.
- **Uso responsável:** score é ferramenta de apoio à decisão, nunca decisão autônoma; revisão humana obrigatória e registrada; proibido o uso fora do escopo do Model Card.
- **Auditoria recomendada:** auditoria de fairness semestral; monitoramento contínuo de *data/concept drift*; revisão humana amostral mensal das decisões; publicação de relatório anual de transparência algorítmica; revisão deste RIA a cada alteração de modelo, base de dados ou legislação.
- **Responsáveis pela governança (em caso de adoção real):**
  - **Secretaria Municipal de Finanças (Sefin):** definição de políticas de cobrança, validação das faixas operacionais, revisão humana das filas e atendimento às contestações administrativas.
  - **Tecnologia da Informação (TI / Governo Digital):** manutenção do pipeline, controle de acesso (RBAC), registro de logs, versionamento de modelos e execução dos testes automatizados de exclusão do IPTU Social.
  - **Encarregado de Proteção de Dados (DPO) e Procuradoria Geral do Município:** validação jurídica das bases legais (LGPD), aprovação de eventuais ajustes territoriais de limiar e auditoria de conformidade do Art. 20.
