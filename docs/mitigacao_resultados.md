# Experimento de mitigação — Modelo 2 (gerado por src/sprint5_mitigacao.py)

Taxa de seleção-alvo (igual à atual): 0.175. Cortes por faixa: baixa = 0.645, media = 0.663, alta = 0.688

## Antes × depois

| metrica | corte_unico_0.66 | corte_por_faixa_de_renda |
|---|---|---|
| taxa_selecao_geral | 0.1751 | 0.1751 |
| razao_paridade_demografica | 0.521 | 1.0 |
| dif_TPR_max | 0.149 | 0.002 |
| precisao_da_selecao | 0.703 | 0.709 |
| recall_geral | 0.239 | 0.241 |

## Depois — paridade demográfica por faixa de renda

| faixa_renda_setor | taxa_selecao | n | razao_vs_maior |
|---|---|---|---|
| baixa | 0.1751 | 7110 | 0.9998 |
| media | 0.1751 | 5453 | 1.0 |
| alta | 0.1751 | 2798 | 1.0 |

## Depois — igualdade de oportunidade por faixa de renda

| faixa_renda_setor | tpr | n_positivos | dif_vs_maior |
|---|---|---|---|
| baixa | 0.2417 | 3591 | 0.0 |
| media | 0.2407 | 2800 | -0.001 |
| alta | 0.2395 | 1528 | -0.0022 |

> Leitura: compare `razao_paridade_demografica` e `dif_TPR_max` com a mudança em `precisao_da_selecao` e `recall_geral` (o custo de eficiência da mitigação).