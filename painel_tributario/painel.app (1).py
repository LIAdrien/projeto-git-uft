"""
Painel Streamlit — Sprint 4 (E4) | Projeto Integrador BIINAR, Eixo II 2026/2
Inteligência Tributária — dívida ativa de IPTU de Palmas-TO

Rodar:  streamlit run <nome deste arquivo>

Arquivos esperados (na pasta do app, em ./models, ../models, ./data ou ../data):
    modelo_inadimplencia.joblib · modelo_recuperabilidade.joblib
    metadados_modelos.json · carteira_contribuintes.csv

AVISO: a camada individual da carteira é SINTÉTICA. O painel mostra que o
pipeline funciona, não que o modelo funcionaria no mundo real.
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
AQUI = Path(__file__).resolve().parent
PASTAS_BUSCA = [AQUI, AQUI / "models", AQUI.parent / "models", AQUI / "data", AQUI.parent / "data"]

LIM_ALTA = 0.66
LIM_BAIXA = 0.33
FAIXAS = ["Alta", "Média", "Baixa"]
ORDEM_RENDA = ["baixa", "media", "alta"]
COL_ID = "id_contribuinte"
SITUACOES = ["Em dia", "Com dívida", "Isento (IPTU Social)"]

# Moldura: azul e verde vivos. Gráficos: verde, amarelo e laranja vivos.
AZUL = "#0077C8"
VERDE_ESCURO = "#00A06A"
VERDE = "#1DB954"
AMARELO = "#FFC800"
LARANJA = "#FF8C00"
LARANJA_ESCURO = "#F03E1E"
TEXTO = "#10242B"

CSS = """
<style>
.topo{background:linear-gradient(90deg,#0066CC 0%,#00B26F 100%);color:#fff;
      padding:1.1rem 1.5rem;border-radius:16px;margin-bottom:1rem;
      border-bottom:6px solid #FFD400}
.topo h1{color:#fff;font-size:1.65rem;margin:0;padding:0}
.topo p{margin:.2rem 0 .7rem;color:#fff;opacity:.95}
.selo{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.6);
      border-radius:999px;padding:.15rem .8rem;font-size:.8rem;color:#fff}

/* Cartões: fundo azul-verde com texto claro, legíveis em tema claro ou escuro */
[data-testid="stMetric"]{background:linear-gradient(135deg,#0066CC 0%,#00A878 100%);
      border-left:8px solid #FFD400;border-radius:12px;padding:.8rem 1.1rem;
      box-shadow:0 2px 8px rgba(0,102,204,.35)}
[data-testid="stMetric"] *{color:#FFFFFF !important}
[data-testid="stMetricLabel"] *{color:#D8F6EA !important;font-weight:600}
[data-testid="stMetricValue"] *{color:#FFFFFF !important;font-weight:800}
[data-testid="stMetricDelta"] *{color:#FFE680 !important}

[data-testid="stSidebar"]{border-right:5px solid #0077C8}
button[data-baseweb="tab"]{font-weight:700}
button[data-baseweb="tab"][aria-selected="true"]{color:#00B26F !important}
div[data-baseweb="tab-highlight"]{background-color:#00B26F !important;height:3px}
div[data-baseweb="slider"] [role="slider"]{background-color:#00B26F !important}
.rodape{margin-top:2rem;padding-top:.8rem;border-top:1px solid rgba(128,128,128,.25);
        font-size:.82rem;opacity:.8;text-align:center}
</style>
"""


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def localizar(nome: str) -> Path:
    for pasta in PASTAS_BUSCA:
        caminho = pasta / nome
        if caminho.exists():
            return caminho
    buscadas = ", ".join(str(p) for p in PASTAS_BUSCA)
    raise FileNotFoundError(f"Arquivo '{nome}' não encontrado. Procurei em: {buscadas}")


def inteiro(n: float) -> str:
    return f"{int(n):,}".replace(",", ".")


def brl(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def brl_curto(valor: float) -> str:
    """R$ 1,2 mi / R$ 350 mil — leitura rápida nos cartões."""
    if abs(valor) >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f} mi".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"R$ {valor / 1_000:.0f} mil"
    return brl(valor)


def pct(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def classificar_faixa(prob: float) -> str:
    if pd.isna(prob):
        return "-"
    if prob > LIM_ALTA:
        return "Alta"
    if prob >= LIM_BAIXA:
        return "Média"
    return "Baixa"


def mostrar_tabela(df: pd.DataFrame, **kwargs) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


def mostrar_grafico(grafico) -> None:
    try:
        st.altair_chart(grafico, width="stretch")
    except TypeError:
        st.altair_chart(grafico, use_container_width=True)


# --------------------------------------------------------------------------- #
# Carga dos artefatos
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Carregando modelos...")
def carregar_modelos():
    with open(localizar("metadados_modelos.json"), encoding="utf-8") as f:
        meta = json.load(f)
    try:
        modelo_inad = joblib.load(localizar(meta["modelo_1_inadimplencia"]["arquivo"]))
        modelo_rec = joblib.load(localizar(meta["modelo_2_recuperabilidade"]["arquivo"]))
    except Exception as erro:
        import sklearn

        versao_treino = meta.get("versoes", {}).get("scikit_learn", "desconhecida")
        raise RuntimeError(
            f"Erro ao carregar os modelos ({type(erro).__name__}: {erro}).\n\n"
            f"• scikit-learn instalado neste ambiente: {sklearn.__version__}\n"
            f"• scikit-learn usado no treino: {versao_treino}\n\n"
            f"Fixe `scikit-learn=={versao_treino}` no requirements.txt e use Python 3.13."
        ) from erro
    return meta, modelo_inad, modelo_rec


@st.cache_data(show_spinner="Lendo a carteira...")
def carregar_carteira() -> pd.DataFrame:
    return pd.read_csv(localizar("carteira_contribuintes.csv"), sep=";", encoding="utf-8-sig")


# --------------------------------------------------------------------------- #
# Lógica (sem dependência da interface)
# --------------------------------------------------------------------------- #
def _proba_positiva(modelo, X: pd.DataFrame) -> np.ndarray:
    classes = list(modelo.classes_)
    return modelo.predict_proba(X)[:, classes.index(1)]


def pontuar(carteira: pd.DataFrame, meta: dict, modelo_inad, modelo_rec) -> pd.DataFrame:
    """Exclusão obrigatória (iptu_social == 0) + probabilidades dos dois modelos."""
    base = carteira.query(meta["exclusao_obrigatoria"]).copy()
    if base.empty:
        return base

    X = base[meta["atributos_entrada"]]

    limiar = meta["modelo_1_inadimplencia"]["limiar_operacional"]
    base["prob_inadimplencia"] = _proba_positiva(modelo_inad, X)
    base["alerta_inadimplencia"] = base["prob_inadimplencia"] >= limiar

    com_divida = base["valor_divida_consolidada"] > 0
    base["prob_recuperacao"] = np.nan
    if com_divida.any():
        base.loc[com_divida, "prob_recuperacao"] = _proba_positiva(modelo_rec, X[com_divida])

    p = base["prob_recuperacao"]
    faixa = pd.Series(
        np.select([p > LIM_ALTA, p >= LIM_BAIXA], ["Alta", "Média"], default="Baixa"),
        index=base.index,
    )
    base["faixa_recuperabilidade"] = faixa.where(com_divida)
    base["retorno_esperado"] = (base["valor_divida_consolidada"] * p).fillna(0.0)
    return base


def situacao_carteira(carteira: pd.DataFrame) -> pd.DataFrame:
    """Classifica cada registro: isento (IPTU Social), com dívida ou em dia."""
    c = carteira[["setor_urbano", "iptu_social", "valor_divida_consolidada"]].copy()
    c["situacao"] = np.select(
        [c["iptu_social"] == 1, c["valor_divida_consolidada"] > 0],
        ["Isento (IPTU Social)", "Com dívida"],
        default="Em dia",
    )
    return c


def resumo_por_setor(situacao: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Tabela agregada por setor (sem identificar pessoas)."""
    cont = pd.crosstab(situacao["setor_urbano"], situacao["situacao"]).reindex(columns=SITUACOES, fill_value=0)
    cont["Total"] = cont.sum(axis=1)
    cont["% em dia"] = cont["Em dia"] / cont["Total"].replace(0, np.nan)
    em_dia_alerta = (
        base[(base["valor_divida_consolidada"] == 0) & (base["alerta_inadimplencia"])]
        .groupby("setor_urbano")
        .size()
    )
    cont["Em dia com alerta de risco"] = em_dia_alerta.reindex(cont.index).fillna(0).astype(int)
    return cont.reset_index().sort_values("% em dia", ascending=False)


def tabela_calor(base: pd.DataFrame, metrica: str) -> pd.DataFrame:
    coluna = "prob_inadimplencia" if metrica == "predita" else "inadimplente_proximo_exercicio"
    return (
        base.groupby(["setor_urbano", "faixa_renda_setor"])
        .agg(valor=(coluna, "mean"), n=(COL_ID, "size"))
        .reset_index()
    )


def projecao(devedores: pd.DataFrame, variacao: float) -> tuple[float, float, float]:
    v = devedores["valor_divida_consolidada"]
    p = devedores["prob_recuperacao"]
    pior = (v * (p * (1 - variacao)).clip(0, 1)).sum()
    esperado = (v * p).sum()
    melhor = (v * (p * (1 + variacao)).clip(0, 1)).sum()
    return pior, esperado, melhor


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #
def simulador_caso(base: pd.DataFrame, meta: dict, modelo_inad, modelo_rec) -> None:
    """Consulta de registro sintético + simulação 'E se...' com proteção contra ausência de colunas."""
    with st.expander("Consultar contribuinte sintético ou simular cenário ('E se...')"):
        if base.empty:
            st.info("Sem registros elegíveis para simulação.")
            return

        ids_disponiveis = base[COL_ID].astype(str).tolist()
        id_escolhido = st.selectbox(
            "Selecionar ID sintético de referência",
            options=ids_disponiveis,
            index=0,
            key="simulador_id",
        )
        registro = base[base[COL_ID].astype(str) == id_escolhido].iloc[0].copy()
        atributos = meta["atributos_entrada"]

        cols = st.columns(4)
        idx_col = 0

        if "valor_divida_consolidada" in atributos:
            registro["valor_divida_consolidada"] = cols[idx_col % 4].number_input(
                "Dívida consolidada (R$)",
                min_value=0.0,
                value=float(registro["valor_divida_consolidada"]),
                step=100.0,
            )
            idx_col += 1

        if "tempo_inadimplencia_dias" in atributos:
            registro["tempo_inadimplencia_dias"] = cols[idx_col % 4].number_input(
                "Tempo inadimplência (dias)",
                min_value=0,
                value=int(registro["tempo_inadimplencia_dias"]),
                step=30,
            )
            idx_col += 1

        if "qtd_parcelamentos_anteriores" in atributos:
            registro["qtd_parcelamentos_anteriores"] = cols[idx_col % 4].number_input(
                "Parcelamentos anteriores",
                min_value=0,
                max_value=20,
                value=int(registro["qtd_parcelamentos_anteriores"]),
                step=1,
            )
            idx_col += 1

        if "qtd_notificacoes" in atributos:
            registro["qtd_notificacoes"] = cols[idx_col % 4].number_input(
                "Notificações emitidas",
                min_value=0,
                max_value=30,
                value=int(registro["qtd_notificacoes"]),
                step=1,
            )

        divida_sim = float(registro.get("valor_divida_consolidada", 0.0))
        X_caso = pd.DataFrame([registro[atributos]])
        prob_inad = float(_proba_positiva(modelo_inad, X_caso)[0])
        limiar = meta["modelo_1_inadimplencia"]["limiar_operacional"]

        if divida_sim > 0:
            prob_rec = float(_proba_positiva(modelo_rec, X_caso)[0])
            faixa = classificar_faixa(prob_rec)
            ret_esp = divida_sim * prob_rec
        else:
            prob_rec = np.nan
            faixa = "Sem dívida ativa"
            ret_esp = 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Risco de inadimplência",
            pct(prob_inad),
            delta="Com alerta" if prob_inad >= limiar else "Abaixo do limiar",
            delta_color="off",
        )
        m2.metric("Chance de recuperar (12m)", pct(prob_rec) if divida_sim > 0 else "N/A")
        m3.metric("Faixa", faixa)
        m4.metric("Retorno esperado", brl(ret_esp))


def aba_ranking(devedores: pd.DataFrame, base: pd.DataFrame, meta: dict, modelo_inad, modelo_rec) -> None:
    st.subheader("Quem cobrar primeiro")
    st.caption("Retorno esperado = valor da dívida × chance de recuperar em 12 meses.")
    if devedores.empty:
        st.info("Nenhum devedor com os filtros escolhidos.")
        simulador_caso(base, meta, modelo_inad, modelo_rec)
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Devedores na fila", inteiro(len(devedores)))
    c2.metric("Dívida total", brl_curto(devedores["valor_divida_consolidada"].sum()))
    c3.metric("Retorno esperado", brl_curto(devedores["retorno_esperado"].sum()))

    col_a, col_b, col_c = st.columns([2, 1, 1])
    criterio = col_a.radio(
        "Ordenar por",
        ["Retorno esperado", "Chance de recuperação", "Valor da dívida"],
        horizontal=True,
    )
    mapa = {
        "Retorno esperado": "retorno_esperado",
        "Chance de recuperação": "prob_recuperacao",
        "Valor da dívida": "valor_divida_consolidada",
    }
    busca_id = col_b.text_input("Buscar ID sintético", placeholder="Ex.: CONT_0012")
    n_max = len(devedores)
    if n_max > 1:
        top_n = col_c.slider("Linhas", 1, min(200, n_max), min(20, n_max))
    else:
        top_n = 1

    filtrados = devedores
    if busca_id.strip():
        filtrados = filtrados[
            filtrados[COL_ID].astype(str).str.contains(busca_id.strip(), case=False, na=False)
        ]

    if filtrados.empty:
        st.warning(f"Nenhum devedor encontrado para a busca '{busca_id}'.")
    else:
        ranking = filtrados.sort_values(mapa[criterio], ascending=False).head(top_n).copy()
        ranking.insert(0, "posicao", np.arange(1, len(ranking) + 1))
        ranking = ranking[
            [
                "posicao",
                COL_ID,
                "setor_urbano",
                "valor_divida_consolidada",
                "prob_recuperacao",
                "faixa_recuperabilidade",
                "retorno_esperado",
            ]
        ]
        mostrar_tabela(
            ranking,
            column_config={
                "posicao": st.column_config.NumberColumn("#", width="small"),
                COL_ID: st.column_config.TextColumn("ID sintético"),
                "setor_urbano": st.column_config.TextColumn("Setor"),
                "valor_divida_consolidada": st.column_config.NumberColumn("Dívida (R$)", format="%.2f"),
                "prob_recuperacao": st.column_config.ProgressColumn(
                    "Chance de recuperar", min_value=0.0, max_value=1.0, format="percent"
                ),
                "faixa_recuperabilidade": st.column_config.TextColumn("Faixa"),
                "retorno_esperado": st.column_config.NumberColumn("Retorno esperado (R$)", format="%.2f"),
            },
        )
        st.download_button(
            "Baixar esta lista (CSV)",
            data=ranking.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig"),
            file_name="ranking_recuperabilidade.csv",
            mime="text/csv",
        )

    simulador_caso(base, meta, modelo_inad, modelo_rec)


def aba_mapa_calor(base: pd.DataFrame) -> None:
    st.subheader("Onde está o risco")
    metrica = st.radio(
        "Mostrar",
        ["Risco previsto pelo modelo", "Inadimplência observada"],
        horizontal=True,
    )
    chave = "predita" if metrica.startswith("Risco") else "observada"
    dados = tabela_calor(base, chave)

    ordem_setor = (
        dados.groupby("setor_urbano")["valor"].mean().sort_values(ascending=False).index.tolist()
    )
    lo, hi = float(dados["valor"].min()), float(dados["valor"].max())
    passo = max((hi - lo) / 3, 1e-6)
    escala = alt.Scale(
        domain=[lo, lo + passo, lo + 2 * passo, lo + 3 * passo],
        range=[VERDE, AMARELO, LARANJA, LARANJA_ESCURO],
    )

    celulas = alt.Chart(dados).encode(
        x=alt.X("faixa_renda_setor:N", sort=ORDEM_RENDA, title="Faixa de renda do setor"),
        y=alt.Y("setor_urbano:N", sort=ordem_setor, title=None),
    )
    calor = celulas.mark_rect(stroke="white", strokeWidth=2).encode(
        color=alt.Color("valor:Q", title="Risco", scale=escala, legend=alt.Legend(format=".0%")),
        tooltip=[
            alt.Tooltip("setor_urbano:N", title="Setor"),
            alt.Tooltip("faixa_renda_setor:N", title="Faixa de renda"),
            alt.Tooltip("valor:Q", title="Risco", format=".1%"),
            alt.Tooltip("n:Q", title="Imóveis"),
        ],
    )
    texto = celulas.mark_text(fontSize=13, color=TEXTO).encode(text=alt.Text("valor:Q", format=".0%"))
    mostrar_grafico((calor + texto).properties(height=330))

    st.caption("Verde = menor risco · laranja = maior risco. Dados agregados, ninguém é identificado.")
    with st.expander("Como ler este mapa"):
        st.markdown(
            "- Cada quadrado é um setor numa faixa de renda; o número é o risco médio.\n"
            "- A faixa de renda não entra no modelo, serve só para agrupar.\n"
            "- Uso diagnóstico: planejar campanhas, não cobrar pessoas."
        )


def aba_projecao(devedores: pd.DataFrame) -> None:
    st.subheader("Quanto dá para arrecadar")
    if devedores.empty:
        st.info("Nenhum devedor com os filtros escolhidos.")
        return

    n_max = len(devedores)
    capacidade = st.slider(
        "Quantos casos a equipe consegue trabalhar?",
        min_value=1 if n_max < 100 else 100,
        max_value=n_max,
        value=min(1000, n_max),
    )
    with st.expander("Ajustar a incerteza dos cenários"):
        variacao = st.slider("Variação (±)", 0, 30, 10, step=5, format="%d%%") / 100

    ordenado = devedores.sort_values("retorno_esperado", ascending=False)
    top = ordenado.head(capacidade)
    pior, esp, melhor = projecao(top, variacao)
    _, esp_total, _ = projecao(devedores, variacao)
    divida_top = float(top["valor_divida_consolidada"].sum())
    taxa_rec_media = (esp / divida_top) if divida_top > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pior caso", brl_curto(pior))
    c2.metric(
        "Esperado",
        brl_curto(esp),
        delta=f"{pct(esp / esp_total)} do total da fila" if esp_total else None,
        delta_color="off",
    )
    c3.metric("Melhor caso", brl_curto(melhor))
    c4.metric("Taxa média de recuperação", pct(taxa_rec_media))

    col_g1, col_g2 = st.columns(2)

    por_faixa = (
        devedores.groupby("faixa_recuperabilidade", observed=True)
        .agg(retorno=("retorno_esperado", "sum"), casos=(COL_ID, "size"))
        .reindex(FAIXAS)
        .fillna(0)
        .reset_index()
    )
    barras = (
        alt.Chart(por_faixa)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("faixa_recuperabilidade:N", sort=FAIXAS, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("retorno:Q", title="Retorno esperado (R$)"),
            color=alt.Color(
                "faixa_recuperabilidade:N",
                legend=None,
                scale=alt.Scale(domain=FAIXAS, range=[VERDE, AMARELO, LARANJA]),
            ),
            tooltip=[
                alt.Tooltip("faixa_recuperabilidade:N", title="Faixa"),
                alt.Tooltip("casos:Q", title="Casos", format=",.0f"),
                alt.Tooltip("retorno:Q", title="Retorno (R$)", format=",.0f"),
            ],
        )
        .properties(title="Retorno por faixa de recuperabilidade", height=300)
    )
    with col_g1:
        mostrar_grafico(barras)

    total = ordenado["retorno_esperado"].sum()
    acumulado = ordenado["retorno_esperado"].cumsum() / total if total else ordenado["retorno_esperado"] * 0
    curva = pd.DataFrame(
        {"fila": np.arange(1, len(ordenado) + 1) / len(ordenado), "retorno": acumulado.to_numpy()}
    )
    if len(curva) > 600:
        curva = curva.iloc[np.linspace(0, len(curva) - 1, 600).astype(int)]
    linha = (
        alt.Chart(curva)
        .mark_area(line={"color": LARANJA_ESCURO}, color=LARANJA, opacity=0.6)
        .encode(
            x=alt.X("fila:Q", title="% da fila trabalhada", axis=alt.Axis(format="%")),
            y=alt.Y("retorno:Q", title="% do retorno esperado", axis=alt.Axis(format="%")),
            tooltip=[
                alt.Tooltip("fila:Q", title="Fila", format=".1%"),
                alt.Tooltip("retorno:Q", title="Retorno", format=".1%"),
            ],
        )
        .properties(title="Quanto da arrecadação a fila concentra", height=300)
    )
    with col_g2:
        mostrar_grafico(linha)


def aba_carteira(situacao: pd.DataFrame, base: pd.DataFrame) -> None:
    st.subheader("Situação da carteira")
    st.caption("Quem está em dia, quem deve e quem é isento. Só números agregados.")

    contagem = situacao.groupby(["setor_urbano", "situacao"]).size().reset_index(name="n")
    ordem_setor = (
        situacao.assign(em_dia=situacao["situacao"] == "Em dia")
        .groupby("setor_urbano")["em_dia"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    barras = (
        alt.Chart(contagem)
        .mark_bar()
        .encode(
            y=alt.Y("setor_urbano:N", sort=ordem_setor, title=None),
            x=alt.X("n:Q", stack="normalize", title="Participação no setor", axis=alt.Axis(format="%")),
            color=alt.Color(
                "situacao:N",
                title=None,
                scale=alt.Scale(domain=SITUACOES, range=[VERDE, LARANJA, AZUL]),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("setor_urbano:N", title="Setor"),
                alt.Tooltip("situacao:N", title="Situação"),
                alt.Tooltip("n:Q", title="Imóveis", format=",.0f"),
            ],
        )
        .properties(height=340)
    )
    mostrar_grafico(barras)

    resumo = resumo_por_setor(situacao, base)
    tabela_exibicao = resumo[
        ["setor_urbano", "Total", "Em dia", "Com dívida", "Isento (IPTU Social)", "% em dia", "Em dia com alerta de risco"]
    ]
    mostrar_tabela(
        tabela_exibicao,
        column_config={
            "setor_urbano": st.column_config.TextColumn("Setor"),
            "% em dia": st.column_config.ProgressColumn("% em dia", min_value=0.0, max_value=1.0, format="percent"),
            "Em dia com alerta de risco": st.column_config.NumberColumn(
                "Em dia, com alerta", help="Sem dívida hoje, mas com risco acima do limiar do Modelo 1."
            ),
        },
    )
    st.caption("“Em dia, com alerta” são candidatos a ações educativas, não à cobrança.")
    st.download_button(
        "Baixar relatório gerencial por setor (CSV)",
        data=tabela_exibicao.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig"),
        file_name="relatorio_carteira_por_setor.csv",
        mime="text/csv",
    )


def aba_modelos_subgrupos(base: pd.DataFrame, meta: dict) -> None:
    """Desempenho dos modelos (Sprint 4) e monitoramento por subgrupo (base Sprint 5)."""
    st.subheader("Avaliação dos modelos e monitoramento por subgrupo")
    st.caption(
        "Métricas registradas no conjunto de teste e distribuição dos scores por faixa de renda "
        "e setor urbano (apoio à análise de equidade / fairness)."
    )

    m1 = meta["modelo_1_inadimplencia"]["metricas_teste"]
    m2 = meta["modelo_2_recuperabilidade"]["metricas_teste"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Modelo 1 — Risco de Inadimplência** (`{meta['modelo_1_inadimplencia']['algoritmo']}`)")
        df_m1 = pd.DataFrame(
            [
                {"Métrica": "ROC-AUC", "Valor": pct(m1["roc_auc"])},
                {"Métrica": "Recall (Sensibilidade)", "Valor": pct(m1["recall"])},
                {"Métrica": "Precisão", "Valor": pct(m1["precisao"])},
                {"Métrica": "F1-Score", "Valor": pct(m1["f1"])},
                {"Métrica": "Acurácia", "Valor": pct(m1["acuracia"])},
            ]
        )
        mostrar_tabela(df_m1)

    with col2:
        st.markdown(f"**Modelo 2 — Recuperabilidade 12m** (`{meta['modelo_2_recuperabilidade']['algoritmo']}`)")
        df_m2 = pd.DataFrame(
            [
                {"Métrica": "ROC-AUC", "Valor": pct(m2["roc_auc"])},
                {"Métrica": "Recall (Sensibilidade)", "Valor": pct(m2["recall"])},
                {"Métrica": "Precisão", "Valor": pct(m2["precisao"])},
                {"Métrica": "F1-Score", "Valor": pct(m2["f1"])},
                {"Métrica": "Acurácia", "Valor": pct(m2["acuracia"])},
            ]
        )
        mostrar_tabela(df_m2)

    if "faixa_renda_setor" in base.columns and not base.empty:
        st.markdown("### Distribuição dos scores por faixa de renda do setor")
        sub_renda = (
            base.groupby("faixa_renda_setor", observed=True)
            .agg(
                imoveis=(COL_ID, "size"),
                risco_medio=("prob_inadimplencia", "mean"),
                taxa_alerta=("alerta_inadimplencia", "mean"),
                recup_media=("prob_recuperacao", "mean"),
            )
            .reindex(ORDEM_RENDA)
            .dropna(how="all")
            .reset_index()
        )
        mostrar_tabela(
            sub_renda,
            column_config={
                "faixa_renda_setor": st.column_config.TextColumn("Faixa de renda do setor"),
                "imoveis": st.column_config.NumberColumn("Imóveis avaliados", format="%d"),
                "risco_medio": st.column_config.ProgressColumn("Risco médio previsto", min_value=0.0, max_value=1.0, format="percent"),
                "taxa_alerta": st.column_config.ProgressColumn("% com alerta de risco", min_value=0.0, max_value=1.0, format="percent"),
                "recup_media": st.column_config.ProgressColumn("Recuperabilidade média", min_value=0.0, max_value=1.0, format="percent"),
            },
        )

        df_long = sub_renda.melt(
            id_vars="faixa_renda_setor",
            value_vars=["risco_medio", "recup_media"],
            var_name="indicador",
            value_name="taxa",
        )
        df_long["indicador"] = df_long["indicador"].map(
            {"risco_medio": "Risco médio previsto", "recup_media": "Recuperabilidade média"}
        )
        grafico_sub = (
            alt.Chart(df_long)
            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
            .encode(
                x=alt.X("faixa_renda_setor:N", sort=ORDEM_RENDA, title="Faixa de renda do setor", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("taxa:Q", title="Média do grupo", axis=alt.Axis(format="%")),
                xOffset="indicador:N",
                color=alt.Color(
                    "indicador:N",
                    title=None,
                    scale=alt.Scale(range=[LARANJA, VERDE]),
                    legend=alt.Legend(orient="bottom"),
                ),
                tooltip=[
                    alt.Tooltip("faixa_renda_setor:N", title="Faixa de renda"),
                    alt.Tooltip("indicador:N", title="Indicador"),
                    alt.Tooltip("taxa:Q", title="Valor", format=".1%"),
                ],
            )
            .properties(title="Comparativo entre subgrupos socioeconômicos (base sintética)", height=280)
        )
        mostrar_grafico(grafico_sub)


def barra_lateral(meta: dict) -> None:
    import sklearn

    with st.sidebar:
        with st.expander("Sobre os dados e modelos"):
            m1 = meta["modelo_1_inadimplencia"]["metricas_teste"]
            m2 = meta["modelo_2_recuperabilidade"]["metricas_teste"]
            st.markdown(
                "**Dados sintéticos**: a camada individual foi simulada a partir de agregados "
                "oficiais. Nenhum dado pessoal é exibido.\n\n"
                f"**Risco de inadimplência**: ROC-AUC {m1['roc_auc']:.2f}, recall {m1['recall']:.2f}.\n\n"
                f"**Recuperabilidade**: ROC-AUC {m2['roc_auc']:.2f}, recall {m2['recall']:.2f}.\n\n"
                f"Faixas: alta acima de {LIM_ALTA:.2f}, média entre {LIM_BAIXA:.2f} e {LIM_ALTA:.2f}, "
                f"baixa abaixo de {LIM_BAIXA:.2f}."
            )
        with st.expander("Quem fica fora da cobrança (IPTU Social)"):
            st.markdown(
                "Imóveis marcados como IPTU Social não entram em nenhum cálculo de cobrança.\n\n"
                "**Automática:** pessoa física, um único imóvel no município, uso só residencial "
                "e imposto abaixo de 50 Ufip.\n\n"
                "**Por pedido:** idoso acima de 65 anos, aposentado, pensionista ou pessoa com "
                "deficiência incapacitada para o trabalho, com renda de até 2 salários mínimos, "
                "um único imóvel residencial e imposto abaixo de 150 Ufip."
            )
        versao_treino = meta["versoes"]["scikit_learn"]
        if sklearn.__version__ != versao_treino:
            st.warning(
                f"scikit-learn {sklearn.__version__} instalado; os modelos usam {versao_treino}. "
                "Instale a mesma versão."
            )


def main() -> None:
    st.set_page_config(page_title="Inteligência Tributária — Palmas", page_icon="📊", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="topo"><h1>Inteligência Tributária · Palmas</h1>'
        "<p>Dívida ativa de IPTU: quem cobrar primeiro e quanto esperar arrecadar</p>"
        '<span class="selo">Dados sintéticos · demonstração</span></div>',
        unsafe_allow_html=True,
    )

    try:
        meta, modelo_inad, modelo_rec = carregar_modelos()
        carteira = carregar_carteira()
    except (FileNotFoundError, RuntimeError) as erro:
        st.error(str(erro))
        st.stop()

    barra_lateral(meta)

    base = pontuar(carteira, meta, modelo_inad, modelo_rec)
    situacao = situacao_carteira(carteira)
    devedores_todos = base[base["valor_divida_consolidada"] > 0]
    n_em_dia = int((situacao["situacao"] == "Em dia").sum())
    n_isentos = int((situacao["situacao"] == "Isento (IPTU Social)").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Imóveis na carteira", inteiro(len(carteira)))
    k2.metric("Em dia", inteiro(n_em_dia))
    k3.metric("Com dívida", inteiro(len(devedores_todos)))
    k4.metric("Isentos (IPTU Social)", inteiro(n_isentos))

    with st.sidebar:
        st.header("Filtros")
        setores = sorted(devedores_todos["setor_urbano"].unique())
        sel_setores = st.multiselect("Setor", setores, default=setores)
        sel_faixas = st.multiselect("Faixa de recuperabilidade", FAIXAS, default=FAIXAS)

        if "faixa_renda_setor" in devedores_todos.columns:
            rendas_presentes = [
                r for r in ORDEM_RENDA if r in devedores_todos["faixa_renda_setor"].dropna().unique()
            ]
            sel_rendas = st.multiselect("Faixa de renda do setor", rendas_presentes, default=rendas_presentes)
        else:
            sel_rendas = None

        max_divida = float(devedores_todos["valor_divida_consolidada"].max()) if not devedores_todos.empty else 0.0
        divida_min = st.number_input(
            "Dívida mínima (R$)",
            min_value=0.0,
            max_value=max(max_divida, 0.0),
            value=0.0,
            step=100.0,
        )
        st.caption("Valem para o ranking e a projeção.")

    condicao = (
        devedores_todos["setor_urbano"].isin(sel_setores)
        & devedores_todos["faixa_recuperabilidade"].isin(sel_faixas)
        & (devedores_todos["valor_divida_consolidada"] >= divida_min)
    )
    if sel_rendas is not None:
        condicao = condicao & devedores_todos["faixa_renda_setor"].isin(sel_rendas)

    devedores = devedores_todos[condicao]

    aba1, aba2, aba3, aba4, aba5 = st.tabs(
        [
            "Quem cobrar primeiro",
            "Onde está o risco",
            "Quanto arrecadar",
            "Situação da carteira",
            "Modelos & Subgrupos",
        ]
    )
    with aba1:
        aba_ranking(devedores, base, meta, modelo_inad, modelo_rec)
    with aba2:
        aba_mapa_calor(base)
    with aba3:
        aba_projecao(devedores)
    with aba4:
        aba_carteira(situacao, base)
    with aba5:
        aba_modelos_subgrupos(base, meta)

    st.markdown(
        '<div class="rodape">Projeto Integrador BIINAR · Eixo II (2026/2) — '
        "Camada individual sintética para fins acadêmicos · Imóveis IPTU Social excluídos por regra de negócio · "
        "Ferramenta de apoio à decisão humana.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
