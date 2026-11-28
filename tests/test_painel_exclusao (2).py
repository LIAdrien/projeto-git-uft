"""E3 — prova, no pipeline do painel, que o IPTU Social é excluído da cobrança preditiva.

Testa a função `pontuar` do painel (app/painel_app.py) com um modelo falso que dá score
máximo a todos: se a exclusão falhar, os protegidos apareceriam no topo da fila.
"""
import importlib.util
import os

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("altair")

RAIZ = os.path.join(os.path.dirname(__file__), "..")
PAINEL = os.path.join(RAIZ, "app", "painel_app.py")


def _carregar_painel():
    spec = importlib.util.spec_from_file_location("painel_app", PAINEL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ModeloFalso:
    classes_ = np.array([0, 1])

    def predict_proba(self, X):
        p = np.full(len(X), 0.99)
        return np.column_stack([1 - p, p])


META = {
    "exclusao_obrigatoria": "iptu_social == 0",
    "atributos_entrada": ["valor_divida_consolidada"],
    "modelo_1_inadimplencia": {"limiar_operacional": 0.35},
}


def _carteira_sintetica():
    return pd.DataFrame({
        "id_contribuinte": list("abcdef"),
        "setor_urbano": ["X"] * 6,
        "faixa_renda_setor": ["baixa"] * 6,
        "iptu_social": [1, 0, 1, 0, 0, 1],
        "valor_divida_consolidada": [900.0, 500.0, 800.0, 300.0, 0.0, 700.0],
    })


def test_pontuar_exclui_iptu_social():
    painel = _carregar_painel()
    base = painel.pontuar(_carteira_sintetica(), META, ModeloFalso(), ModeloFalso())
    assert (base["iptu_social"] == 0).all()
    assert set(base["id_contribuinte"]) == {"b", "d", "e"}


def test_fila_de_cobranca_nao_tem_protegidos():
    painel = _carregar_painel()
    base = painel.pontuar(_carteira_sintetica(), META, ModeloFalso(), ModeloFalso())
    fila = base[base["valor_divida_consolidada"] > 0].sort_values("retorno_esperado", ascending=False)
    assert not set(fila["id_contribuinte"]) & {"a", "c", "f"}
    assert fila["id_contribuinte"].iloc[0] == "b"   # e não "a" (dívida 900, protegido)


def test_trava_barra_exclusao_adulterada():
    painel = _carregar_painel()
    meta_ruim = dict(META, exclusao_obrigatoria="valor_divida_consolidada >= 0")  # não exclui ninguém
    with pytest.raises(RuntimeError):
        painel.pontuar(_carteira_sintetica(), meta_ruim, ModeloFalso(), ModeloFalso())


CARTEIRA = os.path.join(RAIZ, "data", "carteira_contribuintes.csv")


@pytest.mark.skipif(not os.path.exists(CARTEIRA), reason="carteira não está no repositório")
def test_carteira_real_sem_protegidos_apos_pontuar():
    painel = _carregar_painel()
    df = pd.read_csv(CARTEIRA, sep=";", encoding="utf-8-sig")
    base = painel.pontuar(df, META, ModeloFalso(), ModeloFalso())
    assert len(base) == int((df["iptu_social"] == 0).sum())
    assert not base["id_contribuinte"].isin(df.loc[df["iptu_social"] == 1, "id_contribuinte"]).any()
