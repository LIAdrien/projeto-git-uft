"""E3 — Proteção formal do IPTU Social.

Grupos protegidos (idosos, aposentados, pensionistas e PcD de baixa renda)
NUNCA entram em ações preditivas de cobrança. A exclusão acontece ANTES do
ranking e é auditada DEPOIS (defesa em duas camadas).

Ajuste COLUNAS ao esquema real de data/carteira_contribuintes.csv
(rode `df.columns` para conferir).
"""
from __future__ import annotations

import pandas as pd

COLUNAS = {
    "flag": "iptu_social",        # booleano pronto na carteira (preferencial)
    "idade": "idade",
    "aposentado": "aposentado",
    "pensionista": "pensionista",
    "pcd": "pcd",
    "renda": "renda_mensal",
}
# Critério por pedido descrito no painel da equipe: idoso acima de 65 anos, aposentado, pensionista
# ou PcD incapacitada para o trabalho, renda até 2 salários mínimos. CONFERIR com a lei de Palmas.
SALARIO_MINIMO = 1621.0       # TODO: conferir o valor vigente
LIMITE_BAIXA_RENDA = 2 * SALARIO_MINIMO   # usado só se a carteira não trouxer a coluna "flag"
IDADE_IDOSO = 66              # "acima de 65 anos"


class ProtecaoIPTUSocialError(AssertionError):
    """Um contribuinte protegido apareceu numa saída de cobrança preditiva."""


def _col(df: pd.DataFrame, chave: str, padrao=False) -> pd.Series:
    nome = COLUNAS[chave]
    if nome in df.columns:
        return df[nome]
    return pd.Series(padrao, index=df.index)


def eh_protegido(df: pd.DataFrame) -> pd.Series:
    """True para quem pertence a um grupo protegido do IPTU Social."""
    if COLUNAS["flag"] in df.columns:
        return df[COLUNAS["flag"]].fillna(False).astype(bool)
    idoso = _col(df, "idade", 0).fillna(0) >= IDADE_IDOSO
    social = (
        idoso
        | _col(df, "aposentado").fillna(False).astype(bool)
        | _col(df, "pensionista").fillna(False).astype(bool)
        | _col(df, "pcd").fillna(False).astype(bool)
    )
    baixa_renda = _col(df, "renda", float("inf")).fillna(float("inf")) <= LIMITE_BAIXA_RENDA
    return (social & baixa_renda).astype(bool)


def separar_protegidos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (elegíveis à cobrança preditiva, protegidos)."""
    prot = eh_protegido(df)
    return df[~prot].copy(), df[prot].copy()


def auditar_saida(df_saida: pd.DataFrame) -> None:
    """Lança erro se houver protegido numa saída (ranking, fila, painel)."""
    n = int(eh_protegido(df_saida).sum())
    if n:
        raise ProtecaoIPTUSocialError(f"{n} contribuinte(s) protegido(s) na saída de cobrança.")


def ranking_cobranca(df: pd.DataFrame, col_score: str = "score_inadimplencia",
                     top: int | None = None) -> pd.DataFrame:
    """Ranking de cobrança já sem os grupos protegidos."""
    elegiveis, _ = separar_protegidos(df)
    ranking = elegiveis.sort_values(col_score, ascending=False)
    if top:
        ranking = ranking.head(top)
    auditar_saida(ranking)
    return ranking
