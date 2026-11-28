"""E2 (seção 2) — experimento de MITIGAÇÃO para o Modelo 2 (recuperabilidade).

Pós-processamento: em vez de um único corte (score > 0,66), usa um corte por faixa de renda do
setor, de modo que cada faixa tenha a mesma taxa de seleção da carteira. Não retreina nada.
Mede o efeito em fairness e o custo em precisão/recall.   Uso:  python src/sprint5_mitigacao.py
ATENÇÃO: corte por grupo é tratamento diferenciado por território; é um experimento, e uso real
exigiria análise jurídica e decisão da Sefin.
"""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from iptu_social import separar_protegidos  # noqa: E402
from sprint5_fairness import (localizar, md, paridade_demografica,  # noqa: E402
                              igualdade_oportunidade, ORDEM_RENDA)

CORTE_ATUAL = 0.66


def metricas(base, sel, alvo):
    sel = pd.Series(sel, index=base.index).astype(int)
    pdm = paridade_demografica(base, "faixa_renda_setor", sel).reindex(ORDEM_RENDA)
    eo = igualdade_oportunidade(base, "faixa_renda_setor", base[alvo], sel).reindex(ORDEM_RENDA)
    prec = base.loc[sel == 1, alvo].mean()
    rec = sel[base[alvo] == 1].mean()
    return {
        "taxa_selecao_geral": round(sel.mean(), 4),
        "razao_paridade_demografica": round(pdm.taxa_selecao.min() / pdm.taxa_selecao.max(), 3),
        "dif_TPR_max": round(eo.tpr.max() - eo.tpr.min(), 3),
        "precisao_da_selecao": round(prec, 3),
        "recall_geral": round(rec, 3),
    }, pdm, eo


def main():
    meta = json.load(open(localizar("metadados_modelos.json"), encoding="utf-8"))
    m2 = meta["modelo_2_recuperabilidade"]
    df = pd.read_csv(localizar("carteira_contribuintes.csv"), sep=";", encoding="utf-8-sig")
    base = separar_protegidos(df)[0].query("valor_divida_consolidada > 0").copy()
    modelo = joblib.load(localizar(m2["arquivo"]))
    base["score"] = modelo.predict_proba(base[meta["atributos_entrada"]])[:, 1]
    alvo = m2["alvo"]

    antes, pdm0, eo0 = metricas(base, base.score > CORTE_ATUAL, alvo)
    taxa = float((base.score > CORTE_ATUAL).mean())
    cortes = {g: float(np.quantile(base.loc[base.faixa_renda_setor == g, "score"], 1 - taxa)) for g in ORDEM_RENDA}
    sel1 = base.apply(lambda r: r.score >= cortes[r.faixa_renda_setor], axis=1)
    depois, pdm1, eo1 = metricas(base, sel1, alvo)

    comp = pd.DataFrame({"corte_unico_0.66": antes, "corte_por_faixa_de_renda": depois})
    comp.index.name = "metrica"
    L = ["# Experimento de mitigação — Modelo 2 (gerado por src/sprint5_mitigacao.py)\n",
         f"Taxa de seleção-alvo (igual à atual): {taxa:.3f}. Cortes por faixa: " +
         ", ".join(f"{g} = {c:.3f}" for g, c in cortes.items()) + "\n",
         "## Antes × depois\n", md(comp),
         "\n## Depois — paridade demográfica por faixa de renda\n", md(pdm1),
         "\n## Depois — igualdade de oportunidade por faixa de renda\n", md(eo1),
         "\n> Leitura: compare `razao_paridade_demografica` e `dif_TPR_max` com a mudança em `precisao_da_selecao` "
         "e `recall_geral` (o custo de eficiência da mitigação)."]
    os.makedirs("docs", exist_ok=True)
    open("docs/mitigacao_resultados.md", "w", encoding="utf-8").write("\n".join(L))
    print(comp.to_string())
    print("OK: docs/mitigacao_resultados.md gerado.")


if __name__ == "__main__":
    main()
