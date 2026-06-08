import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="🌏 한·미 주식 비교 분석",
    page_icon="📈",
    layout="wide",
)

# ── 타이틀 ───────────────────────────────────────────────
st.title("📈 한국 & 미국 주요 주식 비교 분석")
st.markdown("**yfinance** 데이터를 기반으로 한국·미국 주요 종목의 수익률과 차트를 한눈에 비교합니다.")
st.divider()

# ── 종목 딕셔너리 ─────────────────────────────────────────
KOREAN_STOCKS = {
    "삼성전자":   "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차":     "005380.KS",
    "NAVER":      "035420.KS",
    "카카오":     "035720.KS",
    "셀트리온":   "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "KB금융":     "105560.KS",
    "삼성바이오로직스": "207940.KS",
}

US_STOCKS = {
    "Apple":      "AAPL",
    "Microsoft":  "MSFT",
    "NVIDIA":     "NVDA",
    "Amazon":     "AMZN",
    "Google":     "GOOGL",
    "Meta":       "META",
    "Tesla":      "TSLA",
    "Berkshire":  "BRK-B",
    "JPMorgan":   "JPM",
    "Netflix":    "NFLX",
}

# ── 사이드바 설정 ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    # 기간 선택
    period_options = {
        "1개월":  30,
        "3개월":  90,
        "6개월":  180,
        "1년":    365,
        "2년":    730,
        "5년":    1825,
    }
    selected_period_label = st.selectbox(
        "📅 분석 기간",
        list(period_options.keys()),
        index=3,
    )
    days = period_options[selected_period_label]
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=days)

    st.markdown("---")

    # 한국 종목 선택
    st.subheader("🇰🇷 한국 종목 선택")
    selected_korean = st.multiselect(
        "종목을 선택하세요",
        list(KOREAN_STOCKS.keys()),
        default=["삼성전자", "SK하이닉스", "NAVER"],
    )

    st.markdown("---")

    # 미국 종목 선택
    st.subheader("🇺🇸 미국 종목 선택")
    selected_us = st.multiselect(
        "종목을 선택하세요",
        list(US_STOCKS.keys()),
        default=["Apple", "NVIDIA", "Tesla"],
    )

    st.markdown("---")

    # 차트 유형
    st.subheader("📊 차트 유형")
    chart_type = st.radio(
        "캔들 / 라인",
        ["라인 차트", "캔들스틱"],
        index=0,
    )

    fetch_btn = st.button("🔍 데이터 불러오기", use_container_width=True, type="primary")

# ── 데이터 로딩 함수 ──────────────────────────────────────
@st.cache_data(ttl=600)
def load_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

def calc_return(df: pd.DataFrame) -> float:
    """기간 수익률(%) 계산"""
    if df.empty or len(df) < 2:
        return None
    return round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2)

def calc_volatility(df: pd.DataFrame) -> float:
    """연환산 변동성(%) 계산"""
    if df.empty or len(df) < 2:
        return None
    daily_ret = df["Close"].pct_change().dropna()
    return round(daily_ret.std() * (252 ** 0.5) * 100, 2)

# ── 초기 안내 ────────────────────────────────────────────
if not fetch_btn:
    st.info("👈 왼쪽 사이드바에서 종목과 기간을 선택한 뒤 **[데이터 불러오기]** 버튼을 누르세요!")
    st.stop()

if not selected_korean and not selected_us:
    st.warning("⚠️ 한국 또는 미국 종목을 최소 1개 이상 선택해주세요.")
    st.stop()

# ── 데이터 수집 ───────────────────────────────────────────
start_str = start_date.strftime("%Y-%m-%d")
end_str   = end_date.strftime("%Y-%m-%d")

all_data   = {}   # {이름: df}
all_tickers = {}  # {이름: ticker}

progress_bar = st.progress(0, text="데이터를 불러오는 중...")
total = len(selected_korean) + len(selected_us)

