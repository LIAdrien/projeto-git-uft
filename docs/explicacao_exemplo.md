# Exemplo real de explicação (Art. 20 LGPD)

Método: contribuição de cada variável ao log-odds da regressão logística, relativa à média da carteira (equivale ao SHAP exato para modelo linear). Sinal positivo = aumenta o score.


## Modelo 2 — recuperabilidade (ordena a fila)

Contribuinte (linha 12561, sem identificação) — score **0.90**

| variavel | contribuicao_log_odds |
|---|---|
| qtd_parcelamentos_anteriores | 1.312 |
| tempo_inadimplencia_dias | 0.663 |
| parcelamento_rompido | 0.106 |
| exercicios_inadimplentes_5a | 0.074 |
| valor_divida_consolidada | 0.059 |
| setor_urbano_Plano Diretor Sul | -0.043 |

Importância média (|contribuição|, amostra):

| variavel | importancia_media |
|---|---|
| tempo_inadimplencia_dias | 0.519 |
| qtd_parcelamentos_anteriores | 0.189 |
| parcelamento_rompido | 0.177 |
| valor_divida_consolidada | 0.077 |
| exercicios_inadimplentes_5a | 0.058 |
| valor_iptu_anual | 0.041 |
| valor_venal | 0.031 |
| setor_urbano_Area de Expansao | 0.029 |

> Explicação em linguagem simples: *redigir na revisão (ex.: "o score é alto principalmente porque ...")*.

## Modelo 1 — inadimplência (diagnóstico)

Contribuinte (linha 18870, sem identificação) — score **0.95**

| variavel | contribuicao_log_odds |
|---|---|
| exercicios_inadimplentes_5a | 2.05 |
| parcelamento_rompido | 0.449 |
| tipo_imovel_terreno | 0.203 |
| valor_venal | 0.12 |
| setor_urbano_Taquaralto | 0.108 |
| valor_iptu_anual | -0.058 |

Importância média (|contribuição|, amostra):

| variavel | importancia_media |
|---|---|
| exercicios_inadimplentes_5a | 0.543 |
| valor_venal | 0.18 |
| valor_iptu_anual | 0.14 |
| parcelamento_rompido | 0.134 |
| distancia_centro_km | 0.05 |
| setor_urbano_Plano Diretor Norte | 0.044 |
| setor_urbano_Taquaralto | 0.043 |
| setor_urbano_Taquari | 0.034 |

> Explicação em linguagem simples: *redigir na revisão (ex.: "o score é alto principalmente porque ...")*.