import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Dashboard RU - Campus Cedro",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
        .main {
            background-color: #f8f9fa;
        }

        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e6e6e6;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .metric-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #222;
        }

        .metric-subtitle {
            font-size: 12px;
            color: #777;
        }

        .section-title {
            font-size: 22px;
            font-weight: 700;
            margin-top: 25px;
            margin-bottom: 10px;
        }

        .info-box {
            padding: 15px;
            border-radius: 10px;
            background-color: #eef5ff;
            border-left: 5px solid #3b82f6;
        }

        .warning-box {
            padding: 15px;
            border-radius: 10px;
            background-color: #fff8e1;
            border-left: 5px solid #f59e0b;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CARREGAMENTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "rucedro.csv"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Datas
    df["menu_date"] = pd.to_datetime(
        df["menu_date"],
        errors="coerce"
    )

    df["reservation_date"] = pd.to_datetime(
        df["reservation_date"],
        errors="coerce"
    )

    # Hora da reserva
    df["reservation_time"] = pd.to_datetime(
        df["reservation_time"],
        format="%H:%M:%S",
        errors="coerce"
    ).dt.time

    # Padronização de texto
    text_columns = [
        "menu_description",
        "meal_description",
        "campus_description",
        "was_present",
        "canceled_by_student",
        "reservation_status",
        "absence_justification",
        "is_republic_student",
        "course_description",
        "course_initials",
        "shift_description"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("string")

    # Indicadores auxiliares
    df["present"] = (
        df["was_present"]
        .fillna("")
        .str.lower()
        .eq("sim")
    )

    df["absent"] = (
        df["was_present"]
        .fillna("")
        .str.lower()
        .eq("não")
    )

    df["cancelled"] = (
        df["canceled_by_student"]
        .fillna("")
        .str.lower()
        .eq("sim")
    )

    df["justified_absence"] = df["absence_justification"].notna()

    # Dia da semana
    dias = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }

    df["day_of_week"] = df["menu_date"].dt.dayofweek.map(dias)

    df["day_number"] = df["menu_date"].dt.dayofweek

    # Mês
    df["month"] = df["menu_date"].dt.month
    df["month_name"] = df["menu_date"].dt.strftime("%B")

    return df


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"Arquivo não encontrado: {DATA_PATH}\n\n"
        "Coloque o arquivo rucedro.csv na mesma pasta do app.py."
    )
    st.stop()


# ============================================================
# TÍTULO
# ============================================================

st.title("🍽️ Dashboard de Gestão do Restaurante Universitário")
st.markdown(
    "### IFCE Campus Cedro — Análise de reservas, presença e demanda"
)

st.divider()


# ============================================================
# SIDEBAR / FILTROS
# ============================================================

st.sidebar.header("🔎 Filtros")

min_date = df["menu_date"].min()
max_date = df["menu_date"].max()