for i, name in enumerate(selected_korean):
    ticker = KOREAN_STOCKS[name]
    df = load_data(ticker, start_str, end_str)
    if not df.empty:
        all_data[f"🇰🇷 {name}"] = df
        all_tickers[f"🇰🇷 {name}"] = ticker
    progress_bar.progress((i + 1) / total, text=f"{name} 로딩 중...")

for i, name in enumerate(selected_us):
    ticker = US_STOCKS[name]
    df = load_data(ticker, start_str, end_str)
    if not df.empty:
        all_data[f"🇺🇸 {name}"] = df
        all_tickers[f"🇺🇸 {name}"] = ticker
    progress_bar.progress((len(selected_korean) + i + 1) / total, text=f"{name} 로딩 중...")

progress_bar.empty()

if not all_data:
    st.error("❌ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도하세요.")
    st.stop()

# ════════════════════════════════════════════════════════
# 섹션 1 : 핵심 지표 카드
# ════════════════════════════════════════════════════════
st.subheader(f"📋 핵심 지표 요약  |  기간: {selected_period_label}")

cols = st.columns(min(len(all_data), 5))  # 한 행에 최대 5개
for idx, (name, df) in enumerate(all_data.items()):
    col = cols[idx % len(cols)]
    ret  = calc_return(df)
    vol  = calc_volatility(df)
    last = df["Close"].iloc[-1]

    color = "🟢" if ret and ret >= 0 else "🔴"
    with col:
        st.metric(
            label=name,
            value=f"{last:,.1f}",
            delta=f"{ret:+.2f}%" if ret is not None else "N/A",
        )
        st.caption(f"변동성: {vol:.1f}%" if vol else "변동성: N/A")

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 2 : 정규화 수익률 비교 (라인)
# ════════════════════════════════════════════════════════
st.subheader("📊 정규화 수익률 비교 (기준: 첫날 = 100)")

fig_norm = go.Figure()

COLORS = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24

for idx, (name, df) in enumerate(all_data.items()):
    normalized = df["Close"] / df["Close"].iloc[0] * 100
    fig_norm.add_trace(
        go.Scatter(
            x=df.index,
            y=normalized,
            mode="lines",
            name=name,
            line=dict(width=2, color=COLORS[idx % len(COLORS)]),
            hovertemplate=f"<b>{name}</b><br>날짜: %{{x|%Y-%m-%d}}<br>수익률지수: %{{y:.2f}}<extra></extra>",
        )
    )

