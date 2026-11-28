"""E2 (seções 2 e 3) — fairness por faixa de renda e setor + explicação (Art. 20 LGPD).

Uso (na raiz do repositório da equipe):  python src/sprint5_fairness.py
Lê:     carteira_contribuintes.csv (separador ';'), os 2 .joblib e metadados_modelos.json,
        onde estiverem: pasta atual, models/ ou data/
Gera:   docs/fairness_resultados.md  e  docs/explicacao_exemplo.md
Requer: pandas, numpy, scikit-learn, joblib.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from iptu_social import separar_protegidos  # noqa: E402

RAIZ = Path.cwd()
AQUI = Path(__file__).resolve().parent
PASTAS = [RAIZ, RAIZ / "models", RAIZ / "data", AQUI.parent, AQUI.parent / "models", AQUI.parent / "data"]


def localizar(nome: str) -> Path:
    """Procura o arquivo na pasta atual, em models/ e em data/ (igual ao painel)."""
    for pasta in PASTAS:
        if (pasta / nome).exists():
            return pasta / nome
    raise FileNotFoundError(f"Não encontrei '{nome}'. Procurei em: " + "; ".join(str(p) for p in PASTAS))


GRUPOS = ["faixa_renda_setor", "setor_urbano"]   # renda do setor NÃO é feature; setor é
ORDEM_RENDA = ["baixa", "media", "alta"]


def md(df: pd.DataFrame) -> str:
    """Tabela Markdown sem depender de 'tabulate'."""
    d = df.reset_index()
    cab = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "|".join(["---"] * len(d.columns)) + "|"
    linhas = ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def paridade_demografica(df, grupo, sel):
    t = df.assign(_s=sel).groupby(grupo)["_s"].agg(taxa_selecao="mean", n="size")
    t["razao_vs_maior"] = t["taxa_selecao"] / t["taxa_selecao"].max()   # regra dos 80%: >= 0,8
    return t.round(4)


def igualdade_oportunidade(df, grupo, y, sel):
    d = df.assign(_y=y, _s=sel)
    d = d[d["_y"] == 1]
    t = d.groupby(grupo)["_s"].agg(tpr="mean", n_positivos="size")
    t["dif_vs_maior"] = t["tpr"] - t["tpr"].max()
    return t.round(4)


def resumo(t, col):
    return f"{t[col].min():.3f} (menor) / {t[col].max():.3f} (maior)"


def contribuicoes_lineares(modelo, X: pd.DataFrame, i: int, fundo: int = 2000):
    """Contribuição de cada variável ao log-odds, relativa à média da carteira.
    Para regressão logística isso equivale ao valor SHAP exato (variáveis independentes)."""
    pre, clf = modelo[:-1], modelo[-1]
    Z = pre.transform(X.iloc[:fundo] if len(X) > fundo else X)
    z = pre.transform(X.iloc[[i]])
    Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
    z = z.toarray() if hasattr(z, "toarray") else np.asarray(z)
    nomes = [n.split("__")[-1] for n in pre.get_feature_names_out()]
    return pd.Series(clf.coef_[0] * (z[0] - Z.mean(axis=0)), index=nomes)


def rodar_modelo(df, meta, chave, universo, eh_prioridade):
    m = meta[chave]
    modelo = joblib.load(localizar(m["arquivo"]))
    feats = meta["atributos_entrada"]
    base = universo(df).copy()
    base["score"] = modelo.predict_proba(base[feats])[:, 1]
    base["sel"] = eh_prioridade(base["score"], m).astype(int)
    return modelo, base, m


def secao(titulo, base, alvo):
    out = [f"\n## {titulo}\n", f"Registros avaliados: {len(base)} | taxa geral de seleção: {base['sel'].mean():.3f}"]
    for g in GRUPOS:
        pdm = paridade_demografica(base, g, base["sel"])
        eo = igualdade_oportunidade(base, g, base[alvo], base["sel"])
        if g == "faixa_renda_setor":
            pdm, eo = pdm.reindex(ORDEM_RENDA), eo.reindex(ORDEM_RENDA)
        out += [f"\n### Paridade demográfica por `{g}`\n", md(pdm),
                f"\nRazão menor/maior: **{pdm['taxa_selecao'].min() / pdm['taxa_selecao'].max():.3f}** (referência ≥ 0,80)",
                f"\n### Igualdade de oportunidade por `{g}`\n", md(eo),
                f"\nDiferença TPR máxima: **{eo['tpr'].max() - eo['tpr'].min():.3f}**"]
    return out


def main():
    df = pd.read_csv(localizar("carteira_contribuintes.csv"), sep=";", encoding="utf-8-sig")
    meta = json.load(open(localizar("metadados_modelos.json"), encoding="utf-8"))
    eleg, prot = separar_protegidos(df)
    L = ["# Resultados de fairness (gerado por src/sprint5_fairness.py)\n",
         f"- Carteira: {len(df)} registros | IPTU Social (protegidos, fora do modelo): {len(prot)} | elegíveis: {len(eleg)}",
         "- Avaliação sobre **todos os elegíveis** (a carteira não tem coluna de data; se a Sprint 4 usou um split próprio, "
         "troque `universo` por esse conjunto de teste).",
         "- `faixa_renda_setor` e `setor_urbano` descrevem o **setor**, não a renda individual."]

    # Modelo 1 — inadimplência (uso diagnóstico): selecionado = score >= limiar operacional
    _, b1, m1 = rodar_modelo(df, meta, "modelo_1_inadimplencia", lambda d: separar_protegidos(d)[0],
                             lambda s, m: s >= m["limiar_operacional"])
    L += secao(f"Modelo 1 — inadimplência (limiar {m1['limiar_operacional']})", b1, m1["alvo"])

    # Modelo 2 — recuperabilidade: selecionado = faixa 'alta' (> 0,66), universo com dívida
    mod2, b2, m2 = rodar_modelo(df, meta, "modelo_2_recuperabilidade",
                                lambda d: separar_protegidos(d)[0].query("valor_divida_consolidada > 0"),
                                lambda s, m: s > 0.66)
    L += secao("Modelo 2 — recuperabilidade (selecionado = faixa alta, score > 0,66)", b2, m2["alvo"])

    # Contrafactual: o que aconteceria SEM a exclusão do IPTU Social (Modelo 1)
    mod1 = joblib.load(localizar(m1["arquivo"]))
    tudo = df.copy()
    tudo["sel"] = (mod1.predict_proba(tudo[meta["atributos_entrada"]])[:, 1] >= m1["limiar_operacional"]).astype(int)
    L += ["\n## Contrafactual — Modelo 1 sem a exclusão do IPTU Social\n",
          f"Taxa de seleção dos beneficiários do IPTU Social: **{tudo.loc[tudo.iptu_social == 1, 'sel'].mean():.3f}** "
          f"contra **{tudo.loc[tudo.iptu_social == 0, 'sel'].mean():.3f}** nos demais. "
          f"Sem a exclusão, {int(tudo.loc[tudo.iptu_social == 1, 'sel'].sum())} beneficiários entrariam na fila."]
    os.makedirs("docs", exist_ok=True)
    open("docs/fairness_resultados.md", "w", encoding="utf-8").write("\n".join(L))

    # Explicação (Art. 20): contribuinte elegível no topo da fila do Modelo 2 + importância média
    T = ["# Exemplo real de explicação (Art. 20 LGPD)\n",
         "Método: contribuição de cada variável ao log-odds da regressão logística, relativa à média da carteira "
         "(equivale ao SHAP exato para modelo linear). Sinal positivo = aumenta o score.\n"]
    for nome, mod, base in (("Modelo 2 — recuperabilidade (ordena a fila)", mod2, b2),
                            ("Modelo 1 — inadimplência (diagnóstico)", mod1, b1)):
        feats = meta["atributos_entrada"]
        topo = base.sort_values("score", ascending=False).index[0]
        X = base[feats]
        i = X.index.get_loc(topo)
        c = contribuicoes_lineares(mod, X, i)
        top = c.reindex(c.abs().sort_values(ascending=False).index).head(6).round(3)
        glob = pd.Series(np.abs(np.vstack([contribuicoes_lineares(mod, X, j).values for j in range(0, len(X), max(1, len(X)//300))])).mean(axis=0),
                         index=c.index).sort_values(ascending=False).head(8).round(3)
        T += [f"\n## {nome}\n", f"Contribuinte (linha {topo}, sem identificação) — score **{base.loc[topo, 'score']:.2f}**\n",
              md(top.rename("contribuicao_log_odds").rename_axis("variavel").to_frame()),
              f"\nImportância média (|contribuição|, amostra):\n", md(glob.rename("importancia_media").rename_axis("variavel").to_frame()),
              "\n> Explicação em linguagem simples: *redigir na revisão (ex.: \"o score é alto principalmente porque ...\")*."]
    open("docs/explicacao_exemplo.md", "w", encoding="utf-8").write("\n".join(T))
    print("OK: docs/fairness_resultados.md e docs/explicacao_exemplo.md gerados.")


if __name__ == "__main__":
    main()
