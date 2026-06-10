import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

st.set_page_config(page_title="고객등급별 만족도 분석", layout="wide")

# ── 데이터 로드 ──────────────────────────────────────────────
@st.cache_data
def load_data():
    customers = pd.read_csv("customers.csv", encoding="utf-8-sig")
    records = pd.read_csv("service_records.csv", encoding="utf-8-sig")
    df = records.merge(
        customers[["고객ID", "고객등급", "누적구매액"]], on="고객ID", how="left"
    )
    score_map = {"매우만족": 5, "만족": 4, "보통": 3, "불만족": 2, "매우불만족": 1}
    df["만족도점수"] = df["만족도"].map(score_map)
    df["응대일시"] = pd.to_datetime(df["응대일시"])
    df["년월"] = df["응대일시"].dt.to_period("M").astype(str)
    return df

df = load_data()

GRADE_ORDER = ["VIP", "Gold", "Silver", "Bronze"]
SCORE_COLORS = {
    "매우만족": "#1a6bc1",
    "만족":   "#5aa8e8",
    "보통":   "#a8c8e8",
    "불만족": "#e88a5a",
    "매우불만족": "#c0392b",
}

# ── 사이드바 필터 ─────────────────────────────────────────────
with st.sidebar:
    st.title("필터")

    date_min = df["응대일시"].dt.date.min()
    date_max = df["응대일시"].dt.date.max()
    date_range = st.date_input("응대 기간", value=(date_min, date_max), min_value=date_min, max_value=date_max)

    sel_grades = st.multiselect("고객등급", GRADE_ORDER, default=GRADE_ORDER)
    sel_channels = st.multiselect("응대채널", sorted(df["응대채널"].unique()), default=sorted(df["응대채널"].unique()))

# 필터 적용
if len(date_range) == 2:
    start_date, end_date = date_range
    fdf = df[
        (df["응대일시"].dt.date >= start_date) &
        (df["응대일시"].dt.date <= end_date) &
        (df["고객등급"].isin(sel_grades)) &
        (df["응대채널"].isin(sel_channels))
    ]
else:
    fdf = df[df["고객등급"].isin(sel_grades) & df["응대채널"].isin(sel_channels)]

# ── 헤더 ─────────────────────────────────────────────────────
st.title("고객등급별 만족도 분석 대시보드")
st.caption(f"조회 데이터: {len(fdf):,}건")

# ── 섹션 1: KPI 카드 ─────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

total = len(fdf)
avg_score = fdf["만족도점수"].mean()
resolve_rate = (fdf["상태"] == "해결완료").sum() / total * 100 if total else 0
avg_time = fdf["응대시간(분)"].mean()

c1.metric("전체 응대 건수", f"{total:,}건")
c2.metric("평균 만족도", f"{avg_score:.2f} / 5.00")
c3.metric("해결완료율", f"{resolve_rate:.1f}%")
c4.metric("평균 응대시간", f"{avg_time:.1f}분")

st.divider()

# ── 섹션 2: 고객등급별 만족도 분포 (Stacked Bar) ──────────────
st.subheader("고객등급별 만족도 분포")

score_order = ["매우만족", "만족", "보통", "불만족", "매우불만족"]
grade_score = (
    fdf.groupby(["고객등급", "만족도"])
    .size()
    .reset_index(name="건수")
)
grade_score["고객등급"] = pd.Categorical(grade_score["고객등급"], categories=GRADE_ORDER, ordered=True)
grade_score["만족도"] = pd.Categorical(grade_score["만족도"], categories=score_order, ordered=True)
grade_score = grade_score.sort_values(["고객등급", "만족도"])

fig_bar = px.bar(
    grade_score,
    x="고객등급", y="건수", color="만족도",
    color_discrete_map=SCORE_COLORS,
    category_orders={"고객등급": GRADE_ORDER, "만족도": score_order},
    text="건수",
    height=420,
)
fig_bar.update_traces(textposition="inside", textfont_size=12)
fig_bar.update_layout(legend_title_text="만족도", xaxis_title="고객등급", yaxis_title="응대 건수")
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── 섹션 3: 트렌드 & Heatmap ─────────────────────────────────
st.subheader("월별 만족도 추이 & 채널별 교차 분석")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**월별 평균 만족도 추이 (등급별)**")
    trend = (
        fdf.groupby(["년월", "고객등급"])["만족도점수"]
        .mean()
        .reset_index(name="평균만족도점수")
    )
    trend["고객등급"] = pd.Categorical(trend["고객등급"], categories=GRADE_ORDER, ordered=True)
    grade_colors = {"VIP": "#6a0dad", "Gold": "#e6a817", "Silver": "#7f8c8d", "Bronze": "#a0522d"}
    fig_line = px.line(
        trend.sort_values(["년월", "고객등급"]),
        x="년월", y="평균만족도점수", color="고객등급",
        color_discrete_map=grade_colors,
        markers=True, height=380,
    )
    fig_line.update_layout(yaxis=dict(range=[1, 5]), xaxis_title="년월", yaxis_title="평균 만족도 점수")
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.markdown("**응대채널 × 고객등급 평균 만족도 (Heatmap)**")
    heat_data = (
        fdf.groupby(["고객등급", "응대채널"])["만족도점수"]
        .mean()
        .unstack(fill_value=0)
    )
    heat_data = heat_data.reindex([g for g in GRADE_ORDER if g in heat_data.index])
    fig_heat = go.Figure(
        go.Heatmap(
            z=heat_data.values,
            x=heat_data.columns.tolist(),
            y=heat_data.index.tolist(),
            colorscale="RdBu",
            zmin=1, zmax=5,
            text=[[f"{v:.2f}" for v in row] for row in heat_data.values],
            texttemplate="%{text}",
            colorbar=dict(title="평균 점수"),
        )
    )
    fig_heat.update_layout(height=380, xaxis_title="응대채널", yaxis_title="고객등급")
    st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ── 섹션 4: 문의유형별 평균 만족도 ────────────────────────────