fig_norm.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
fig_norm.update_layout(
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_title="날짜",
    yaxis_title="수익률 지수 (시작=100)",
    template="plotly_dark",
    margin=dict(l=40, r=40, t=40, b=40),
)
st.plotly_chart(fig_norm, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 3 : 수익률 막대그래프
# ════════════════════════════════════════════════════════
st.subheader("📊 기간 수익률 순위")

bar_data = {
    name: calc_return(df)
    for name, df in all_data.items()
    if calc_return(df) is not None
}
bar_df = (
    pd.DataFrame.from_dict(bar_data, orient="index", columns=["수익률(%)"])
    .sort_values("수익률(%)", ascending=True)
)
bar_df["색상"] = bar_df["수익률(%)"].apply(lambda x: "#ef553b" if x < 0 else "#00cc96")

fig_bar = go.Figure(
    go.Bar(
        x=bar_df["수익률(%)"],
        y=bar_df.index,
        orientation="h",
        marker_color=bar_df["색상"],
        text=[f"{v:+.2f}%" for v in bar_df["수익률(%)"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>수익률: %{x:.2f}%<extra></extra>",
    )
)
fig_bar.update_layout(
    height=max(300, len(bar_df) * 45),
    xaxis_title="수익률 (%)",
    template="plotly_dark",
    margin=dict(l=40, r=80, t=20, b=40),
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 4 : 개별 종목 차트 (캔들 or 라인)
# ════════════════════════════════════════════════════════
st.subheader(f"🕯️ 개별 종목 차트  ({chart_type})")

# 2열 그리드
names_list = list(all_data.keys())
for row_start in range(0, len(names_list), 2):
    cols2 = st.columns(2)
    for col_idx, name in enumerate(names_list[row_start: row_start + 2]):
        df = all_data[name]
        with cols2[col_idx]:
            fig_sub = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                row_heights=[0.75, 0.25],
                vertical_spacing=0.03,
            )

            # 가격 차트
            if chart_type == "캔들스틱":
                fig_sub.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        name="가격",
                        increasing_line_color="#00cc96",
                        decreasing_line_color="#ef553b",
                    ),
                    row=1, col=1,
                )
            else:
                fig_sub.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df["Close"],
                        mode="lines",
                        name="종가",
                        line=dict(color=COLORS[names_list.index(name) % len(COLORS)], width=2),
                    ),
                    row=1, col=1,
                )

            # 이동평균선 (20일)
            if len(df) >= 20:
                ma20 = df["Close"].rolling(20).mean()
                fig_sub.add_trace(
                    go.Scatter(
                        x=df.index, y=ma20,
                        mode="lines", name="MA20",
                        line=dict(color="orange", width=1, dash="dot"),
                    ),
                    row=1, col=1,
                )

            # 거래량
            vol_colors = [
                "#00cc96" if df["Close"].iloc[i] >= df["Close"].iloc[i - 1] else "#ef553b"
                for i in range(len(df))
            ]
            fig_sub.add_trace(
                go.Bar(
                    x=df.index,
                    y=df["Volume"],
                    name="거래량",
                    marker_color=vol_colors,
                    opacity=0.6,
                ),
                row=2, col=1,
            )

            ret_val = calc_return(df)
            title_ret = f"({ret_val:+.2f}%)" if ret_val is not None else ""

            fig_sub.update_layout(
                title=dict(text=f"{name} {title_ret}", font=dict(size=14)),
                height=400,
                template="plotly_dark",
                showlegend=False,
                xaxis_rangeslider_visible=False,
                margin=dict(l=30, r=20, t=40, b=20),
            )
            fig_sub.update_yaxes(title_text="가격", row=1, col=1)
            fig_sub.update_yaxes(title_text="거래량", row=2, col=1)

            st.plotly_chart(fig_sub, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════
# 섹션 5 : 상관관계 히트맵
# ════════════════════════════════════════════════════════
if len(all_data) >= 2:
    st.subheader("🔗 종목 간 수익률 상관관계")

    # 일별 수익률 테이블 구성
    returns_df = pd.DataFrame(
        {name: df["Close"].pct_change() for name, df in all_data.items()}
    ).dropna()

    corr = returns_df.corr().round(2)

    fig_heat = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu",
            zmid=0,
            text=corr.values,
            texttemplate="%{text:.2f}",
            hovertemplate="X: %{x}<br>Y: %{y}<br>상관계수: %{z:.2f}<extra></extra>",
        )
    )
    fig_heat.update_layout(
        height=max(400, len(all_data) * 50),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

# ════════════════════════════════════════════════════════
# 섹션 6 : 원시 데이터 테이블
# ════════════════════════════════════════════════════════
with st.expander("📄 원시 데이터 보기"):
    for name, df in all_data.items():
        st.markdown(f"**{name}**")
        show_df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        show_df.index = show_df.index.strftime("%Y-%m-%d")
        show_df.columns = ["시가", "고가", "저가", "종가", "거래량"]
        st.dataframe(show_df.tail(30), use_container_width=True)

# ── 푸터 ──────────────────────────────────────────────
st.caption("📌 데이터 출처: Yahoo Finance (yfinance)  |  10분마다 캐시 갱신  |  투자 참고용이며 투자 권유가 아닙니다.")
