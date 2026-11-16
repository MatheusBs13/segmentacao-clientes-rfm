"""Dashboard de segmentação de clientes (RFM + clusterização).

Rodar a partir da raiz do projeto:
    streamlit run app/app.py

Precisa dos arquivos gerados pelo notebook 04, na pasta app/data/:
    rfm_segmentos.csv, segmentos_resumo.csv, receita_cliente_mes.csv
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"
CLIENTES_CSV = DATA_DIR / "rfm_segmentos.csv"
RESUMO_CSV = DATA_DIR / "segmentos_resumo.csv"
MENSAL_CSV = DATA_DIR / "receita_cliente_mes.csv"

COLUNAS_CLIENTES = {
    "Recency", "Frequency", "Monetary", "Segmento",
    "Country", "PrimeiraCompra", "UltimaCompra",
}
COLUNAS_RESUMO = {
    "segmento", "clientes", "pct_clientes", "pct_receita",
    "recencia_mediana", "frequencia_mediana", "valor_mediano", "valor_por_cliente",
    "z_Recency", "z_Frequency", "z_Monetary",
    "porque_existe", "distintivo", "explicacao_dados",
    "acao_recomendada", "indicador",
}
COLUNAS_MENSAL = {"CustomerID", "Mes", "receita", "notas"}

PAIS_DOMINANTE = "United Kingdom"

st.set_page_config(page_title="Segmentação de Clientes", page_icon="🛍️", layout="wide")


@st.cache_data
def carregar():
    clientes = pd.read_csv(CLIENTES_CSV, index_col="CustomerID")
    resumo = pd.read_csv(RESUMO_CSV)
    mensal = pd.read_csv(MENSAL_CSV)
    return clientes, resumo, mensal


def parar_com_erro(mensagem):
    st.error(mensagem)
    st.stop()


# ---------------------------------------------------------------- Carga e validação
if not all(p.exists() for p in (CLIENTES_CSV, RESUMO_CSV, MENSAL_CSV)):
    parar_com_erro(
        "Arquivos não encontrados em `app/data/`. Rode os notebooks 01 a 04 antes de abrir "
        "o dashboard (o notebook 04 gera os três arquivos)."
    )

clientes, resumo, mensal = carregar()

for nome, df, obrigatorias in [
    ("rfm_segmentos.csv", clientes.reset_index(), COLUNAS_CLIENTES),
    ("segmentos_resumo.csv", resumo, COLUNAS_RESUMO),
    ("receita_cliente_mes.csv", mensal, COLUNAS_MENSAL),
]:
    faltando = obrigatorias - set(df.columns)
    if faltando:
        parar_com_erro(
            f"O arquivo `{nome}` está desatualizado (faltam as colunas: {', '.join(sorted(faltando))}). "
            "Rode novamente o notebook 04."
        )

clientes = clientes.assign(
    PrimeiraCompra=pd.to_datetime(clientes["PrimeiraCompra"]),
    UltimaCompra=pd.to_datetime(clientes["UltimaCompra"]),
)
mensal = mensal.assign(Mes=pd.to_datetime(mensal["Mes"]))

# Ordem dos segmentos = ordem do resumo (do maior para o menor valor) e cores fixas
ordem = resumo["segmento"].tolist()
paleta = px.colors.qualitative.Set2
cores = {seg: paleta[i % len(paleta)] for i, seg in enumerate(ordem)}

# ---------------------------------------------------------------- Sidebar
st.sidebar.header("Filtros")
segmentos_sel = st.sidebar.multiselect("Segmentos", options=ordem, default=ordem)

paises_ordenados = clientes["Country"].value_counts().index.tolist()
paises_sel = st.sidebar.multiselect(
    "Países (vazio = todos)",
    options=paises_ordenados,
    default=[],
    help="Este filtro não se aplica à aba Países, que compara os países entre si.",
)

rec_min, rec_max = int(clientes["Recency"].min()), int(clientes["Recency"].max())
if rec_min < rec_max:
    rec_faixa = st.sidebar.slider(
        "Recência (dias desde a última compra)", rec_min, rec_max, (rec_min, rec_max)
    )
else:
    rec_faixa = (rec_min, rec_max)

# "base" = segmento + recência; "filtrado" = base + país
base = clientes[
    clientes["Segmento"].isin(segmentos_sel)
    & clientes["Recency"].between(rec_faixa[0], rec_faixa[1])
]
filtrado = base[base["Country"].isin(paises_sel)] if paises_sel else base

st.sidebar.caption(f"{len(filtrado):,} de {len(clientes):,} clientes selecionados")

# ---------------------------------------------------------------- Cabeçalho
st.title("🛍️ Segmentação de Clientes")
st.caption(
    "RFM + clusterização sobre o dataset Online Retail II (UCI). "
    "Use os filtros ao lado para explorar os segmentos."
)

if filtrado.empty:
    st.warning("Nenhum cliente com esses filtros. Amplie a seleção na barra lateral.")
    st.stop()

receita_total = clientes["Monetary"].sum()
receita_sel = filtrado["Monetary"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Clientes", f"{len(filtrado):,}")
c2.metric("Receita", f"{receita_sel:,.0f}")
c3.metric("% da receita total", f"{receita_sel / receita_total:.1%}")
c4.metric("Valor médio por cliente", f"{filtrado['Monetary'].mean():,.0f}")
c5.metric("Países", f"{filtrado['Country'].nunique():,}")

aba_geral, aba_porque, aba_tempo, aba_pais, aba_clientes = st.tabs(
    ["Visão geral", "Por que os grupos existem", "Evolução no tempo", "Países", "Clientes"]
)

# ---------------------------------------------------------------- Visão geral
with aba_geral:
    esq, dir_ = st.columns(2)

    peso = (
        filtrado.groupby("Segmento")
        .agg(clientes=("Monetary", "size"), receita=("Monetary", "sum"))
        .assign(
            **{
                "% de clientes": lambda d: d["clientes"] / d["clientes"].sum() * 100,
                "% da receita": lambda d: d["receita"] / d["receita"].sum() * 100,
            }
        )
        .reset_index()
        .melt(
            id_vars="Segmento",
            value_vars=["% de clientes", "% da receita"],
            var_name="Métrica",
            value_name="%",
        )
    )
    fig_peso = px.bar(
        peso,
        x="Segmento",
        y="%",
        color="Métrica",
        barmode="group",
        title="Peso de cada segmento: clientes vs receita",
        category_orders={"Segmento": ordem},
    )
    fig_peso.update_layout(xaxis_title=None, legend_title=None)
    esq.plotly_chart(fig_peso, width="stretch")

    fig_disp = px.scatter(
        filtrado.reset_index(),
        x="Recency",
        y="Monetary",
        color="Segmento",
        color_discrete_map=cores,
        category_orders={"Segmento": ordem},
        log_y=True,
        hover_data=["CustomerID", "Frequency", "Country"],
        opacity=0.7,
        title="Recência vs valor monetário (escala log)",
        labels={"Recency": "Recência (dias)", "Monetary": "Valor monetário"},
    )
    dir_.plotly_chart(fig_disp, width="stretch")

# ---------------------------------------------------------------- Por que os grupos existem
with aba_porque:
    resumo_sel = resumo[resumo["segmento"].isin(segmentos_sel)]

    st.subheader("Como cada grupo se diferencia da média")
    heat = resumo_sel.set_index("segmento")[["z_Recency", "z_Frequency", "z_Monetary"]].copy()
    heat["z_Recency"] = -heat["z_Recency"]   # inverte: valor alto = comprou há pouco tempo
    heat.columns = ["Comprou recentemente", "Frequência", "Valor gasto"]
    limite = max(2.0, float(heat.abs().to_numpy().max()))
    fig_heat = px.imshow(
        heat,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-limite,
        zmax=limite,
        aspect="auto",
    )
    fig_heat.update_layout(coloraxis_colorbar_title="vs média")
    st.plotly_chart(fig_heat, width="stretch")
    st.caption(
        "Vermelho = acima da média da base, azul = abaixo (em desvios-padrão). "
        "A recência está invertida: valor alto significa que o cliente comprou há pouco tempo."
    )

    st.subheader("Comparação com a base inteira")
    comparacao = resumo_sel[
        ["segmento", "clientes", "recencia_mediana", "frequencia_mediana", "valor_mediano"]
    ].copy()
    linha_base = pd.DataFrame(
        [{
            "segmento": "Base inteira",
            "clientes": len(clientes),
            "recencia_mediana": clientes["Recency"].median(),
            "frequencia_mediana": clientes["Frequency"].median(),
            "valor_mediano": clientes["Monetary"].median(),
        }]
    )
    comparacao = pd.concat([comparacao, linha_base], ignore_index=True).rename(
        columns={
            "segmento": "Segmento",
            "clientes": "Clientes",
            "recencia_mediana": "Recência mediana (dias)",
            "frequencia_mediana": "Frequência mediana",
            "valor_mediano": "Valor mediano",
        }
    )
    st.dataframe(
        comparacao,
        hide_index=True,
        width="stretch",
        column_config={
            "Recência mediana (dias)": st.column_config.NumberColumn(format="%.0f"),
            "Frequência mediana": st.column_config.NumberColumn(format="%.0f"),
            "Valor mediano": st.column_config.NumberColumn(format="%.0f"),
        },
    )

    st.subheader("Por que cada grupo existe")
    st.caption(
        "Os textos descrevem padrões de comportamento e justificam a separação do grupo; "
        "não explicam as causas desse comportamento."
    )
    for i, (_, linha) in enumerate(resumo_sel.iterrows()):
        titulo = (
            f"{linha['segmento']} — {linha['pct_clientes']:.1f}% dos clientes, "
            f"{linha['pct_receita']:.1f}% da receita"
        )
        with st.expander(titulo, expanded=(i == 0)):
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(f"**Por que este grupo existe**  \n{linha['porque_existe']}")
                st.markdown(f"**O que o distingue**  \n{linha['distintivo']}")
                st.markdown(f"**Em números**  \n{linha['explicacao_dados']}")
            with col_b:
                st.markdown(f"**Ação recomendada**  \n{linha['acao_recomendada']}")
                st.markdown(f"**Indicador de sucesso**  \n{linha['indicador']}")

# ---------------------------------------------------------------- Evolução no tempo
with aba_tempo:
    st.caption(
        "O segmento de cada cliente foi definido com o período inteiro. Os gráficos abaixo mostram, "
        "portanto, como os clientes que hoje estão em cada segmento se comportaram ao longo do tempo."
    )

    ctrl1, ctrl2 = st.columns(2)
    metrica = ctrl1.radio(
        "Métrica",
        ["Receita", "Clientes ativos", "Notas fiscais"],
        horizontal=True,
        key="metrica",
    )
    modo = ctrl2.radio(
        "Mostrar como",
        ["Valor absoluto", "% do mês"],
        horizontal=True,
        key="modo_tempo",
    )

    m = mensal[mensal["CustomerID"].isin(filtrado.index)].merge(
        filtrado[["Segmento"]], left_on="CustomerID", right_index=True
    )
    mensal_seg = (
        m.groupby(["Mes", "Segmento"])
        .agg(
            receita=("receita", "sum"),
            notas=("notas", "sum"),
            clientes_ativos=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    coluna = {"Receita": "receita", "Clientes ativos": "clientes_ativos", "Notas fiscais": "notas"}[metrica]

    fig_tempo = px.bar(
        mensal_seg,
        x="Mes",
        y=coluna,
        color="Segmento",
        color_discrete_map=cores,
        category_orders={"Segmento": ordem},
        title=f"{metrica} por mês e segmento",
        labels={"Mes": "", coluna: "%" if modo == "% do mês" else metrica},
    )
    fig_tempo.update_layout(legend_title=None)
    if modo == "% do mês":
        fig_tempo.update_layout(barnorm="percent", yaxis_title="% do mês")
    st.plotly_chart(fig_tempo, width="stretch")
    st.caption("O último mês da base pode estar incompleto.")

    meses = filtrado.assign(
        MesPrimeira=filtrado["PrimeiraCompra"].dt.to_period("M").dt.to_timestamp(),
        MesUltima=filtrado["UltimaCompra"].dt.to_period("M").dt.to_timestamp(),
    )
    esq, dir_ = st.columns(2)

    entrada = meses.groupby(["MesPrimeira", "Segmento"]).size().reset_index(name="Clientes")
    fig_entrada = px.bar(
        entrada,
        x="MesPrimeira",
        y="Clientes",
        color="Segmento",
        color_discrete_map=cores,
        category_orders={"Segmento": ordem},
        title="Entrada de clientes (mês da primeira compra)",
        labels={"MesPrimeira": ""},
    )
    fig_entrada.update_layout(legend_title=None)
    esq.plotly_chart(fig_entrada, width="stretch")
    esq.caption(
        "O primeiro mês da base também reúne clientes que já existiam antes do período, "
        "então ele aparece inflado."
    )

    saida = meses.groupby(["MesUltima", "Segmento"]).size().reset_index(name="Clientes")
    fig_saida = px.bar(
        saida,
        x="MesUltima",
        y="Clientes",
        color="Segmento",
        color_discrete_map=cores,
        category_orders={"Segmento": ordem},
        title="Quando compraram pela última vez",
        labels={"MesUltima": ""},
    )
    fig_saida.update_layout(legend_title=None)
    dir_.plotly_chart(fig_saida, width="stretch")
    dir_.caption(
        "Barras altas em meses antigos mostram quando muitos clientes pararam de comprar."
    )

# ---------------------------------------------------------------- Países
with aba_pais:
    st.caption(
        "Esta aba compara os países entre si, então ignora o filtro de países da barra lateral. "
        "Os filtros de segmento e de recência continuam valendo."
    )

    p1, p2, p3 = st.columns(3)
    n_max = max(1, base["Country"].nunique())
    n_paises = p1.number_input(
        "Quantos países mostrar", min_value=1, max_value=n_max, value=min(10, n_max), key="n_paises"
    )
    excluir_dominante = p2.checkbox(
        f"Excluir {PAIS_DOMINANTE}",
        value=False,
        key="excluir_uk",
        help="Um país costuma concentrar quase toda a base. Excluí-lo deixa os demais legíveis.",
    )
    base_comp = p3.radio(
        "Composição dos grupos por",
        ["% de clientes", "% da receita"],
        horizontal=True,
        key="base_pais",
    )

    dados_p = base[base["Country"] != PAIS_DOMINANTE] if excluir_dominante else base

    if dados_p.empty:
        st.warning("Nenhum cliente com esses filtros.")
    else:
        tabela_p = (
            dados_p.groupby("Country")
            .agg(clientes=("Monetary", "size"), receita=("Monetary", "sum"))
            .assign(
                pct_clientes=lambda d: d["clientes"] / d["clientes"].sum() * 100,
                pct_receita=lambda d: d["receita"] / d["receita"].sum() * 100,
            )
            .sort_values("clientes", ascending=False)
        )
        topo = tabela_p.head(int(n_paises))
        paises_topo = topo.index.tolist()

        esq, dir_ = st.columns(2)

        fig_cli = px.bar(
            topo.reset_index().sort_values("clientes"),
            x="clientes",
            y="Country",
            orientation="h",
            title="Clientes por país",
            labels={"clientes": "Clientes", "Country": ""},
        )
        esq.plotly_chart(fig_cli, width="stretch")

        comp = (
            dados_p[dados_p["Country"].isin(paises_topo)]
            .groupby(["Country", "Segmento"])
            .agg(clientes=("Monetary", "size"), receita=("Monetary", "sum"))
            .reset_index()
        )
        n_por_pais = topo["clientes"].to_dict()
        comp["Rotulo"] = comp["Country"].map(lambda p: f"{p} (n={n_por_pais[p]:,})")
        rotulos = [f"{p} (n={n_por_pais[p]:,})" for p in paises_topo]
        coluna_comp = "clientes" if base_comp == "% de clientes" else "receita"

        fig_comp = px.bar(
            comp,
            x=coluna_comp,
            y="Rotulo",
            color="Segmento",
            orientation="h",
            color_discrete_map=cores,
            category_orders={"Segmento": ordem, "Rotulo": rotulos[::-1]},
            title=f"Composição dos grupos em cada país ({base_comp})",
            labels={coluna_comp: "%", "Rotulo": ""},
        )
        fig_comp.update_layout(legend_title=None, barnorm="percent", xaxis_title="%")
        dir_.plotly_chart(fig_comp, width="stretch")
        dir_.caption(
            "O n ao lado do país é o número de clientes. Países com poucos clientes têm "
            "percentuais instáveis: um único cliente pode mudar a barra."
        )

        st.subheader("Tabela por país")
        contagem = (
            dados_p[dados_p["Country"].isin(paises_topo)]
            .pivot_table(index="Country", columns="Segmento", values="Monetary", aggfunc="size", fill_value=0)
            .reindex(columns=[s for s in ordem if s in dados_p["Segmento"].unique()], fill_value=0)
        )
        tabela_final = (
            topo.rename(
                columns={
                    "clientes": "Clientes",
                    "receita": "Receita",
                    "pct_clientes": "% clientes",
                    "pct_receita": "% receita",
                }
            )
            .join(contagem)
            .reset_index()
            .rename(columns={"Country": "País"})
        )
        st.dataframe(
            tabela_final,
            hide_index=True,
            width="stretch",
            column_config={
                "Receita": st.column_config.NumberColumn(format="%.0f"),
                "% clientes": st.column_config.NumberColumn(format="%.1f%%"),
                "% receita": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )
        st.caption(
            "As colunas dos segmentos mostram quantos clientes de cada grupo existem no país. "
            "O país de cada cliente é aquele em que ele mais comprou."
        )

# ---------------------------------------------------------------- Clientes
with aba_clientes:
    st.subheader("Lista de clientes")
    lista = (
        filtrado.reset_index()
        .rename(
            columns={
                "Country": "País",
                "Recency": "Recência",
                "Frequency": "Frequência",
                "Monetary": "Valor",
            }
        )
        .assign(
            PrimeiraCompra=lambda d: d["PrimeiraCompra"].dt.date,
            UltimaCompra=lambda d: d["UltimaCompra"].dt.date,
        )[
            ["CustomerID", "Segmento", "País", "Recência", "Frequência", "Valor", "PrimeiraCompra", "UltimaCompra"]
        ]
        .sort_values("Valor", ascending=False)
    )
    st.dataframe(
        lista,
        hide_index=True,
        width="stretch",
        column_config={"Valor": st.column_config.NumberColumn(format="%.0f")},
    )
    st.download_button(
        "Baixar lista (CSV)",
        data=lista.to_csv(index=False).encode("utf-8"),
        file_name="clientes_filtrados.csv",
        mime="text/csv",
    )
