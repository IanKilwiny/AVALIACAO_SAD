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
    initial_sidebar_state="expanded",
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
    unsafe_allow_html=True,
)

# ============================================================
# CARREGAMENTO E PREPARAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "rucedro3.csv"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Datas
    date_columns = [
        "reservation_date",
        "menu_date",
        "reservation_insert_date",
        "reservation_created_at",
        "reservation_updated_at",
        "student_valid_date",
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Horários
    for col in ["reservation_time", "meal_time_start", "meal_time_end"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col].astype("string"),
                format="%H:%M:%S",
                errors="coerce",
            ).dt.time

    # Texto
    text_columns = [
        "student_name",
        "course_description",
        "course_initials",
        "shift_description",
        "student_campus_description",
        "scheduling_campus_description",
        "is_republic_student",
        "republic_description",
        "reservation_status",
        "was_present",
        "canceled_by_student",
        "absence_justification",
        "student_justification",
        "menu_description",
        "meal_description",
        "review_comment",
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("string")

    # Indicadores
    df["present"] = df["reservation_status"].eq("Presente")
    df["absent"] = df["reservation_status"].eq("Ausente")
    df["cancelled"] = df["reservation_status"].eq("Cancelada")

    df["justified_absence"] = (
        df["absence_justification"].notna()
        | df["student_justification"].notna()
    )

    # Calendário
    dias = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    df["day_number"] = df["reservation_date"].dt.dayofweek
    df["day_of_week"] = df["day_number"].map(dias)

    ordem_dias = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]

    df["day_of_week"] = pd.Categorical(
        df["day_of_week"],
        categories=ordem_dias,
        ordered=True,
    )

    df["year_month"] = df["reservation_date"].dt.to_period("M").astype("string")
    df["month"] = df["reservation_date"].dt.month

    # Hora da reserva
    df["reservation_hour"] = pd.to_datetime(
        df["reservation_time"].astype("string"),
        errors="coerce",
    ).dt.hour

    # Garantir campos numéricos
    for col in ["advance_hours", "review_score", "total_food_waste_kg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"Arquivo não encontrado: {DATA_PATH}\n\n"
        "Coloque o arquivo rucedro3.csv na mesma pasta do app.py."
    )
    st.stop()

# ============================================================
# PADRONIZAÇÃO DO TIPO DE REFEIÇÃO
# ============================================================

def normalizar_refeicao(valor):
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip().lower()

    if "manhã" in texto or "manha" in texto:
        return "Lanche da manhã"

    if "almoço" in texto or "almoco" in texto:
        return "Almoço"

    if "tarde" in texto:
        return "Lanche da tarde"

    if "noite" in texto:
        return "Lanche da noite"

    return str(valor).strip()


if "meal_description" in df.columns:
    df["meal_type"] = df["meal_description"].apply(normalizar_refeicao)

# ============================================================
# TÍTULO
# ============================================================

st.title("🍽️ Dashboard de Gestão do Restaurante Universitário")
st.markdown(
    "### IFCE Campus Cedro — Reservas, presença, demanda, perfil dos alunos, desperdício e satisfação"
)

st.divider()

# ============================================================
# SIDEBAR / FILTROS
# IMPORTANTE: NÃO EXISTE FILTRO POR COMIDA/REFEIÇÃO/CARDÁPIO
# ============================================================

st.sidebar.header("🔎 Filtros Globais")

min_date = df["reservation_date"].min()
max_date = df["reservation_date"].max()

