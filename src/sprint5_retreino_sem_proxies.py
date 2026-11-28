"""E2 (seção 2) — mitigação por RETREINO do Modelo 2 sem variáveis que funcionam como proxy de renda.

1) Reproduz o pipeline da Sprint 4 (mesma carteira, semente 42, mesma competência sorteada, mesmo corte
   de 01/04/2026, regressão logística com imputação + StandardScaler + OneHot). A AUC de teste deve dar
   0,6842, igual à do modelo salvo; se não der, pare e confira a versão do scikit-learn.
2) Decompõe a diferença média de log-odds entre renda alta e baixa por grupo de variável.
3) Retreina sem `setor_urbano` e sem `setor_urbano` + `distancia_centro_km` e mede fairness e AUC.
Uso:  python src/sprint5_retreino_sem_proxies.py   (gera docs/retreino_resultados.md)
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
from sprint5_fairness import localizar, md  # noqa: E402

SEMENTE = 42
ORD = ["baixa", "media", "alta"]
CAT0 = ["tipo_imovel", "setor_urbano"]
NUM0 = ["area_construida_m2", "valor_venal", "valor_iptu_anual", "distancia_centro_km",
        "exercicios_inadimplentes_5a", "tempo_inadimplencia_dias", "valor_divida_consolidada",
        "qtd_parcelamentos_anteriores", "parcelamento_rompido", "qtd_notificacoes"]
ALVO = "divida_recuperada_12m"


def montar(cat, num):
    pre = ColumnTransformer(
        ([("cat", OneHotEncoder(handle_unknown="ignore"), cat)] if cat else []) +
        [("num", Pipeline([("i", SimpleImputer(strategy="median")), ("e", StandardScaler())]), num)])
    return Pipeline([("p", pre), ("c", LogisticRegression(max_iter=1000, random_state=SEMENTE))])


def main():
    d = pd.read_csv(localizar("carteira_contribuintes.csv"), sep=";", encoding="utf-8-sig")
    u = d[d.iptu_social == 0].copy()
    rng = np.random.default_rng(SEMENTE)
    meses = pd.date_range("2024-01-01", "2026-10-01", freq="MS")
    u["competencia"] = rng.choice(meses, size=len(u))
    u = u.sort_values("competencia").reset_index(drop=True)
    corte = pd.Timestamp("2026-04-01")
    tr, te = u[u.competencia < corte], u[u.competencia >= corte]
    tr2, te2 = tr[tr.valor_divida_consolidada > 0], te[te.valor_divida_consolidada > 0]
    pop = u[u.valor_divida_consolidada > 0].copy()          # mesma população do sprint5_fairness.py

    def rodar(nome, cat, num):
        atr = cat + num
        m = montar(cat, num).fit(tr2[atr], tr2[ALVO])
        auc = roc_auc_score(te2[ALVO], m.predict_proba(te2[atr])[:, 1])
        sel = (m.predict_proba(pop[atr])[:, 1] > 0.66).astype(int)
        p = pop.assign(sel=sel)
        dp = p.groupby("faixa_renda_setor").sel.mean().reindex(ORD)
        tpr = p[p[ALVO] == 1].groupby("faixa_renda_setor").sel.mean().reindex(ORD)
        ds = p.groupby("setor_urbano").sel.mean()
        return m, {"AUC_teste": round(auc, 4), "taxa_selecao_geral": round(sel.mean(), 3),
                   "razao_paridade_renda": round(dp.min() / dp.max(), 3),
                   "dif_TPR_renda": round(tpr.max() - tpr.min(), 3),
                   "razao_paridade_setor": round(ds.min() / ds.max(), 3),
                   "precisao": round(p.loc[p.sel == 1, ALVO].mean(), 3),
                   "recall": round(p[p[ALVO] == 1].sel.mean(), 3)}

    m0, r0 = rodar("atual", CAT0, NUM0)
    _, r1 = rodar("sem setor_urbano", ["tipo_imovel"], NUM0)
    _, r2 = rodar("sem setor_urbano e distancia", ["tipo_imovel"], [c for c in NUM0 if c != "distancia_centro_km"])
    comp = pd.DataFrame({"atual (12 atributos)": r0, "sem setor_urbano": r1,
                         "sem setor_urbano e distancia_centro_km": r2})
    comp.index.name = "metrica"

    # Decomposição da diferença renda alta x baixa no modelo atual
    atr = CAT0 + NUM0
    Z = m0[0].transform(pop[atr])
    Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
    nomes = [n.split("__")[-1] for n in m0[0].get_feature_names_out()]
    C = Z * m0[-1].coef_[0]
    C = pd.DataFrame(C - C.mean(axis=0), columns=nomes, index=pop.index)
    g = C.T.groupby(lambda n: "setor_urbano (todas)" if n.startswith("setor_urbano")
                    else "tipo_imovel (todas)" if n.startswith("tipo_imovel") else n).sum().T
    g["faixa"] = pop.faixa_renda_setor
    dec = g.groupby("faixa").mean().reindex(ORD).T
    dec["alta_menos_baixa"] = dec["alta"] - dec["baixa"]
    dec = dec.reindex(dec["alta_menos_baixa"].abs().sort_values(ascending=False).index).head(8).round(3)
    dec.index.name = "grupo_de_variaveis"
    coef = pd.Series(m0[-1].coef_[0], index=nomes)
    coef = coef.reindex(coef.abs().sort_values(ascending=False).index).head(8).round(3).rename("coeficiente_padronizado")

    L = ["# Retreino sem proxies de renda — Modelo 2 (gerado por src/sprint5_retreino_sem_proxies.py)\n",
         "Verificação: a AUC de teste da linha `atual` deve ser 0,6842 (a do modelo salvo na Sprint 4).\n",
         "## Antes × depois do retreino\n", md(comp),
         "\n## Maiores coeficientes do modelo atual (variáveis padronizadas)\n", md(coef.to_frame()),
         "\n## De onde vem a diferença entre renda alta e baixa (média da contribuição ao log-odds)\n", md(dec),
         "\n> Valor positivo em `alta_menos_baixa` = empurra a favor da faixa de renda alta."]
    os.makedirs("docs", exist_ok=True)
    open("docs/retreino_resultados.md", "w", encoding="utf-8").write("\n".join(L))
    print(comp.to_string())
    print("\n", dec.to_string())
    print("OK: docs/retreino_resultados.md gerado.")


if __name__ == "__main__":
    main()
