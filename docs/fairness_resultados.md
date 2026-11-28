# Resultados de fairness (gerado por src/sprint5_fairness.py)

- Carteira: 20000 registros | IPTU Social (protegidos, fora do modelo): 1393 | elegíveis: 18607
- Avaliação sobre **todos os elegíveis** (a carteira não tem coluna de data; se a Sprint 4 usou um split próprio, troque `universo` por esse conjunto de teste).
- `faixa_renda_setor` e `setor_urbano` descrevem o **setor**, não a renda individual.

## Modelo 1 — inadimplência (limiar 0.35)

Registros avaliados: 18607 | taxa geral de seleção: 0.764

### Paridade demográfica por `faixa_renda_setor`

| faixa_renda_setor | taxa_selecao | n | razao_vs_maior |
|---|---|---|---|
| baixa | 0.8976 | 7976 | 1.0 |
| media | 0.7865 | 6683 | 0.8762 |
| alta | 0.4564 | 3948 | 0.5085 |

Razão menor/maior: **0.508** (referência ≥ 0,80)

### Igualdade de oportunidade por `faixa_renda_setor`

| faixa_renda_setor | tpr | n_positivos | dif_vs_maior |
|---|---|---|---|
| baixa | 0.9476 | 4771 | 0.0 |
| media | 0.8918 | 3169 | -0.0558 |
| alta | 0.6058 | 1494 | -0.3418 |

Diferença TPR máxima: **0.342**

### Paridade demográfica por `setor_urbano`

| setor_urbano | taxa_selecao | n | razao_vs_maior |
|---|---|---|---|
| Area de Expansao | 0.7969 | 975 | 0.8717 |
| Aureny | 0.89 | 3182 | 0.9735 |
| Jardim Aureny IV | 0.7776 | 1349 | 0.8505 |
| Plano Diretor Norte | 0.4546 | 2763 | 0.4972 |
| Plano Diretor Sul | 0.7869 | 4359 | 0.8607 |
| Setor Comercial Central | 0.4608 | 1185 | 0.504 |
| Taquaralto | 0.898 | 3441 | 0.9822 |
| Taquari | 0.9143 | 1353 | 1.0 |

Razão menor/maior: **0.497** (referência ≥ 0,80)

### Igualdade de oportunidade por `setor_urbano`

| setor_urbano | tpr | n_positivos | dif_vs_maior |
|---|---|---|---|
| Area de Expansao | 0.8934 | 469 | -0.0632 |
| Aureny | 0.942 | 1880 | -0.0146 |
| Jardim Aureny IV | 0.888 | 643 | -0.0686 |
| Plano Diretor Norte | 0.5998 | 1052 | -0.3568 |
| Plano Diretor Sul | 0.8926 | 2057 | -0.0641 |
| Setor Comercial Central | 0.6199 | 442 | -0.3367 |
| Taquaralto | 0.949 | 2038 | -0.0077 |
| Taquari | 0.9566 | 853 | 0.0 |

Diferença TPR máxima: **0.357**

## Modelo 2 — recuperabilidade (selecionado = faixa alta, score > 0,66)

Registros avaliados: 15361 | taxa geral de seleção: 0.175

### Paridade demográfica por `faixa_renda_setor`

| faixa_renda_setor | taxa_selecao | n | razao_vs_maior |
|---|---|---|---|
| baixa | 0.1353 | 7110 | 0.5207 |
| media | 0.1836 | 5453 | 0.7065 |
| alta | 0.2598 | 2798 | 1.0 |

Razão menor/maior: **0.521** (referência ≥ 0,80)

### Igualdade de oportunidade por `faixa_renda_setor`

| faixa_renda_setor | tpr | n_positivos | dif_vs_maior |
|---|---|---|---|
| baixa | 0.1877 | 3591 | -0.1494 |
| media | 0.2507 | 2800 | -0.0863 |
| alta | 0.337 | 1528 | 0.0 |

Diferença TPR máxima: **0.149**

### Paridade demográfica por `setor_urbano`

| setor_urbano | taxa_selecao | n | razao_vs_maior |
|---|---|---|---|
| Area de Expansao | 0.3835 | 798 | 1.0 |
| Aureny | 0.1409 | 2818 | 0.3674 |
| Jardim Aureny IV | 0.1201 | 1107 | 0.3133 |
| Plano Diretor Norte | 0.2878 | 1960 | 0.7504 |
| Plano Diretor Sul | 0.1584 | 3548 | 0.4131 |
| Setor Comercial Central | 0.1945 | 838 | 0.5073 |
| Taquaralto | 0.1485 | 3071 | 0.3872 |
| Taquari | 0.0893 | 1221 | 0.2328 |

Razão menor/maior: **0.233** (referência ≥ 0,80)

### Igualdade de oportunidade por `setor_urbano`

| setor_urbano | tpr | n_positivos | dif_vs_maior |
|---|---|---|---|
| Area de Expansao | 0.46 | 463 | 0.0 |
| Aureny | 0.1914 | 1426 | -0.2686 |
| Jardim Aureny IV | 0.1733 | 554 | -0.2868 |
| Plano Diretor Norte | 0.3699 | 1084 | -0.0901 |
| Plano Diretor Sul | 0.2204 | 1783 | -0.2396 |
| Setor Comercial Central | 0.2568 | 444 | -0.2033 |
| Taquaralto | 0.2051 | 1565 | -0.2549 |
| Taquari | 0.1333 | 600 | -0.3267 |

Diferença TPR máxima: **0.327**

## Contrafactual — Modelo 1 sem a exclusão do IPTU Social

Taxa de seleção dos beneficiários do IPTU Social: **0.897** contra **0.764** nos demais. Sem a exclusão, 1250 beneficiários entrariam na fila.