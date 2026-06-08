import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="🤖 AI 관련 기업 주식 대시보드",
    page_icon="🤖",
    layout="wide",
)

# ── 타이틀 ───────────────────────────────────────────────
st.title("🤖 AI 관련 기업 주식 대시보드")
st.markdown("AI 산업과 관련된 **반도체, 소프트웨어, 클라우드, 로보틱스** 기업들의 주가 데이터를 분석합니다.")
st.caption("⚠️ 본 대시보드는 학습/교육 목적이며, 투자 권유가 아닙니다.")
st.divider()

# ── AI 관련 종목 딕셔너리 ─────────────────────────────────
AI_STOCKS = {
    "🔵 반도체": {
        "NVIDIA":           "NVDA",
        "AMD":              "AMD",
        "Intel":            "INTC",
        "TSMC":             "TSM",
        "Qualcomm":         "QCOM",
        "삼성전자":          "005930.KS",
        "SK하이닉스":        "000660.KS",
    },
    "🟢 소프트웨어/플랫폼": {
        "Microsoft":        "MSFT",
        "Google":           "GOOGL",
        "Meta":             "META",
        "OpenAI(파트너 MS)": "MSFT",
        "IBM":              "IBM",
        "Palantir":         "PLTR",
        "C3.ai":            "AI",
    },
    "🟠 클라우드": {
        "Amazon(AWS)":      "AMZN",
        "Salesforce":       "CRM",
        "Oracle":           "ORCL",
        "Snowflake":        "SNOW",
    },
    "🟣 로보틱스/자율주행": {
        "Tesla":            "TSLA",
        "Intuitive Surgical": "ISRG",
        "UiPath":           "PATH",
    },
    "🇰🇷 한국 AI 관련": {
        "NAVER":            "035420.KS",
        "카카오":            "035720.KS",
        "LG전자":           "066570.KS",
        "한화시스템":         "272210.KS",
    },
}

# 전체 종목 평탄화
ALL_STOCKS_FLAT = {}
STOCK_CATEGORY  = {}
for category, stocks in AI_STOCKS.items():
    for name, ticker in stocks.items():
        if name not in ALL_STOCKS_FLAT:          # 중복 제거
            ALL_STOCKS_FLAT[name]    = ticker
            STOCK_CATEGORY[name]     = category

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    # 기간 선택
    period_map = {
        "1개월": 30, "3개월": 90, "6개월": 180,
        "1년": 365, "2년": 730, "3년": 1095,
    }
    period_label = st.selectbox("📅 분석 기간", list(period_map.keys()), index=3)
    days      = period_map[period_label]
    end_date  = datetime.today()
    start_date = end_date - timedelta(days=days)

    st.markdown("---")

    # 카테고리별 선택
    st.subheader("🗂️ 카테고리 선택")
    selected_names = []
    for category, stocks in AI_STOCKS.items():
        with st.expander(category, expanded=True):
            defaults = list(stocks.keys())[:2]   # 기본 2개 선택
            chosen = st.multiselect(
                f"{category} 종목",
                list(stocks.keys()),
                default=defaults,
                key=category,
                label_visibility="collapsed",
            )
            selected_names.extend(chosen)

    # 중복 제거
    selected_names = list(dict.fromkeys(selected_names))

    st.markdown("---")

    chart_type = st.radio("📊 차트 유형", ["라인 차트", "캔들스틱"], index=0)
    fetch_btn  = st.button("🔍 데이터 불러오기", use_container_width=True, type="primary")

# ── 초기 안내 ────────────────────────────────────────────
if not fetch_btn:
    # 카테고리 소개 카드
    st.subheader("📚 AI 산업 카테고리 소개")
    c1, c2 = st.columns(2)
    with c1:
        st.info("🔵 **반도체**\nAI 연산에 필수적인 GPU·NPU 등을 설계·생산하는 기업들")
        st.info("🟢 **소프트웨어/플랫폼**\nAI 모델 개발·서비스 플랫폼 기업들")
    with c2:
        st.info("🟠 **클라우드**\nAI 학습·추론 인프라를 제공하는 클라우드 기업들")
        st.info("🟣 **로보틱스/자율주행**\nAI를 활용한 자동화·로봇 기업들")
    st.stop()