date_range = st.sidebar.date_input(
    "Período",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = df[
        (df["menu_date"].dt.date >= start_date) &
        (df["menu_date"].dt.date <= end_date)
    ].copy()
else:
    filtered_df = df.copy()


# Filtro refeição
meal_options = sorted(
    filtered_df["meal_description"]
    .dropna()
    .unique()
    .tolist()
)

selected_meals = st.sidebar.multiselect(
    "Tipo de refeição",
    meal_options,
    default=meal_options
)

if selected_meals:
    filtered_df = filtered_df[
        filtered_df["meal_description"].isin(selected_meals)
    ]


# Filtro cardápio
menu_options = sorted(
    filtered_df["menu_description"]
    .dropna()
    .unique()
    .tolist()
)

selected_menus = st.sidebar.multiselect(
    "Cardápio",
    menu_options,
    default=menu_options
)

if selected_menus:
    filtered_df = filtered_df[
        filtered_df["menu_description"].isin(selected_menus)
    ]


# República
republic_options = sorted(
    filtered_df["is_republic_student"]
    .dropna()
    .unique()
    .tolist()
)

selected_republic = st.sidebar.multiselect(
    "Aluno de república",
    republic_options,
    default=republic_options
)

if selected_republic:
    filtered_df = filtered_df[
        filtered_df["is_republic_student"].isin(selected_republic)
    ]


# ============================================================
# KPIs
# ============================================================

total = len(filtered_df)

presentes = int(filtered_df["present"].sum())
faltas = int(filtered_df["absent"].sum())
cancelados = int(filtered_df["cancelled"].sum())
justificativas = int(filtered_df["justified_absence"].sum())

taxa_comparecimento = (
    presentes / total * 100
    if total > 0 else 0
)

taxa_ausencia = (
    faltas / total * 100
    if total > 0 else 0
)

taxa_cancelamento = (
    cancelados / total * 100
    if total > 0 else 0
)


# ============================================================
# CABEÇALHO DOS KPIs
# ============================================================

st.markdown(
    '<div class="section-title">📊 Indicadores principais</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(
        "Agendamentos",
        f"{total:,}".replace(",", ".")
    )

with k2:
    st.metric(
        "Compareceram",
        f"{presentes:,}".replace(",", "."),
        f"{taxa_comparecimento:.1f}%"
    )

with k3:
    st.metric(
        "Faltaram",
        f"{faltas:,}".replace(",", "."),
        f"{taxa_ausencia:.1f}%"
    )

with k4:
    st.metric(
        "Cancelamentos",
        f"{cancelados:,}".replace(",", "."),
        f"{taxa_cancelamento:.1f}%"
    )

with k5:
    st.metric(
        "Justificativas",
        f"{justificativas:,}".replace(",", ".")
    )


# ============================================================
# TAXAS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Taxas de utilização</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=taxa_comparecimento,
            title={"text": "Taxa de comparecimento"},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "threshold": {
                    "line": {"width": 4},
                    "value": taxa_comparecimento
                }
            }
        )
    )

    fig.update_layout(height=300)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=taxa_ausencia,
            title={"text": "Taxa de ausência"},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "threshold": {
                    "line": {"width": 4},
                    "value": taxa_ausencia
                }
            }
        )
    )

    fig.update_layout(height=300)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col3:

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=taxa_cancelamento,
            title={"text": "Taxa de cancelamento"},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "threshold": {
                    "line": {"width": 4},
                    "value": taxa_cancelamento
                }
            }
        )
    )

    fig.update_layout(height=300)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# PRESENÇA X AUSÊNCIA
# ============================================================