date_range = st.sidebar.date_input(
    "Período",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

filtered_df = df.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = filtered_df[
        (filtered_df["reservation_date"].dt.date >= start_date)
        & (filtered_df["reservation_date"].dt.date <= end_date)
    ]

# Campus
campus_options = ["Todos"] + sorted(
    filtered_df["student_campus_description"].dropna().unique().tolist()
)
selected_campus = st.sidebar.selectbox("Campus do aluno", campus_options)

if selected_campus != "Todos":
    filtered_df = filtered_df[
        filtered_df["student_campus_description"] == selected_campus
    ]

# Curso
course_options = ["Todos"] + sorted(
    filtered_df["course_description"].dropna().unique().tolist()
)
selected_course = st.sidebar.selectbox("Curso", course_options)

if selected_course != "Todos":
    filtered_df = filtered_df[
        filtered_df["course_description"] == selected_course
    ]

# Tipo de refeição
meal_options = ["Todos"] + sorted(
    filtered_df["meal_type"].dropna().unique().tolist()
)
selected_meal = st.sidebar.selectbox(
    "Tipo de refeição",
    meal_options,
)

if selected_meal != "Todos":
    filtered_df = filtered_df[
        filtered_df["meal_type"] == selected_meal
    ]

# República
republic_options = ["Todos"] + sorted(
    filtered_df["is_republic_student"].dropna().unique().tolist()
)
selected_republic = st.sidebar.selectbox(
    "Aluno de república",
    republic_options,
)

if selected_republic != "Todos":
    filtered_df = filtered_df[
        filtered_df["is_republic_student"] == selected_republic
    ]

# ============================================================
# BASE DE AGENDAMENTOS
# ============================================================

df_sched = filtered_df[filtered_df["scheduling_id"].notna()].copy()

# ============================================================
# KPIs
# ============================================================

# Totalidade de alunos existente na base.
# Esse valor não é afetado pelos filtros de período, curso,
# campus, refeição ou república.
total_alunos_base = df["student_id"].nunique()

# Alunos que efetivamente aparecem nas reservas após os filtros.
alunos_que_reservaram = filtered_df.loc[
    filtered_df["scheduling_id"].notna(),
    "student_id",
].nunique()

total_alunos = filtered_df["student_id"].nunique()
total_agendamentos = df_sched["scheduling_id"].nunique()

media_reservas_aluno = (
    total_agendamentos / alunos_que_reservaram
    if alunos_que_reservaram > 0
    else 0
)

presentes = int(df_sched["present"].sum())
faltas = int(df_sched["absent"].sum())
cancelados = int(df_sched["cancelled"].sum())
justificativas = int(df_sched["justified_absence"].sum())

taxa_comparecimento = (
    presentes / total_agendamentos * 100
    if total_agendamentos
    else 0
)

taxa_ausencia = (
    faltas / total_agendamentos * 100
    if total_agendamentos
    else 0
)

taxa_cancelamento = (
    cancelados / total_agendamentos * 100
    if total_agendamentos
    else 0
)

# advance_hours pode estar inconsistente no dataset.
advance_valid = df_sched.loc[
    df_sched["advance_hours"].between(0, 24 * 30, inclusive="both"),
    "advance_hours",
].dropna()

tempo_medio_antecedencia = advance_valid.mean() if not advance_valid.empty else None

# ============================================================
# CABEÇALHO DOS KPIs
# ============================================================

st.markdown(
    '<div class="section-title">📊 Indicadores principais</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)

with k1:
    st.metric(
        "Total de alunos",
        f"{total_alunos_base:,}".replace(",", "."),
    )

with k2:
    st.metric(
        "Alunos que reservaram",
        f"{alunos_que_reservaram:,}".replace(",", "."),
    )

with k3:
    st.metric(
        "Agendamentos",
        f"{total_agendamentos:,}".replace(",", "."),
    )

with k4:
    st.metric(
        "Compareceram",
        f"{presentes:,}".replace(",", "."),
        f"{taxa_comparecimento:.1f}%",
    )

with k5:
    st.metric(
        "Faltaram",
        f"{faltas:,}".replace(",", "."),
        f"{taxa_ausencia:.1f}%",
        delta_color="inverse",
    )

with k6:
    st.metric(
        "Cancelamentos",
        f"{cancelados:,}".replace(",", "."),
        f"{taxa_cancelamento:.1f}%",
        delta_color="inverse",
    )

with k7:
    st.metric(
        "Média reservas/aluno",
        f"{media_reservas_aluno:.2f}",
    )

# ============================================================
# TAXAS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Taxas de utilização</div>',
    unsafe_allow_html=True,
)

g1, g2, g3 = st.columns(3)

def gauge(title, value):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "threshold": {
                    "line": {"width": 4},
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20))
    return fig

with g1:
    st.plotly_chart(
        gauge("Taxa de comparecimento", taxa_comparecimento),
        use_container_width=True,
    )