if not selected_names:
    st.warning("⚠️ 최소 1개 이상 종목을 선택해주세요.")
    st.stop()

# ── 데이터 로딩 ───────────────────────────────────────────
@st.cache_data(ttl=600)
def load_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, start=start, end=end,
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

def calc_return(df):
    if df.empty or len(df) < 2:
        return None
    return round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2)

def calc_volatility(df):
    if df.empty or len(df) < 2:
        return None
    return round(df["Close"].pct_change().dropna().std() * (252 ** 0.5) * 100, 2)

start_str = start_date.strftime("%Y-%m-%d")
end_str   = end_date.strftime("%Y-%m-%d")

all_data = {}
prog = st.progress(0, text="데이터 로딩 중...")
for i, name in enumerate(selected_names):
    ticker = ALL_STOCKS_FLAT[name]
    df = load_data(ticker, start_str, end_str)
    label = f"{STOCK_CATEGORY[name]} {name}"
    if not df.empty:
        all_data[label] = df
    prog.progress((i + 1) / len(selected_names), text=f"{name} 로딩 중...")
prog.empty()

if not all_data:
    st.error("❌ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도하세요.")
    st.stop()

COLORS = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24

# ════════════════════════════════════════════════════════
# 섹션 1 : 핵심 지표 카드
# ════════════════════════════════════════════════════════
st.subheader(f"📋 핵심 지표  |  기간: {period_label}")

cols = st.columns(min(len(all_data), 4))
for idx, (label, df) in enumerate(all_data.items()):
    ret = calc_return(df)
    vol = calc_volatility(df)
    last = df["Close"].iloc[-1]
    with cols[idx % 4]:
        st.metric(
            label=label,
            value=f"{last:,.2f}",
            delta=f"{ret:+.2f}%" if ret is not None else "N/A",
        )
        st.caption(f"📉 변동성: {vol:.1f}%" if vol else "변동성: N/A")

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 2 : 정규화 수익률 비교
# ════════════════════════════════════════════════════════
st.subheader("📊 정규화 수익률 비교 (시작일 = 100)")

fig_norm = go.Figure()
for idx, (label, df) in enumerate(all_data.items()):
    norm = df["Close"] / df["Close"].iloc[0] * 100
    fig_norm.add_trace(go.Scatter(
        x=df.index, y=norm, mode="lines", name=label,
        line=dict(width=2, color=COLORS[idx % len(COLORS)]),
        hovertemplate=f"<b>{label}</b><br>날짜: %{{x|%Y-%m-%d}}<br>지수: %{{y:.2f}}<extra></extra>",
    ))