st.subheader("문의유형별 평균 만족도")

inquiry = (
    fdf.groupby("문의유형")["만족도점수"]
    .mean()
    .reset_index(name="평균만족도점수")
    .sort_values("평균만족도점수", ascending=True)
)
fig_inquiry = px.bar(
    inquiry,
    x="평균만족도점수", y="문의유형",
    orientation="h",
    color="평균만족도점수",
    color_continuous_scale="RdBu",
    range_color=[1, 5],
    text=inquiry["평균만족도점수"].map(lambda v: f"{v:.2f}"),
    height=380,
)
fig_inquiry.update_traces(textposition="outside")
fig_inquiry.update_layout(coloraxis_showscale=False, xaxis=dict(range=[0, 5.5]), xaxis_title="평균 만족도 점수")
st.plotly_chart(fig_inquiry, use_container_width=True)

st.divider()

# ── 섹션 5: 고객등급별 집계 테이블 ────────────────────────────
st.subheader("고객등급별 상세 통계")

summary = (
    fdf.groupby("고객등급")
    .agg(
        응대건수=("응대ID", "count"),
        평균만족도점수=("만족도점수", "mean"),
        해결완료율=("상태", lambda x: (x == "해결완료").sum() / len(x) * 100),
        평균응대시간=("응대시간(분)", "mean"),
    )
    .reindex([g for g in GRADE_ORDER if g in fdf["고객등급"].unique()])
    .reset_index()
)
summary["평균만족도점수"] = summary["평균만족도점수"].map(lambda v: f"{v:.2f}")
summary["해결완료율"] = summary["해결완료율"].map(lambda v: f"{v:.1f}%")
summary["평균응대시간"] = summary["평균응대시간"].map(lambda v: f"{v:.1f}분")
summary["응대건수"] = summary["응대건수"].map(lambda v: f"{v:,}건")

st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()

# ── 섹션 6: AI 대화 ───────────────────────────────────────────
st.subheader("AI 데이터 분석 대화")
st.caption("현재 필터링된 데이터를 기반으로 질문하세요.")

def build_context(dataframe):
    total = len(dataframe)
    avg = dataframe["만족도점수"].mean()
    resolve = (dataframe["상태"] == "해결완료").sum() / total * 100 if total else 0
    avg_time = dataframe["응대시간(분)"].mean()

    grade_stats = (
        dataframe.groupby("고객등급")
        .agg(건수=("응대ID", "count"), 평균만족도=("만족도점수", "mean"))
        .reindex([g for g in GRADE_ORDER if g in dataframe["고객등급"].unique()])
        .to_string()
    )
    channel_stats = (
        dataframe.groupby("응대채널")["만족도점수"].mean().to_string()
    )
    inquiry_stats = (
        dataframe.groupby("문의유형")["만족도점수"].mean().to_string()
    )

    return f"""당신은 고객 서비스 데이터 분석 전문가입니다. 아래 데이터를 기반으로 한국어로 답변하세요.

[현재 데이터 요약]
- 전체 응대 건수: {total:,}건
- 평균 만족도: {avg:.2f} / 5.00
- 해결완료율: {resolve:.1f}%
- 평균 응대시간: {avg_time:.1f}분

[고객등급별 통계]
{grade_stats}

[응대채널별 평균 만족도]
{channel_stats}

[문의유형별 평균 만족도]
{inquiry_stats}
"""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("데이터에 대해 질문하세요 (예: VIP 고객의 불만 원인은?)")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            try:
                context = build_context(fdf)
                role_map = {"user": "user", "assistant": "model"}
                history = [
                    types.Content(role=role_map[m["role"]], parts=[types.Part(text=m["content"])])
                    for m in st.session_state.chat_history[:-1]
                ]
                chat = client.chats.create(model="gemini-1.5-flash", history=history)
                response = chat.send_message(f"{context}\n\n질문: {user_input}")
                answer = response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    answer = "⚠️ API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
                else:
                    answer = f"오류가 발생했습니다: {e}"
            st.markdown(answer)

    st.session_state.chat_history.append({"role": "assistant", "content": answer})

if st.session_state.chat_history:
    if st.button("대화 초기화"):
        st.session_state.chat_history = []
        st.rerun()