st.markdown(
    '<div class="section-title">👥 Presença e ausência</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)


with col1:

    presence_df = pd.DataFrame({
        "Situação": [
            "Compareceram",
            "Faltaram"
        ],
        "Quantidade": [
            presentes,
            faltas
        ]
    })

    fig = px.pie(
        presence_df,
        names="Situação",
        values="Quantidade",
        hole=0.55,
        title="Distribuição das reservas"
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    status_df = (
        filtered_df["reservation_status"]
        .value_counts()
        .reset_index()
    )

    status_df.columns = [
        "Status",
        "Quantidade"
    ]

    fig = px.bar(
        status_df,
        x="Status",
        y="Quantidade",
        text="Quantidade",
        title="Reservas por status",
        labels={
            "Quantidade": "Quantidade de reservas",
            "Status": "Status"
        }
    )

    fig.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# EVOLUÇÃO TEMPORAL
# ============================================================

st.markdown(
    '<div class="section-title">📅 Evolução da demanda</div>',
    unsafe_allow_html=True
)

daily = (
    filtered_df
    .groupby("menu_date")
    .agg(
        reservas=("scheduling_id", "count"),
        presentes=("present", "sum"),
        faltas=("absent", "sum")
    )
    .reset_index()
)

daily["taxa_ausencia"] = (
    daily["faltas"] /
    daily["reservas"] *
    100
).fillna(0)

fig = px.line(
    daily,
    x="menu_date",
    y=["reservas", "presentes", "faltas"],
    markers=True,
    title="Evolução diária de reservas, presença e faltas",
    labels={
        "menu_date": "Data",
        "value": "Quantidade",
        "variable": "Indicador"
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# DIA DA SEMANA
# ============================================================

st.markdown(
    '<div class="section-title">🗓️ Comportamento por dia da semana</div>',
    unsafe_allow_html=True
)

weekday_df = (
    filtered_df
    .groupby(["day_number", "day_of_week"])
    .agg(
        reservas=("scheduling_id", "count"),
        faltas=("absent", "sum"),
        presentes=("present", "sum")
    )
    .reset_index()
    .sort_values("day_number")
)

weekday_df["taxa_ausencia"] = (
    weekday_df["faltas"] /
    weekday_df["reservas"] *
    100
).round(2)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        weekday_df,
        x="day_of_week",
        y="reservas",
        text="reservas",
        title="Demanda por dia da semana",
        labels={
            "day_of_week": "Dia",
            "reservas": "Reservas"
        }
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.bar(
        weekday_df,
        x="day_of_week",
        y="taxa_ausencia",
        text="taxa_ausencia",
        title="Taxa de ausência por dia",
        labels={
            "day_of_week": "Dia",
            "taxa_ausencia": "Ausência (%)"
        }
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REFEIÇÕES
# ============================================================

st.markdown(
    '<div class="section-title">🍛 Análise por tipo de refeição</div>',
    unsafe_allow_html=True
)

meal_df = (
    filtered_df
    .groupby("meal_description")
    .agg(
        reservas=("scheduling_id", "count"),
        presentes=("present", "sum"),
        faltas=("absent", "sum")
    )
    .reset_index()
)

meal_df["taxa_ausencia"] = (
    meal_df["faltas"] /
    meal_df["reservas"] *
    100
).round(2)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        meal_df.sort_values("reservas"),
        x="reservas",
        y="meal_description",
        orientation="h",
        text="reservas",
        title="Quantidade de reservas por refeição",
        labels={
            "meal_description": "Refeição",
            "reservas": "Reservas"
        }
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.bar(
        meal_df.sort_values("taxa_ausencia"),
        x="meal_description",
        y="taxa_ausencia",
        text="taxa_ausencia",
        title="Ausência por tipo de refeição",
        labels={
            "meal_description": "Refeição",
            "taxa_ausencia": "Ausência (%)"
        }
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# HEATMAP
# ============================================================

st.markdown(
    '<div class="section-title">🔥 Mapa de calor das reservas</div>',
    unsafe_allow_html=True
)

heatmap_df = (
    filtered_df
    .groupby([
        "day_of_week",
        "meal_description"
    ])
    .size()
    .reset_index(name="reservas")
)

heatmap_pivot = heatmap_df.pivot(
    index="day_of_week",
    columns="meal_description",
    values="reservas"
).fillna(0)

order_days = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo"
]

heatmap_pivot = heatmap_pivot.reindex(
    [d for d in order_days if d in heatmap_pivot.index]
)

fig = px.imshow(
    heatmap_pivot,
    text_auto=True,
    aspect="auto",
    title="Quantidade de reservas por dia e refeição",
    labels={
        "x": "Refeição",
        "y": "Dia da semana",
        "color": "Reservas"
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# CARDÁPIOS
# ============================================================

st.markdown(
    '<div class="section-title">🍽️ Desempenho dos cardápios</div>',
    unsafe_allow_html=True
)

menu_df = (
    filtered_df
    .groupby("menu_description")
    .agg(
        reservas=("scheduling_id", "count"),
        presentes=("present", "sum"),
        faltas=("absent", "sum")
    )
    .reset_index()
)

menu_df["taxa_ausencia"] = (
    menu_df["faltas"] /
    menu_df["reservas"] *
    100
).round(2)

menu_df = menu_df.sort_values(
    "taxa_ausencia",
    ascending=False
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        menu_df,
        x="taxa_ausencia",
        y="menu_description",
        orientation="h",
        text="taxa_ausencia",
        title="Cardápios com maior taxa de ausência",
        labels={
            "menu_description": "Cardápio",
            "taxa_ausencia": "Ausência (%)"
        }
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.treemap(
        menu_df,
        path=["menu_description"],
        values="reservas",
        color="taxa_ausencia",
        title="Participação dos cardápios nas reservas",
        labels={
            "reservas": "Reservas",
            "taxa_ausencia": "Taxa de ausência"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REPÚBLICA
# ============================================================

st.markdown(
    '<div class="section-title">🏠 Alunos de república</div>',
    unsafe_allow_html=True
)

republic_df = (
    filtered_df
    .groupby("is_republic_student")
    .agg(
        reservas=("scheduling_id", "count"),
        presentes=("present", "sum"),
        faltas=("absent", "sum")
    )
    .reset_index()
)

republic_df["taxa_ausencia"] = (
    republic_df["faltas"] /
    republic_df["reservas"] *
    100
).round(2)

col1, col2 = st.columns(2)

with col1:

    fig = px.pie(
        republic_df,
        names="is_republic_student",
        values="reservas",
        hole=0.5,
        title="Reservas: república × não república"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.bar(
        republic_df,
        x="is_republic_student",
        y="taxa_ausencia",
        text="taxa_ausencia",
        title="Taxa de ausência por situação de moradia",
        labels={
            "is_republic_student": "Aluno de república",
            "taxa_ausencia": "Ausência (%)"
        }
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# HORÁRIOS DAS RESERVAS
# ============================================================

st.markdown(
    '<div class="section-title">⏰ Distribuição dos horários</div>',
    unsafe_allow_html=True
)

time_df = filtered_df.copy()

time_df["hora"] = pd.to_datetime(
    time_df["reservation_time"].astype(str),
    errors="coerce"
).dt.hour

time_df = time_df.dropna(subset=["hora"])

if not time_df.empty:

    hourly = (
        time_df
        .groupby("hora")
        .agg(
            reservas=("scheduling_id", "count"),
            faltas=("absent", "sum")
        )
        .reset_index()
    )

    hourly["taxa_ausencia"] = (
        hourly["faltas"] /
        hourly["reservas"] *
        100
    )

    fig = px.area(
        hourly,
        x="hora",
        y="reservas",
        markers=True,
        title="Demanda ao longo do horário",
        labels={
            "hora": "Hora da reserva",
            "reservas": "Reservas"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:
    st.info("Não existem horários válidos suficientes para análise.")


# ============================================================
# MOTIVOS DAS FALTAS
# ============================================================

st.markdown(
    '<div class="section-title">❌ Motivos das ausências</div>',
    unsafe_allow_html=True
)

justification_df = (
    filtered_df[
        filtered_df["absence_justification"].notna()
    ]
    ["absence_justification"]
    .value_counts()
    .reset_index()
)

justification_df.columns = [
    "Motivo",
    "Quantidade"
]

if not justification_df.empty:

    col1, col2 = st.columns(2)

    with col1:

        fig = px.bar(
            justification_df.sort_values("Quantidade"),
            x="Quantidade",
            y="Motivo",
            orientation="h",
            text="Quantidade",
            title="Justificativas por motivo"
        )

        fig.update_traces(
            textposition="outside"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.pie(
            justification_df,
            names="Motivo",
            values="Quantidade",
            hole=0.45,
            title="Distribuição dos motivos de ausência"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

else:

    st.info(
        "Não existem justificativas de ausência no período selecionado."
    )


# ============================================================
# ANÁLISE DE CAPACIDADE / OCUPAÇÃO
# ============================================================

st.markdown(
    '<div class="section-title">🏢 Ocupação do RU</div>',
    unsafe_allow_html=True
)

st.warning(
    "O arquivo não possui a capacidade máxima do Restaurante Universitário. "
    "Por isso, não é possível calcular a taxa de ocupação real (%). "
    "O gráfico abaixo representa apenas a demanda de reservas."
)

occupation_df = (
    filtered_df
    .groupby("menu_date")
    .size()
    .reset_index(name="reservas")
)

fig = px.bar(
    occupation_df,
    x="menu_date",
    y="reservas",
    text="reservas",
    title="Demanda diária do RU",
    labels={
        "menu_date": "Data",
        "reservas": "Número de reservas"
    }
)

fig.update_traces(
    textposition="outside"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# INDICADORES NÃO DISPONÍVEIS
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Indicadores que precisam de novos dados</div>',
    unsafe_allow_html=True
)

missing_data = pd.DataFrame({
    "Indicador": [
        "Utilização por curso",
        "Utilização por turno",
        "Desperdício em kg",
        "Kg desperdiçados/refeição",
        "Relação satisfação × desperdício",
        "Tempo entre agendamento e refeição",
        "Ocupação percentual do RU",
        "Sazonalidade mensal"
    ],
    "Situação": [
        "Dados de curso estão vazios",
        "Dados de turno estão vazios",
        "Coluna de desperdício não existe",
        "Coluna de desperdício não existe",
        "Não existe coluna de satisfação",
        "Não existe data/hora do momento do agendamento",
        "Não existe capacidade máxima do RU",
        "A planilha possui somente 3 dias"
    ]
})

st.dataframe(
    missing_data,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# RESUMO AUTOMÁTICO
# ============================================================

st.markdown(
    '<div class="section-title">🧠 Principais descobertas do período</div>',
    unsafe_allow_html=True
)

if not weekday_df.empty:

    worst_day = weekday_df.loc[
        weekday_df["taxa_ausencia"].idxmax()
    ]

    best_day = weekday_df.loc[
        weekday_df["reservas"].idxmax()
    ]

else:
    worst_day = None
    best_day = None


if not meal_df.empty:

    worst_meal = meal_df.loc[
        meal_df["taxa_ausencia"].idxmax()
    ]

    most_used_meal = meal_df.loc[
        meal_df["reservas"].idxmax()
    ]

else:
    worst_meal = None
    most_used_meal = None


col1, col2, col3 = st.columns(3)

with col1:

    if best_day is not None:
        st.info(
            f"📅 **Maior demanda:** "
            f"{best_day['day_of_week']} "
            f"com {int(best_day['reservas'])} reservas."
        )


with col2:

    if worst_day is not None:
        st.warning(
            f"⚠️ **Maior taxa de ausência:** "
            f"{worst_day['day_of_week']} "
            f"({worst_day['taxa_ausencia']:.1f}%)."
        )


with col3:

    if worst_meal is not None:
        st.warning(
            f"🍽️ **Refeição com maior ausência:** "
            f"{worst_meal['meal_description']} "
            f"({worst_meal['taxa_ausencia']:.1f}%)."
        )


# ============================================================
# TABELA DETALHADA
# ============================================================

st.markdown(
    '<div class="section-title">📋 Dados detalhados</div>',
    unsafe_allow_html=True
)

show_columns = [
    "menu_date",
    "menu_description",
    "meal_description",
    "reservation_time",
    "was_present",
    "reservation_status",
    "absence_justification",
    "is_republic_student",
    "student_name"
]

show_columns = [
    col for col in show_columns
    if col in filtered_df.columns
]

st.dataframe(
    filtered_df[show_columns],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD
# ============================================================

csv = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Baixar dados filtrados",
    data=csv,
    file_name="rucedro_filtrado.csv",
    mime="text/csv"
)


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Dashboard desenvolvido com Streamlit, Pandas e Plotly. "
    "Os indicadores são calculados exclusivamente a partir dos dados "
    "disponíveis na planilha."
)