fig_norm.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
fig_norm.update_layout(
    height=500, hovermode="x unified", template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_title="날짜", yaxis_title="수익률 지수",
    margin=dict(l=40, r=40, t=40, b=40),
)
st.plotly_chart(fig_norm, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 3 : 수익률 랭킹
# ════════════════════════════════════════════════════════
st.subheader(f"🏆 {period_label} 수익률 랭킹")

bar_data = {
    label: calc_return(df)
    for label, df in all_data.items()
    if calc_return(df) is not None
}
bar_df = (
    pd.DataFrame.from_dict(bar_data, orient="index", columns=["수익률(%)"])
    .sort_values("수익률(%)", ascending=True)
)
bar_df["색상"] = bar_df["수익률(%)"].apply(
    lambda x: "#ef553b" if x < 0 else "#00cc96"
)

fig_bar = go.Figure(go.Bar(
    x=bar_df["수익률(%)"],
    y=bar_df.index,
    orientation="h",
    marker_color=bar_df["색상"],
    text=[f"{v:+.2f}%" for v in bar_df["수익률(%)"]],
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>수익률: %{x:.2f}%<extra></extra>",
))
fig_bar.update_layout(
    height=max(300, len(bar_df) * 48),
    xaxis_title="수익률 (%)",
    template="plotly_dark",
    margin=dict(l=40, r=80, t=20, b=40),
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 4 : 개별 종목 차트
# ════════════════════════════════════════════════════════
st.subheader(f"🕯️ 개별 종목 차트 ({chart_type})")

names_list = list(all_data.keys())
for row_start in range(0, len(names_list), 2):
    cols2 = st.columns(2)
    for col_idx, label in enumerate(names_list[row_start: row_start + 2]):
        df = all_data[label]
        with cols2[col_idx]:
            fig_sub = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                row_heights=[0.75, 0.25], vertical_spacing=0.03,
            )
            color = COLORS[names_list.index(label) % len(COLORS)]

            if chart_type == "캔들스틱":
                fig_sub.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["Open"], high=df["High"],
                    low=df["Low"],   close=df["Close"],
                    name="가격",
                    increasing_line_color="#00cc96",
                    decreasing_line_color="#ef553b",
                ), row=1, col=1)
            else:
                fig_sub.add_trace(go.Scatter(
                    x=df.index, y=df["Close"],
                    mode="lines", name="종가",
                    line=dict(color=color, width=2),
                ), row=1, col=1)

            # MA20
            if len(df) >= 20:
                fig_sub.add_trace(go.Scatter(
                    x=df.index, y=df["Close"].rolling(20).mean(),
                    mode="lines", name="MA20",
                    line=dict(color="orange", width=1, dash="dot"),
                ), row=1, col=1)

            # 거래량
            vol_colors = [
                "#00cc96" if i == 0 or df["Close"].iloc[i] >= df["Close"].iloc[i-1]
                else "#ef553b"
                for i in range(len(df))
            ]
            fig_sub.add_trace(go.Bar(
                x=df.index, y=df["Volume"],
                name="거래량", marker_color=vol_colors, opacity=0.6,
            ), row=2, col=1)

            ret_val = calc_return(df)
            fig_sub.update_layout(
                title=dict(
                    text=f"{label}  ({ret_val:+.2f}%)" if ret_val else label,
                    font=dict(size=13),
                ),
                height=420, template="plotly_dark",
                showlegend=False,
                xaxis_rangeslider_visible=False,
                margin=dict(l=30, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_sub, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 5 : 상관관계 히트맵
# ════════════════════════════════════════════════════════
if len(all_data) >= 2:
    st.subheader("🔗 AI 종목 간 수익률 상관관계")

    ret_df = pd.DataFrame(
        {label: df["Close"].pct_change() for label, df in all_data.items()}
    ).dropna()
    corr = ret_df.corr().round(2)

    fig_heat = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu", zmid=0,
        text=corr.values, texttemplate="%{text:.2f}",
        hovertemplate="X: %{x}<br>Y: %{y}<br>상관계수: %{z:.2f}<extra></extra>",
    ))
    fig_heat.update_layout(
        height=max(400, len(all_data) * 55),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=20, b=80),
        xaxis=dict(tickangle=-35),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.divider()

# ════════════════════════════════════════════════════════
# 섹션 6 : 원시 데이터
# ════════════════════════════════════════════════════════
with st.expander("📄 원시 데이터 보기 (최근 20일)"):
    for label, df in all_data.items():
        st.markdown(f"**{label}**")
        show = df[["Open","High","Low","Close","Volume"]].tail(20).copy()
        show.index = show.index.strftime("%Y-%m-%d")
        show.columns = ["시가","고가","저가","종가","거래량"]
        st.dataframe(show, use_container_width=True)

st.caption("📌 데이터 출처: Yahoo Finance | 10분 캐시 갱신 | 교육 목적 대시보드이며 투자 권유가 아닙니다.")
