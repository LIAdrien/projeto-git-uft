# Relatório de Impacto Algorítmico (RIA) — Inteligência Tributária, Sefin Palmas

> Documento técnico acadêmico, não é parecer jurídico. Bases legais citadas devem ser validadas com o encarregado (DPO) da Prefeitura. **⟦PREENCHER⟧** = dado da sua execução.

## 1. Mapeamento de dados pessoais e sensíveis (LGPD)

| Dado | Tipo | Finalidade | Base legal (hipótese) | Armazenamento | Retenção |
|---|---|---|---|---|---|
| CPF/CNPJ | Pessoal | Identificar devedor | Art. 7º, II e III (obrigação legal; políticas públicas) — Art. 23 (poder público) | **Pseudonimizado (hash)** antes de gravar | Enquanto durar a dívida + prazo legal ⟦PREENCHER⟧ |
| Nome, endereço | Pessoal | Localizar para notificação | Art. 7º, II/III | Fora da base do modelo; só na base transacional da Sefin | Idem |
| Renda, valor e histórico de dívida | Pessoal | Feature do modelo | Art. 7º, III | Base analítica anonimizada | Idem |
| Idade, aposentado, pensionista, PcD (origem do benefício) | Pessoal / **sensível (saúde)** no caso de PcD | Identificar IPTU Social (proteção) | Art. 7º, III; para PcD, Art. 11, II, "b" (políticas públicas) | Na carteira do projeto só existe a flag `iptu_social` (0/1); nunca é atributo de entrada do modelo | Mínima necessária |
| Score de inadimplência/recuperabilidade | Derivado | Priorização | Art. 7º, III | Base analítica | Reprocessável; guardar versão do modelo |

- **Minimização (Art. 6º, III):** o modelo não usa nome, endereço, idade nem deficiência; só variáveis necessárias.
- **Anonimização/pseudonimização:** hash com *salt* guardado fora do repositório; nenhum dado pessoal real no Git. A carteira usada no projeto é **sintética**.
- **Segurança (Art. 46):** acesso por perfil, log de consultas ao ranking, repositório sem dados pessoais.

## 2. Análise de fairness

- **Teste 1 — Paridade demográfica:** taxa de contribuintes sinalizados para cobrança por faixa de renda e por setor. Referência: razão entre menor e maior taxa ≥ 0,8.
- **Teste 2 — Igualdade de oportunidade:** entre os que de fato ficaram inadimplentes, proporção corretamente sinalizada (TPR) por faixa de renda e setor.
- **Resultados:** ⟦PREENCHER: cole as tabelas de `docs/fairness_resultados.md` e escreva 3–5 linhas de leitura⟧.
- **Discussão honesta dos vieses:** ⟦PREENCHER⟧. Pontos a considerar: (i) renda e setor podem ser proxies de vulnerabilidade; (ii) a carteira é sintética, então a disparidade pode refletir como foi gerada; (iii) grupos pequenos geram métricas instáveis; (iv) os dois critérios podem entrar em conflito quando a taxa-base de inadimplência difere entre grupos.
- **Contexto dos dados:** na carteira, a inadimplência observada é maior em setores de renda baixa (59,6%) do que de renda alta (37,8%); um modelo que prevê "quem provavelmente deve" tende a aprender esse padrão territorial. O beneficiário do IPTU Social tem taxa de 57,2% contra 50,7% dos demais, então, sem exclusão, seria sinalizado com mais frequência.
- **Mitigação:** (a) exclusão formal do IPTU Social (E3, testada); (b) ⟦PREENCHER: o que foi testado — remover proxy, reponderar, limiar por grupo — e o efeito medido⟧; (c) revisão humana.
- **Comparação ilustrativa:** o script também mede a população inteira, para mostrar o efeito da exclusão do IPTU Social.

## 3. Direito à explicação (Art. 20 da LGPD)
- **Direito:** o titular pode pedir revisão de decisão automatizada e informações claras sobre critérios e procedimentos (Art. 20, *caput* e §1º).
- **Técnica:** como os dois modelos são regressões logísticas, a explicação é a contribuição de cada variável ao log-odds relativa à média da carteira — equivalente ao valor SHAP exato para modelo linear (`src/sprint5_fairness.py`). Importância global: tabela gerada em `docs/explicacao_exemplo.md`.
- **Exemplo real:** ver `docs/explicacao_exemplo.md` (contribuinte sem identificação). Texto leigo: ⟦PREENCHER⟧.
- **Avaliação da explicação:** ⟦PREENCHER: a explicação faz sentido? Há variável inesperada/proxy? Qual a limitação (SHAP descreve o modelo, não causalidade)?⟧
- **Fluxo de contestação:** pedido → revisão por analista humano → resposta com critérios → registro. Auditoria do Art. 20, §2º, pela autoridade, se houver sigilo comercial/industrial.

## 4. Impactos sociais e recomendações
- **Benefícios:** cobrança mais eficiente, redução de custo operacional, arrecadação para serviços públicos.
- **Riscos:** cobrança indevida a vulneráveis; opacidade; *feedback loop*; dependência excessiva do score; vazamento de dados.
- **Proteção do IPTU Social:** idosos, aposentados, pensionistas e PcD de baixa renda ficam fora das ações preditivas. Critérios descritos no painel da equipe (⟦PREENCHER: citar a lei/decreto municipal⟧): *concessão automática* — pessoa física, imóvel único no município, uso só residencial, imposto abaixo de 50 Ufip; *por pedido* — idoso acima de 65 anos, aposentado, pensionista ou pessoa com deficiência incapacitada para o trabalho, renda até 2 salários mínimos, imóvel único residencial, imposto abaixo de 150 Ufip.
- **Como a exclusão foi implementada e provada:** no painel, `pontuar()` filtra `iptu_social == 0` (regra `exclusao_obrigatoria` dos metadados) antes de qualquer score ou ranking e lança erro se algum beneficiário sobrar; os modelos também foram treinados só com `iptu_social == 0` e `iptu_social` não é atributo de entrada. Testes automatizados: `tests/test_painel_exclusao.py` (usa um modelo falso que dá score máximo a todos; se a exclusão falhasse, os protegidos liderariam a fila) e `tests/test_iptu_social.py`.
- **Riscos específicos do painel:** (i) a aba *Situação da carteira* mostra "Em dia com alerta de risco": são contribuintes sem dívida que o modelo marca como risco; o painel os trata como candidatos a ação educativa, não a cobrança, mas rotular quem está em dia é um tratamento preditivo sobre pessoas regulares e exige a mesma cautela (finalidade, revisão humana); (ii) o ranking padrão ordena por retorno esperado (dívida × chance de recuperar), o que tende a priorizar dívidas grandes e pode deixar dívidas pequenas — mais comuns em setores de renda baixa — por último: ⟦PREENCHER: verificar nos dados e discutir⟧; (iii) o painel só mostra médias por faixa de renda (aba *Modelos & Subgrupos*), sem os testes formais de paridade e igualdade de oportunidade, que estão neste RIA.
- **Uso responsável:** score é apoio, não decisão; revisão humana registrada; proibido o uso fora do escopo do Model Card.
- **Auditoria recomendada:** fairness a cada ciclo (semestral); monitorar *drift*; amostra mensal de decisões para revisão; relatório público resumido; reavaliar este RIA a cada mudança de modelo, dados ou legislação.
- **Responsáveis:** ⟦PREENCHER: papel de cada área (Sefin, TI, DPO)⟧.
