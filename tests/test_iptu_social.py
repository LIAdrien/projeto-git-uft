import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import iptu_social as ips  # noqa: E402


@pytest.fixture
def df_flag():
    return pd.DataFrame({
        "iptu_social": [True, False, True, False, False],
        "score_inadimplencia": [0.99, 0.80, 0.95, 0.40, 0.10],
    })


def test_ranking_nao_contem_protegidos(df_flag):
    r = ips.ranking_cobranca(df_flag)
    assert not r["iptu_social"].any()
    assert len(r) == 3


def test_protegidos_com_score_alto_ficam_fora(df_flag):
    r = ips.ranking_cobranca(df_flag, top=1)
    assert r["score_inadimplencia"].iloc[0] == 0.80  # não 0.99


def test_particao_completa_sem_perda(df_flag):
    eleg, prot = ips.separar_protegidos(df_flag)
    assert len(eleg) + len(prot) == len(df_flag)
    assert set(eleg.index).isdisjoint(prot.index)


def test_auditoria_barra_vazamento(df_flag):
    with pytest.raises(ips.ProtecaoIPTUSocialError):
        ips.auditar_saida(df_flag)


def test_derivacao_sem_flag():
    df = pd.DataFrame({
        "idade": [70, 30, 30, 70, 30],
        "aposentado": [False, True, False, False, False],
        "pensionista": [False, False, True, False, False],
        "pcd": [False, False, False, False, True],
        "renda_mensal": [1500, 1500, 1500, 20000, 1500],
    })
    assert ips.eh_protegido(df).tolist() == [True, True, True, False, True]


CARTEIRA = os.path.join(os.path.dirname(__file__), "..", "data", "carteira_contribuintes.csv")


@pytest.mark.skipif(not os.path.exists(CARTEIRA), reason="carteira não está no repositório")
def test_carteira_real_sem_protegidos_no_ranking():
    df = pd.read_csv(CARTEIRA)
    if "score_inadimplencia" not in df.columns:
        df["score_inadimplencia"] = 0.5
    r = ips.ranking_cobranca(df)
    eleg, prot = ips.separar_protegidos(df)
    assert len(r) == len(eleg)
    assert not ips.eh_protegido(r).any()


META = os.path.join(os.path.dirname(__file__), "..", "models", "metadados_modelos.json")


@pytest.mark.skipif(not os.path.exists(META), reason="metadados não estão no repositório")
def test_grupo_protegido_fora_dos_preditores():
    import json
    meta = json.load(open(META, encoding="utf-8"))
    assert "iptu_social" not in meta["atributos_entrada"]
    assert meta["exclusao_obrigatoria"] == "iptu_social == 0"