with g2:
    st.plotly_chart(
        gauge("Taxa de ausência", taxa_ausencia),
        use_container_width=True,
    )

with g3:
    st.plotly_chart(
        gauge("Taxa de cancelamento", taxa_cancelamento),
        use_container_width=True,
    )

# ============================================================
# ABAS PRINCIPAIS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "👥 Perfil e utilização",
        "📅 Demanda e operação",
        "🍛 Cardápio, desperdício e satisfação",
        "📋 Dados detalhados",
    ]
)

# ============================================================
# ABA 1 — PERFIL
# ============================================================

with tab1:

    st.markdown(
        '<div class="section-title">👥 Perfil dos usuários do RU</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        course_df = (
            df_sched[df_sched["present"]]
            .groupby("course_description", dropna=False)
            .agg(
                refeicoes=("scheduling_id", "count"),
                alunos=("student_id", "nunique"),
            )
            .reset_index()
            .sort_values("refeicoes", ascending=False)
            .head(10)
        )

        fig = px.bar(
            course_df.sort_values("refeicoes"),
            x="refeicoes",
            y="course_description",
            orientation="h",
            text="refeicoes",
            title="Top 10 cursos por refeições consumidas",
            labels={
                "refeicoes": "Refeições consumidas",
                "course_description": "Curso",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        rep_df = (
            df_filtered
            if False
            else filtered_df
        )

        rep_usage = (
            rep_df.groupby("is_republic_student", dropna=False)
            .agg(
                alunos=("student_id", "nunique"),
                presentes=("present", "sum"),
                agendamentos=("scheduling_id", "count"),
            )
            .reset_index()
        )

        rep_usage["refeicoes_por_aluno"] = (
            rep_usage["presentes"] / rep_usage["alunos"].replace(0, pd.NA)
        )

        fig = px.bar(
            rep_usage,
            x="is_republic_student",
            y="refeicoes_por_aluno",
            text="refeicoes_por_aluno",
            title="Média de refeições consumidas por aluno",
            labels={
                "is_republic_student": "Aluno de república?",
                "refeicoes_por_aluno": "Refeições por aluno",
            },
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="section-title">🎓 Ausência por curso</div>',
        unsafe_allow_html=True,
    )

    course_absence = (
        df_sched.groupby("course_description", dropna=False)
        .agg(
            agendamentos=("scheduling_id", "count"),
            faltas=("absent", "sum"),
            presentes=("present", "sum"),
        )
        .reset_index()
    )

    course_absence["taxa_ausencia"] = (
        course_absence["faltas"]
        / course_absence["agendamentos"].replace(0, pd.NA)
        * 100
    )

    course_absence = course_absence.sort_values(
        "taxa_ausencia",
        ascending=False,
    )

    fig = px.bar(
        course_absence,
        x="taxa_ausencia",
        y="course_description",
        orientation="h",
        text="taxa_ausencia",
        title="Taxa de ausência por curso",
        labels={
            "taxa_ausencia": "Ausência (%)",
            "course_description": "Curso",
        },
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="section-title">🏠 Perfil de república</div>',
        unsafe_allow_html=True,
    )

    republic_df = (
        filtered_df.groupby("is_republic_student", dropna=False)
        .agg(
            alunos=("student_id", "nunique"),
            reservas=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
        )
        .reset_index()
    )

    republic_df["taxa_ausencia"] = (
        republic_df["faltas"]
        / republic_df["reservas"].replace(0, pd.NA)
        * 100
    )

    r1, r2 = st.columns(2)

    with r1:
        fig = px.pie(
            republic_df,
            names="is_republic_student",
            values="reservas",
            hole=0.5,
            title="Distribuição das reservas por situação de moradia",
        )
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        fig = px.bar(
            republic_df,
            x="is_republic_student",
            y="taxa_ausencia",
            text="taxa_ausencia",
            title="Taxa de ausência: república × não república",
            labels={
                "is_republic_student": "Aluno de república?",
                "taxa_ausencia": "Ausência (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# ABA 2 — DEMANDA E OPERAÇÃO
# ============================================================

with tab2:

    st.markdown(
        '<div class="section-title">📅 Evolução da demanda</div>',
        unsafe_allow_html=True,
    )

    daily = (
        df_sched.groupby("reservation_date")
        .agg(
            agendamentos=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
            cancelados=("cancelled", "sum"),
        )
        .reset_index()
        .sort_values("reservation_date")
    )

    fig = px.line(
        daily,
        x="reservation_date",
        y=["agendamentos", "presentes", "faltas", "cancelados"],
        markers=True,
        title="Evolução diária de reservas, presença, faltas e cancelamentos",
        labels={
            "reservation_date": "Data",
            "value": "Quantidade",
            "variable": "Indicador",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="section-title">📆 Sazonalidade mensal</div>',
        unsafe_allow_html=True,
    )

    monthly = (
        df_sched.groupby("year_month")
        .agg(
            agendamentos=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
            cancelados=("cancelled", "sum"),
        )
        .reset_index()
    )

    fig = px.line(
        monthly,
        x="year_month",
        y=["agendamentos", "presentes", "faltas"],
        markers=True,
        title="Evolução mensal dos agendamentos",
        labels={
            "year_month": "Mês",
            "value": "Quantidade",
            "variable": "Indicador",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    d1, d2 = st.columns(2)

    with d1:
        weekday_df = (
            df_sched.groupby(
                ["day_number", "day_of_week"],
                observed=False,
            )
            .agg(
                agendamentos=("scheduling_id", "count"),
                faltas=("absent", "sum"),
                presentes=("present", "sum"),
            )
            .reset_index()
            .sort_values("day_number")
        )

        weekday_df["taxa_ausencia"] = (
            weekday_df["faltas"]
            / weekday_df["agendamentos"].replace(0, pd.NA)
            * 100
        )

        fig = px.bar(
            weekday_df,
            x="day_of_week",
            y="faltas",
            text="faltas",
            title="Dia da semana com mais faltas",
            labels={
                "day_of_week": "Dia",
                "faltas": "Faltas",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with d2:
        meal_df = (
            df_sched.groupby("meal_type", dropna=False)
            .agg(
                agendamentos=("scheduling_id", "count"),
                faltas=("absent", "sum"),
                presentes=("present", "sum"),
            )
            .reset_index()
        )

        meal_df["taxa_ausencia"] = (
            meal_df["faltas"]
            / meal_df["agendamentos"].replace(0, pd.NA)
            * 100
        )

        fig = px.bar(
            meal_df,
            x="meal_type",
            y="taxa_ausencia",
            text="taxa_ausencia",
            title="Taxa de ausência por tipo de refeição",
            labels={
                "meal_type": "Tipo de refeição",
                "taxa_ausencia": "Ausência (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="section-title">⏰ Horário das reservas</div>',
        unsafe_allow_html=True,
    )

    hourly = (
        df_sched.dropna(subset=["reservation_hour"])
        .groupby("reservation_hour")
        .agg(
            reservas=("scheduling_id", "count"),
            faltas=("absent", "sum"),
            presentes=("present", "sum"),
        )
        .reset_index()
    )

    if not hourly.empty:
        hourly["taxa_ausencia"] = (
            hourly["faltas"]
            / hourly["reservas"].replace(0, pd.NA)
            * 100
        )

        fig = px.bar(
            hourly,
            x="reservation_hour",
            y="reservas",
            text="reservas",
            title="Demanda por hora da reserva",
            labels={
                "reservation_hour": "Hora",
                "reservas": "Reservas",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.line(
            hourly,
            x="reservation_hour",
            y="taxa_ausencia",
            markers=True,
            title="Taxa de ausência por hora da reserva",
            labels={
                "reservation_hour": "Hora",
                "taxa_ausencia": "Ausência (%)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap sem filtro de comida
    st.markdown(
        '<div class="section-title">🔥 Mapa de calor da demanda</div>',
        unsafe_allow_html=True,
    )

    heatmap = (
        df_sched.groupby(
            ["day_of_week", "meal_type"],
            observed=False,
        )
        .size()
        .reset_index(name="reservas")
    )

    heatmap_pivot = heatmap.pivot(
        index="day_of_week",
        columns="meal_type",
        values="reservas",
    ).fillna(0)

    heatmap_pivot = heatmap_pivot.reindex(
        [
            d
            for d in [
                "Segunda-feira",
                "Terça-feira",
                "Quarta-feira",
                "Quinta-feira",
                "Sexta-feira",
                "Sábado",
                "Domingo",
            ]
            if d in heatmap_pivot.index
        ]
    )

    if not heatmap_pivot.empty:
        fig = px.imshow(
            heatmap_pivot,
            text_auto=True,
            aspect="auto",
            title="Reservas por dia da semana e tipo de refeição",
            labels={
                "x": "Tipo de refeição",
                "y": "Dia da semana",
                "color": "Reservas",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# ABA 3 — CARDÁPIO, DESPERDÍCIO E SATISFAÇÃO
# ============================================================

with tab3:

    st.markdown(
        '<div class="section-title">🍛 Análise por tipo de refeição</div>',
        unsafe_allow_html=True,
    )

    meal_df = (
        df_sched.groupby("meal_description", dropna=False)
        .agg(
            reservas=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
        )
        .reset_index()
    )

    meal_df["taxa_ausencia"] = (
        meal_df["faltas"]
        / meal_df["reservas"].replace(0, pd.NA)
        * 100
    )

    m1, m2 = st.columns(2)

    with m1:
        fig = px.bar(
            meal_df.sort_values("reservas"),
            x="reservas",
            y="meal_description",
            orientation="h",
            text="reservas",
            title="Reservas por tipo de refeição",
            labels={
                "meal_description": "Refeição",
                "reservas": "Reservas",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with m2:
        fig = px.bar(
            meal_df.sort_values("taxa_ausencia"),
            x="meal_description",
            y="taxa_ausencia",
            text="taxa_ausencia",
            title="Ausência por tipo de refeição",
            labels={
                "meal_description": "Refeição",
                "taxa_ausencia": "Ausência (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="section-title">🥪🍛 Refeições mais reservadas</div>',
        unsafe_allow_html=True,
    )

    meal_reservations = (
        df_sched.groupby("meal_type", dropna=False)
        .agg(
            reservas=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
        )
        .reset_index()
        .dropna(subset=["meal_type"])
        .sort_values("reservas", ascending=False)
    )

    if not meal_reservations.empty:

        r1, r2 = st.columns(2)

        with r1:
            fig = px.bar(
                meal_reservations.sort_values("reservas"),
                x="reservas",
                y="meal_type",
                orientation="h",
                text="reservas",
                title="Quantidade de reservas por refeição",
                labels={
                    "meal_type": "Tipo de refeição",
                    "reservas": "Reservas",
                },
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with r2:
            fig = px.pie(
                meal_reservations,
                names="meal_type",
                values="reservas",
                hole=0.40,
                title="Participação das refeições nas reservas",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Destaques de lanche e almoço
        lanche_mask = meal_reservations["meal_type"].str.contains(
            "lanche",
            case=False,
            na=False,
        )

        lanches = meal_reservations[lanche_mask].copy()
        almoco = meal_reservations[
            meal_reservations["meal_type"].str.contains(
                "almoço|almoco",
                case=False,
                na=False,
                regex=True,
            )
        ].copy()

        d1, d2 = st.columns(2)

        with d1:
            if not lanches.empty:
                fig = px.bar(
                    lanches.sort_values("reservas"),
                    x="reservas",
                    y="meal_type",
                    orientation="h",
                    text="reservas",
                    title="🥪 Lanches mais reservados",
                    labels={
                        "meal_type": "Lanche",
                        "reservas": "Reservas",
                    },
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há registros de lanches no período.")

        with d2:
            if not almoco.empty:
                fig = px.bar(
                    almoco.sort_values("reservas"),
                    x="reservas",
                    y="meal_type",
                    orientation="h",
                    text="reservas",
                    title="🍛 Almoço mais reservado",
                    labels={
                        "meal_type": "Refeição",
                        "reservas": "Reservas",
                    },
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há registros de almoço no período.")

    st.markdown(
        '<div class="section-title">🍽️ Desempenho dos cardápios</div>',
        unsafe_allow_html=True,
    )

    menu_df = (
        df_sched.groupby("menu_description", dropna=False)
        .agg(
            reservas=("scheduling_id", "count"),
            presentes=("present", "sum"),
            faltas=("absent", "sum"),
        )
        .reset_index()
    )

    menu_df["taxa_ausencia"] = (
        menu_df["faltas"]
        / menu_df["reservas"].replace(0, pd.NA)
        * 100
    )

    m1, m2 = st.columns(2)

    with m1:
        top_menus = menu_df.sort_values(
            "reservas",
            ascending=False,
        ).head(10)

        fig = px.bar(
            top_menus.sort_values("reservas"),
            x="reservas",
            y="menu_description",
            orientation="h",
            text="reservas",
            title="Cardápios com maior demanda",
            labels={
                "menu_description": "Cardápio",
                "reservas": "Reservas",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with m2:
        absence_menus = menu_df[
            menu_df["reservas"] >= 2
        ].sort_values(
            "taxa_ausencia",
            ascending=False,
        ).head(10)

        fig = px.bar(
            absence_menus,
            x="taxa_ausencia",
            y="menu_description",
            orientation="h",
            text="taxa_ausencia",
            title="Cardápios com maior taxa de ausência",
            labels={
                "menu_description": "Cardápio",
                "taxa_ausencia": "Ausência (%)",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # DESPERDÍCIO
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">♻️ Desperdício de alimentos</div>',
        unsafe_allow_html=True,
    )

    waste_base = df_sched.dropna(
        subset=["total_food_waste_kg"]
    ).copy()

    if not waste_base.empty:

        waste_daily = (
            waste_base.groupby("reservation_date")
            .agg(
                desperdicio_kg=("total_food_waste_kg", "max"),
                refeicoes_servidas=("present", "sum"),
            )
            .reset_index()
        )

        waste_daily["kg_por_refeicao"] = (
            waste_daily["desperdicio_kg"]
            / waste_daily["refeicoes_servidas"].replace(0, pd.NA)
        )

        w1, w2, w3 = st.columns(3)

        with w1:
            total_waste = waste_daily["desperdicio_kg"].sum()
            st.metric(
                "Desperdício registrado",
                f"{total_waste:.2f} kg",
            )

        with w2:
            valid_waste = waste_daily["kg_por_refeicao"].dropna()
            if not valid_waste.empty:
                st.metric(
                    "Kg desperdiçados/refeição",
                    f"{valid_waste.mean():.3f} kg",
                )
            else:
                st.metric(
                    "Kg desperdiçados/refeição",
                    "N/D",
                )

        with w3:
            max_waste = waste_daily["desperdicio_kg"].max()
            st.metric(
                "Maior desperdício diário",
                f"{max_waste:.2f} kg",
            )

        fig = px.line(
            waste_daily,
            x="reservation_date",
            y="desperdicio_kg",
            markers=True,
            title="Evolução do desperdício registrado",
            labels={
                "reservation_date": "Data",
                "desperdicio_kg": "Desperdício (kg)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

        waste_menu = (
            waste_base.groupby("menu_description")
            .agg(
                desperdicio_kg=("total_food_waste_kg", "mean"),
                refeicoes=("present", "sum"),
            )
            .reset_index()
        )

        waste_menu["kg_por_refeicao"] = (
            waste_menu["desperdicio_kg"]
            / waste_menu["refeicoes"].replace(0, pd.NA)
        )

        waste_menu = waste_menu.dropna(
            subset=["kg_por_refeicao"]
        ).sort_values(
            "kg_por_refeicao",
            ascending=False,
        ).head(10)

        fig = px.bar(
            waste_menu.sort_values("kg_por_refeicao"),
            x="kg_por_refeicao",
            y="menu_description",
            orientation="h",
            text="kg_por_refeicao",
            title="Cardápios com maior desperdício por refeição",
            labels={
                "menu_description": "Cardápio",
                "kg_por_refeicao": "Kg/refeição",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.3f}",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(
            "Não existem registros de desperdício no período selecionado."
        )

    # --------------------------------------------------------
    # SATISFAÇÃO
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">⭐ Satisfação dos usuários</div>',
        unsafe_allow_html=True,
    )

    review_df = df_sched.dropna(
        subset=["review_score"]
    ).copy()

    if not review_df.empty:

        s1, s2 = st.columns(2)

        with s1:
            st.metric(
                "Avaliações registradas",
                f"{len(review_df):,}".replace(",", "."),
            )

            st.metric(
                "Nota média",
                f"{review_df['review_score'].mean():.2f}/5",
            )

        with s2:
            score_df = (
                review_df["review_score"]
                .value_counts()
                .sort_index()
                .reset_index()
            )
            score_df.columns = ["nota", "quantidade"]

            fig = px.bar(
                score_df,
                x="nota",
                y="quantidade",
                text="quantidade",
                title="Distribuição das notas",
                labels={
                    "nota": "Nota",
                    "quantidade": "Avaliações",
                },
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        satisfaction_menu = (
            review_df.groupby("menu_description")
            .agg(
                nota_media=("review_score", "mean"),
                avaliacoes=("review_score", "count"),
            )
            .reset_index()
            .sort_values("nota_media", ascending=False)
        )

        fig = px.bar(
            satisfaction_menu.head(10).sort_values("nota_media"),
            x="nota_media",
            y="menu_description",
            orientation="h",
            text="nota_media",
            title="Cardápios com melhores avaliações",
            labels={
                "menu_description": "Cardápio",
                "nota_media": "Nota média",
            },
        )
        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Relação satisfação x desperdício
        relation = (
            df_sched.groupby(
                ["reservation_date", "menu_description"],
                dropna=False,
            )
            .agg(
                nota_satisfacao=("review_score", "mean"),
                desperdicio_kg=("total_food_waste_kg", "max"),
            )
            .reset_index()
            .dropna()
        )

        if len(relation) >= 3:
            fig = px.scatter(
                relation,
                x="nota_satisfacao",
                y="desperdicio_kg",
                hover_data=["menu_description", "reservation_date"],
                trendline="ols",
                title="Relação entre satisfação e desperdício",
                labels={
                    "nota_satisfacao": "Nota média",
                    "desperdicio_kg": "Desperdício (kg)",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(
            "Não existem avaliações de satisfação no período selecionado."
        )

    # --------------------------------------------------------
    # MOTIVOS DE AUSÊNCIA
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">❌ Motivos das ausências</div>',
        unsafe_allow_html=True,
    )

    # Usa a justificativa disponível. Quando as duas colunas existem,
    # prioriza a justificativa de ausência e utiliza a justificativa do
    # estudante como complemento.
    absence_data = df_sched[df_sched["absent"]].copy()

    if not absence_data.empty:

        if (
            "absence_justification" in absence_data.columns
            and "student_justification" in absence_data.columns
        ):
            absence_data["absence_reason"] = (
                absence_data["absence_justification"]
                .fillna(absence_data["student_justification"])
            )
        elif "absence_justification" in absence_data.columns:
            absence_data["absence_reason"] = (
                absence_data["absence_justification"]
            )
        elif "student_justification" in absence_data.columns:
            absence_data["absence_reason"] = (
                absence_data["student_justification"]
            )
        else:
            absence_data["absence_reason"] = pd.NA

        absence_data["absence_reason"] = (
            absence_data["absence_reason"]
            .astype("string")
            .str.strip()
        )

        # Ausências sem justificativa entram como uma categoria própria.
        absence_data["absence_reason"] = (
            absence_data["absence_reason"]
            .fillna("Sem justificativa")
            .replace("", "Sem justificativa")
        )

        reason_df = (
            absence_data["absence_reason"]
            .value_counts()
            .reset_index()
        )
        reason_df.columns = ["Motivo", "Quantidade"]

        a1, a2 = st.columns(2)

        with a1:
            fig = px.pie(
                reason_df,
                names="Motivo",
                values="Quantidade",
                hole=0.40,
                title="Distribuição dos motivos das ausências",
            )
            st.plotly_chart(fig, use_container_width=True)

        with a2:
            fig = px.bar(
                reason_df.sort_values("Quantidade"),
                x="Quantidade",
                y="Motivo",
                orientation="h",
                text="Quantidade",
                title="Quantidade de ausências por motivo",
                labels={
                    "Motivo": "Motivo",
                    "Quantidade": "Ausências",
                },
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        # Percentuais
        reason_df["Percentual"] = (
            reason_df["Quantidade"]
            / reason_df["Quantidade"].sum()
            * 100
        )

        st.dataframe(
            reason_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "Não existem ausências no período selecionado."
        )

# ============================================================
# RESUMO EXECUTIVO
# ============================================================

st.markdown("---")
st.markdown(
    '<div class="section-title">🧠 Principais descobertas do período</div>',
    unsafe_allow_html=True,
)

ins1, ins2, ins3 = st.columns(3)

# Maior demanda por dia
daily_summary = (
    df_sched.groupby("reservation_date")
    .size()
    .reset_index(name="reservas")
)

with ins1:
    if not daily_summary.empty:
        peak = daily_summary.loc[daily_summary["reservas"].idxmax()]
        st.info(
            f"📈 **Maior demanda diária:** "
            f"{peak['reservation_date'].strftime('%d/%m/%Y')} "
            f"com **{int(peak['reservas'])} reservas**."
        )
    else:
        st.info("Sem dados suficientes para identificar o pico.")

# Maior taxa de ausência por tipo de refeição
meal_summary = (
    df_sched.groupby("meal_type")
    .agg(
        reservas=("scheduling_id", "count"),
        faltas=("absent", "sum"),
    )
    .reset_index()
)

if not meal_summary.empty:
    meal_summary["taxa"] = (
        meal_summary["faltas"]
        / meal_summary["reservas"].replace(0, pd.NA)
        * 100
    )

with ins2:
    if not meal_summary.empty:
        worst_meal = meal_summary.loc[
            meal_summary["taxa"].idxmax()
        ]
        st.warning(
            f"⚠️ **Maior taxa de ausência:** "
            f"{worst_meal['meal_type']} "
            f"({worst_meal['taxa']:.1f}%)."
        )
    else:
        st.warning(
            "Sem dados suficientes para avaliar as refeições."
        )

# Cardápio com maior ausência
menu_valid = menu_df[menu_df["reservas"] >= 2].copy()

with ins3:
    if not menu_valid.empty:
        worst_menu = menu_valid.loc[
            menu_valid["taxa_ausencia"].idxmax()
        ]
        st.warning(
            f"🍽️ **Maior ausência em cardápio:** "
            f"{worst_menu['menu_description']} "
            f"({worst_menu['taxa_ausencia']:.1f}%)."
        )
    else:
        st.info("Sem dados suficientes para avaliar os cardápios.")

# ============================================================
# QUALIDADE DOS DADOS
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Qualidade e disponibilidade dos dados</div>',
    unsafe_allow_html=True,
)

quality = pd.DataFrame(
    {
        "Indicador": [
            "Alunos únicos",
            "Agendamentos",
            "Avaliações",
            "Registros com desperdício",
            "Cursos",
            "Tipos de refeição",
        ],
        "Quantidade": [
            filtered_df["student_id"].nunique(),
            df_sched["scheduling_id"].nunique(),
            df_sched["review_score"].notna().sum(),
            df_sched["total_food_waste_kg"].notna().sum(),
            df_sched["course_description"].nunique(),
            df_sched["meal_type"].nunique(),
        ],
    }
)

st.dataframe(
    quality,
    use_container_width=True,
    hide_index=True,
)

if tempo_medio_antecedencia is None:
    st.warning(
        "A coluna advance_hours possui valores fora de uma faixa temporal "
        "válida para antecedência. Por isso, a dashboard não apresenta "
        "uma média potencialmente enganosa."
    )

# ============================================================
# DADOS DETALHADOS
# ============================================================

st.markdown(
    '<div class="section-title">📋 Dados detalhados</div>',
    unsafe_allow_html=True,
)

show_columns = [
    "reservation_date",
    "reservation_time",
    "student_name",
    "course_description",
    "shift_description",
    "is_republic_student",
    "reservation_status",
    "meal_type",

    "absence_justification",
    "student_justification",
    "review_score",
    "total_food_waste_kg",
]

show_columns = [
    col for col in show_columns
    if col in filtered_df.columns
]

st.dataframe(
    filtered_df[show_columns],
    use_container_width=True,
    hide_index=True,
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
    mime="text/csv",
)

# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Dashboard desenvolvida com Streamlit, Pandas e Plotly. "
    "Os indicadores são calculados exclusivamente a partir dos dados "
    "disponíveis no arquivo rucedro3.csv."
)