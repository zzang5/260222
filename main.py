import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO
import warnings
import os
import pathlib
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════
#  페이지 설정
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700&family=Bebas+Neue&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem;
    letter-spacing: 4px;
    background: linear-gradient(135deg, #e8d5b7, #f5c842);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.sub-title {
    color: #8a9bb0;
    font-size: 0.82rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}
.kpi-grid { display: flex; gap: 10px; flex-wrap: wrap; margin: 14px 0; }
.kpi-card {
    flex: 1; min-width: 130px;
    background: linear-gradient(145deg, #1a2332, #243044);
    border: 1px solid #2e3f55;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.kpi-label { color: #8a9bb0; font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
.kpi-value { color: #e8d5b7; font-size: 1.75rem; font-weight: 700; line-height: 1; }
.kpi-sub   { color: #5a7a9a; font-size: 0.68rem; margin-top: 3px; }
.section-divider { border: none; border-top: 1px solid #2e3f55; margin: 18px 0; }
.compare-card {
    border-radius: 12px; padding: 14px 18px; margin: 8px 0;
    border: 1px solid #2e3f55;
}
.compare-hot  { background: linear-gradient(145deg, #2a1515, #3a1e1e); border-color: #7a3a3a; }
.compare-cold { background: linear-gradient(145deg, #152030, #1e2d40); border-color: #3a6a8a; }
.compare-norm { background: linear-gradient(145deg, #1a2a1a, #222e22); border-color: #3a6a3a; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #111827; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; font-weight: 600; border-radius: 8px; padding: 8px 14px; color: #8a9bb0; }
.stTabs [aria-selected="true"] { background: #243044 !important; color: #e8d5b7 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  수능 날짜 데이터 (시행연도 기준 1993~2025)
# ═══════════════════════════════════════════════════════
SUNEUNG = {
    "1994학년도 1차": ("1993-08-20", "첫 수능 1차 (여름)"),
    "1994학년도 2차": ("1993-11-16", "첫 수능 2차"),
    "1995학년도":    ("1994-11-23", ""),
    "1996학년도":    ("1995-11-22", ""),
    "1997학년도":    ("1996-11-13", "역대 최악 불수능"),
    "1998학년도":    ("1997-11-19", "IMF 발표 당일"),
    "1999학년도":    ("1998-11-18", "최초 만점자 배출"),
    "2000학년도":    ("1999-11-17", ""),
    "2001학년도":    ("2000-11-15", "최대 물수능, 만점자 66명"),
    "2002학년도":    ("2001-11-07", "불수능"),
    "2003학년도":    ("2002-11-06", ""),
    "2004학년도":    ("2003-11-05", ""),
    "2005학년도":    ("2004-11-17", ""),
    "2006학년도":    ("2005-11-23", ""),
    "2007학년도":    ("2006-11-16", ""),
    "2008학년도":    ("2007-11-15", ""),
    "2009학년도":    ("2008-11-13", ""),
    "2010학년도":    ("2009-11-12", ""),
    "2011학년도":    ("2010-11-18", "G20으로 1주 연기"),
    "2012학년도":    ("2011-11-10", ""),
    "2013학년도":    ("2012-11-08", "이상 고온"),
    "2014학년도":    ("2013-11-07", ""),
    "2015학년도":    ("2014-11-13", ""),
    "2016학년도":    ("2015-11-12", ""),
    "2017학년도":    ("2016-11-17", ""),
    "2018학년도":    ("2017-11-23", "포항 지진으로 1주 연기"),
    "2019학년도":    ("2018-11-15", ""),
    "2020학년도":    ("2019-11-14", ""),
    "2021학년도":    ("2020-12-03", "COVID-19로 12월 연기"),
    "2022학년도":    ("2021-11-18", ""),
    "2023학년도":    ("2022-11-17", ""),
    "2024학년도":    ("2023-11-16", ""),
    "2025학년도":    ("2024-11-14", "이상 고온"),
    "2026학년도":    ("2025-11-13", "이상 고온"),
}

# ═══════════════════════════════════════════════════════
#  데이터 로드 함수
# ═══════════════════════════════════════════════════════
# app.py 가 있는 폴더 기준으로 절대 경로 설정 → Streamlit Cloud에서도 안정적으로 동작
_HERE = pathlib.Path(__file__).parent.resolve()
BUILTIN_FILE = _HERE / "20260122_temp.csv"

@st.cache_data(show_spinner="📂 기본 데이터 로딩 중…")
def load_builtin():
    if not BUILTIN_FILE.exists():
        st.error(
            f"⚠️ 기본 데이터 파일을 찾을 수 없습니다.\n\n"
            f"**찾는 경로:** `{BUILTIN_FILE}`\n\n"
            f"`20260122_temp.csv` 파일을 `app.py` 와 **같은 폴더**에 넣어 주세요."
        )
        return None
    # EUC-KR → UTF-8 순으로 인코딩 시도
    for enc in ["euc-kr", "cp949", "utf-8", "utf-8-sig"]:
        try:
            df = pd.read_csv(
                BUILTIN_FILE, encoding=enc, header=0,
                names=["날짜","지점","평균기온","최저기온","최고기온"],
                skipinitialspace=True,
            )
            return _clean(df)
        except (UnicodeDecodeError, Exception):
            continue
    st.error("기본 데이터 파일의 인코딩을 인식할 수 없습니다.")
    return None

def load_uploaded(file):
    raw = file.read()
    text = None
    for enc in ["euc-kr","utf-8","cp949"]:
        try:
            text = raw.decode(enc); break
        except Exception:
            pass
    if text is None:
        st.error("파일 인코딩을 인식할 수 없습니다."); return None
    df = pd.read_csv(
        StringIO(text), header=0,
        names=["날짜","지점","평균기온","최저기온","최고기온"],
        skipinitialspace=True,
    )
    return _clean(df)

def _clean(df):
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    for c in ["평균기온","최저기온","최고기온"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["평균기온","최저기온","최고기온"])
    df["연도"] = df["날짜"].dt.year
    df["월"]   = df["날짜"].dt.month
    df["일"]   = df["날짜"].dt.day
    return df.sort_values("날짜").reset_index(drop=True)

_DARK = dict(
    plot_bgcolor="#0f1923", paper_bgcolor="#0f1923",
    font=dict(color="#8a9bb0"),
    xaxis=dict(showgrid=True, gridcolor="#1e2e3e"),
    yaxis=dict(showgrid=True, gridcolor="#1e2e3e"),
    legend=dict(orientation="h", y=1.06),
    margin=dict(t=40, b=20),
)

# ═══════════════════════════════════════════════════════
#  사이드바
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="main-title">🌡️ SEOUL<br>TEMP</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">기상청 ASOS · 지점 108</div>', unsafe_allow_html=True)
    st.markdown("---")
    uploaded = st.file_uploader("📤 추가 CSV 업로드", type=["csv"],
        help="날짜,지점,평균기온(℃),최저기온(℃),최고기온(℃) 형식")
    st.markdown("---")
    st.markdown("**📅 기간 필터**")
    yr_placeholder = st.empty()
    month_sel = st.multiselect("월 선택 (전체=미선택)", list(range(1,13)),
        format_func=lambda m: f"{m}월")

# ═══════════════════════════════════════════════════════
#  데이터 병합
# ═══════════════════════════════════════════════════════
base_df = load_builtin()
if base_df is None:
    st.stop()

if uploaded is not None:
    up_df = load_uploaded(uploaded)
    if up_df is not None:
        df = (pd.concat([base_df, up_df])
              .drop_duplicates("날짜").sort_values("날짜").reset_index(drop=True))
        df["연도"] = df["날짜"].dt.year
        df["월"]   = df["날짜"].dt.month
        df["일"]   = df["날짜"].dt.day
        st.sidebar.success(f"✅ {len(up_df):,}행 추가됨")
    else:
        df = base_df
else:
    df = base_df

min_yr, max_yr = int(df["연도"].min()), int(df["연도"].max())
with yr_placeholder:
    yr_range = st.slider("연도 범위", min_yr, max_yr, (max(min_yr, max_yr-30), max_yr))

fdf = df[(df["연도"]>=yr_range[0]) & (df["연도"]<=yr_range[1])]
if month_sel:
    fdf = fdf[fdf["월"].isin(month_sel)]

# ═══════════════════════════════════════════════════════
#  헤더 + KPI
# ═══════════════════════════════════════════════════════
st.markdown('<div class="main-title">서울 기온 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">기상청 ASOS · 지점 108 · '
    f'{df["날짜"].min().strftime("%Y.%m.%d")} ~ {df["날짜"].max().strftime("%Y.%m.%d")}</div>',
    unsafe_allow_html=True
)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

idx_hi = fdf["최고기온"].idxmax()
idx_lo = fdf["최저기온"].idxmin()
idx_rng= (fdf["최고기온"]-fdf["최저기온"]).idxmax()

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">📊 평균기온</div>
    <div class="kpi-value">{fdf['평균기온'].mean():.1f}℃</div>
    <div class="kpi-sub">{yr_range[0]}~{yr_range[1]}년</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">🔴 역대 최고</div>
    <div class="kpi-value">{fdf['최고기온'].max():.1f}℃</div>
    <div class="kpi-sub">{fdf.loc[idx_hi,'날짜'].strftime('%Y-%m-%d')}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">🔵 역대 최저</div>
    <div class="kpi-value">{fdf['최저기온'].min():.1f}℃</div>
    <div class="kpi-sub">{fdf.loc[idx_lo,'날짜'].strftime('%Y-%m-%d')}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">↕️ 최대 일교차</div>
    <div class="kpi-value">{(fdf['최고기온']-fdf['최저기온']).max():.1f}℃</div>
    <div class="kpi-sub">{fdf.loc[idx_rng,'날짜'].strftime('%Y-%m-%d')}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">📅 데이터</div>
    <div class="kpi-value">{len(fdf):,}</div>
    <div class="kpi-sub">일 (필터 후)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  탭
# ═══════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 날짜 비교", "📈 시계열", "📊 월별·연별", "🔥 기후변화", "🎓 수능날 기온", "📋 원본"
])

# ──────────────────────────────────────────────
# TAB 1 — 날짜 비교
# ──────────────────────────────────────────────
with tab1:
    st.subheader("📅 특정 날짜 기온 — 과거 같은 날과 비교")

    col_d, col_y = st.columns([1,2])
    with col_d:
        latest = df["날짜"].max().date()
        sel_date = st.date_input("분석할 날짜",
            value=latest,
            min_value=df["날짜"].min().date(),
            max_value=df["날짜"].max().date(),
            help="기본값: 데이터상 가장 최근 날짜")
    with col_y:
        compare_yrs = st.slider("비교 기준 기간 (최근 N년)", 10, 130, 30,
            help="선택 날짜와 같은 월·일 데이터 중 최근 몇 년치 평균을 '평년'으로 삼을지")

    t_row = df[df["날짜"]==pd.Timestamp(sel_date)]

    if t_row.empty:
        st.warning(f"⚠️ {sel_date} 날짜의 데이터가 없습니다.")
    else:
        r = t_row.iloc[0]
        t_avg, t_hi, t_lo = r["평균기온"], r["최고기온"], r["최저기온"]

        cutoff_yr = sel_date.year - compare_yrs
        same_md = df[
            (df["월"]==sel_date.month) & (df["일"]==sel_date.day) &
            (df["날짜"] < pd.Timestamp(sel_date)) & (df["연도"] >= cutoff_yr)
        ]
        all_same = df[
            (df["월"]==sel_date.month) & (df["일"]==sel_date.day)
        ].sort_values("연도")

        if same_md.empty:
            st.info("선택한 기간 내 같은 날짜의 과거 데이터가 없습니다.")
        else:
            ref_avg = same_md["평균기온"].mean()
            ref_hi  = same_md["최고기온"].mean()
            ref_lo  = same_md["최저기온"].mean()
            n_ref   = len(same_md)
            diff_avg = t_avg - ref_avg

            if diff_avg >= 2:
                cls = "compare-hot"; emoji = "🔴"
                verdict = f"평년보다 {abs(diff_avg):.1f}℃ 더 따뜻한 날"
            elif diff_avg <= -2:
                cls = "compare-cold"; emoji = "🔵"
                verdict = f"평년보다 {abs(diff_avg):.1f}℃ 더 추운 날"
            else:
                cls = "compare-norm"; emoji = "🟢"
                verdict = f"평년과 비슷한 날 (차이 {abs(diff_avg):.1f}℃)"

            st.markdown(f"""
            <div class="compare-card {cls}">
              <div style="font-size:1.1rem;font-weight:700;color:#e8d5b7;margin-bottom:6px;">
                {emoji} {sel_date.strftime('%Y년 %m월 %d일')} — {verdict}
              </div>
              <div style="color:#8a9bb0;font-size:0.76rem;">
                비교 기준: {cutoff_yr}~{sel_date.year-1}년 같은 날({n_ref}개년) 평균
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            for col_w, label, t_val, r_val in [
                (c1,"평균기온",t_avg,ref_avg),
                (c2,"최고기온",t_hi, ref_hi),
                (c3,"최저기온",t_lo, ref_lo),
            ]:
                d = t_val - r_val
                col_w.metric(label, f"{t_val:.1f}℃",
                    delta=f"{'▲' if d>0 else '▼' if d<0 else '—'} {abs(d):.1f}℃ (평년 {r_val:.1f}℃)")

            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

            # 같은 월·일 전체 연도 추이
            st.markdown(f"#### 📈 {sel_date.month}월 {sel_date.day}일 — 연도별 평균기온")
            bar_colors = [
                "#e74c3c" if v >= ref_avg+2 else ("#3498db" if v <= ref_avg-2 else "#7fb3d3")
                for v in all_same["평균기온"]
            ]
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=all_same["연도"], y=all_same["평균기온"],
                marker_color=bar_colors, name="평균기온",
                text=[f"{v:.1f}" for v in all_same["평균기온"]],
                textposition="outside", textfont=dict(size=8, color="#8a9bb0"),
                hovertemplate="<b>%{x}년</b><br>평균기온: %{y:.1f}℃<extra></extra>",
            ))
            fig1.add_hline(y=ref_avg, line_dash="dot", line_color="#f39c12",
                annotation_text=f"평년({cutoff_yr}~{sel_date.year-1}) {ref_avg:.1f}℃",
                annotation_font_color="#f39c12")
            if sel_date.year in all_same["연도"].values:
                fig1.add_vline(x=sel_date.year, line_width=2.5, line_color="#e8d5b7",
                    annotation_text=f"{sel_date.year}년", annotation_font_color="#e8d5b7")
            fig1.update_layout(height=360, hovermode="x unified", **_DARK)
            fig1.update_layout(xaxis=dict(showgrid=False), yaxis_title="평균기온 (℃)")
            st.plotly_chart(fig1, use_container_width=True)

            # 월 분포 박스플롯
            st.markdown(f"#### 📦 {sel_date.month}월 기온 분포 (최근 {compare_yrs}년)")
            recent_month = df[
                (df["월"]==sel_date.month) & (df["연도"]>=cutoff_yr)
            ]
            fig2 = go.Figure()
            for cn, color, name in [
                ("최고기온","#e74c3c","최고기온"),
                ("평균기온","#f39c12","평균기온"),
                ("최저기온","#3498db","최저기온"),
            ]:
                fig2.add_trace(go.Box(y=recent_month[cn], name=name,
                    marker_color=color, boxmean=True, line=dict(width=1.5)))
            for cn, val in [("최고기온",t_hi),("평균기온",t_avg),("최저기온",t_lo)]:
                fig2.add_trace(go.Scatter(
                    x=[cn], y=[val], mode="markers",
                    marker=dict(color="#e8d5b7",size=13,symbol="star"),
                    showlegend=False, name=f"선택날 {cn}",
                ))
            fig2.update_layout(height=340, boxmode="group", **_DARK)
            fig2.update_layout(xaxis=dict(showgrid=False), yaxis_title="기온 (℃)")
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("⭐ 별 마커 = 선택 날짜 실제 기온  |  🔴따뜻  🔵추움  🟤평년근처")

# ──────────────────────────────────────────────
# TAB 2 — 시계열
# ──────────────────────────────────────────────
with tab2:
    st.subheader("📈 기온 시계열")
    resample_opt = st.radio("집계 단위", ["일","월","연"], horizontal=True)
    rule = {"일":"D","월":"ME","연":"YE"}[resample_opt]
    ts = fdf.set_index("날짜")[["평균기온","최저기온","최고기온"]].resample(rule).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts["최고기온"], name="최고기온",
        line=dict(color="#e74c3c",width=1.2)))
    fig.add_trace(go.Scatter(x=ts.index, y=ts["최저기온"], name="최저기온",
        line=dict(color="#3498db",width=1.2),
        fill="tonexty", fillcolor="rgba(52,152,219,0.07)"))
    fig.add_trace(go.Scatter(x=ts.index, y=ts["평균기온"], name="평균기온",
        line=dict(color="#f39c12",width=2.5)))
    fig.update_layout(height=460, hovermode="x unified", **_DARK)
    fig.update_layout(yaxis_title="기온 (℃)")
    st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────
# TAB 3 — 월별·연별
# ──────────────────────────────────────────────
with tab3:
    cl, cr = st.columns(2)
    with cl:
        st.markdown("#### 월별 기온 범위")
        monthly = fdf.groupby("월").agg(
            평균기온=("평균기온","mean"),최저기온=("최저기온","mean"),최고기온=("최고기온","mean")
        ).reset_index()
        monthly["월명"] = monthly["월"].apply(lambda m: f"{m}월")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=monthly["월명"],
            y=monthly["최고기온"]-monthly["최저기온"],
            base=monthly["최저기온"],name="범위",
            marker_color="rgba(52,152,219,0.3)"))
        fig3.add_trace(go.Scatter(x=monthly["월명"],y=monthly["평균기온"],
            name="평균기온",mode="lines+markers",
            line=dict(color="#f39c12",width=3),marker=dict(size=8)))
        fig3.update_layout(height=340,**_DARK)
        fig3.update_layout(xaxis=dict(showgrid=False),yaxis_title="기온 (℃)")
        st.plotly_chart(fig3,use_container_width=True)

    with cr:
        st.markdown("#### 연도별 평균기온 + 추세선")
        yearly = fdf.groupby("연도")["평균기온"].mean().reset_index()
        z = np.polyfit(yearly["연도"],yearly["평균기온"],1)
        p = np.poly1d(z)
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=yearly["연도"],y=yearly["평균기온"],
            mode="lines+markers",name="평균기온",
            line=dict(color="#3498db",width=1.5),marker=dict(size=4)))
        fig4.add_trace(go.Scatter(x=yearly["연도"],y=p(yearly["연도"]),
            mode="lines",name="추세선",
            line=dict(color="#e74c3c",dash="dash",width=2)))
        fig4.update_layout(height=340,**_DARK)
        fig4.update_layout(xaxis=dict(showgrid=False),yaxis_title="기온 (℃)")
        st.plotly_chart(fig4,use_container_width=True)

    st.markdown("#### 연도×월 평균기온 히트맵")
    pivot = fdf.groupby(["연도","월"])["평균기온"].mean().unstack()
    pivot.columns = [f"{m}월" for m in pivot.columns]
    fig5 = px.imshow(pivot.T,color_continuous_scale="RdBu_r",aspect="auto",
        labels=dict(x="연도",y="월",color="평균기온(℃)"))
    fig5.update_layout(height=380,plot_bgcolor="#0f1923",paper_bgcolor="#0f1923",
        font=dict(color="#8a9bb0"))
    st.plotly_chart(fig5,use_container_width=True)

# ──────────────────────────────────────────────
# TAB 4 — 기후변화
# ──────────────────────────────────────────────
with tab4:
    st.subheader("🔥 기후변화 지표")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**폭염일수 (최고기온 ≥ 33℃)**")
        heat = fdf[fdf["최고기온"]>=33].groupby("연도").size().reset_index(name="폭염일수")
        fig6 = px.bar(heat,x="연도",y="폭염일수",color="폭염일수",color_continuous_scale="Reds")
        fig6.update_layout(height=300,plot_bgcolor="#0f1923",paper_bgcolor="#0f1923",
            font=dict(color="#8a9bb0"),coloraxis_showscale=False,
            xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="#1e2e3e"))
        st.plotly_chart(fig6,use_container_width=True)
    with cb:
        st.markdown("**한파일수 (최저기온 ≤ -12℃)**")
        cold = fdf[fdf["최저기온"]<=-12].groupby("연도").size().reset_index(name="한파일수")
        fig7 = px.bar(cold,x="연도",y="한파일수",color="한파일수",color_continuous_scale="Blues_r")
        fig7.update_layout(height=300,plot_bgcolor="#0f1923",paper_bgcolor="#0f1923",
            font=dict(color="#8a9bb0"),coloraxis_showscale=False,
            xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="#1e2e3e"))
        st.plotly_chart(fig7,use_container_width=True)

    st.markdown("**기온 편차 (1981~2010 평균 대비)**")
    bm = df[(df["연도"]>=1981)&(df["연도"]<=2010)]["평균기온"].mean()
    y2 = fdf.groupby("연도")["평균기온"].mean().reset_index()
    y2["편차"] = y2["평균기온"] - bm
    fig8 = go.Figure(go.Bar(x=y2["연도"],y=y2["편차"],
        marker_color=y2["편차"].apply(lambda x:"#e74c3c" if x>=0 else "#3498db")))
    fig8.add_hline(y=0,line_dash="dot",line_color="#e8d5b7")
    fig8.add_annotation(x=0.02,y=0.97,xref="paper",yref="paper",
        text=f"기준(1981–2010 평균): {bm:.2f}℃",showarrow=False,
        bgcolor="#1a2332",font=dict(color="#e8d5b7",size=11))
    fig8.update_layout(height=340,plot_bgcolor="#0f1923",paper_bgcolor="#0f1923",
        font=dict(color="#8a9bb0"),
        xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="#1e2e3e",title="편차 (℃)"))
    st.plotly_chart(fig8,use_container_width=True)

# ──────────────────────────────────────────────
# TAB 5 — 수능날 기온
# ──────────────────────────────────────────────
with tab5:
    st.subheader("🎓 수능 시험날 서울 기온 분석 (1993~2025년 시행)")

    # 수능 데이터 구성
    records = []
    for 학년도, (ds, note) in SUNEUNG.items():
        dt = pd.to_datetime(ds)
        row = df[df["날짜"]==dt]
        yr = dt.year
        same_ref = df[
            (df["월"]==dt.month) & (df["일"]==dt.day) &
            (df["연도"]>=yr-30) & (df["연도"]<yr)
        ]
        ref_avg = same_ref["평균기온"].mean() if not same_ref.empty else None
        if not row.empty:
            r = row.iloc[0]
            records.append({
                "학년도": 학년도, "날짜": ds, "시행연도": yr,
                "평균기온": r["평균기온"], "최저기온": r["최저기온"], "최고기온": r["최고기온"],
                "일교차": r["최고기온"]-r["최저기온"],
                "평년대비": round(r["평균기온"]-ref_avg,1) if ref_avg is not None else None,
                "비고": note,
            })
        else:
            records.append({
                "학년도": 학년도, "날짜": ds, "시행연도": yr,
                "평균기온": None, "최저기온": None, "최고기온": None,
                "일교차": None, "평년대비": None, "비고": note,
            })

    sdf = pd.DataFrame(records).dropna(subset=["평균기온"])
    sdf["시행연도"] = sdf["시행연도"].astype(int)

    # KPI
    ci = sdf["평균기온"].idxmin(); hi = sdf["평균기온"].idxmax()
    ri = sdf["일교차"].idxmax()
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">🥶 가장 추운 수능</div>
        <div class="kpi-value">{sdf.loc[ci,'평균기온']:.1f}℃</div>
        <div class="kpi-sub">{sdf.loc[ci,'학년도']} · {sdf.loc[ci,'날짜']}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">🥵 가장 더운 수능</div>
        <div class="kpi-value">{sdf.loc[hi,'평균기온']:.1f}℃</div>
        <div class="kpi-sub">{sdf.loc[hi,'학년도']} · {sdf.loc[hi,'날짜']}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">↕️ 최대 일교차</div>
        <div class="kpi-value">{sdf.loc[ri,'일교차']:.1f}℃</div>
        <div class="kpi-sub">{sdf.loc[ri,'학년도']} · {sdf.loc[ri,'날짜']}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">📊 수능 평균기온</div>
        <div class="kpi-value">{sdf['평균기온'].mean():.1f}℃</div>
        <div class="kpi-sub">전체 수능 평균</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">🌡️ 수능 시행 횟수</div>
        <div class="kpi-value">{len(sdf)}</div>
        <div class="kpi-sub">데이터 있는 시험</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 차트 1: 연도별 기온 범위 + 평균기온
    st.markdown("#### 📊 연도별 수능 당일 기온")
    mcolors = []
    for v in sdf["평년대비"]:
        if v is None: mcolors.append("#7f8c8d")
        elif v >= 3:  mcolors.append("#e74c3c")
        elif v <= -3: mcolors.append("#3498db")
        else:         mcolors.append("#f39c12")

    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        x=sdf["시행연도"], y=sdf["최고기온"]-sdf["최저기온"], base=sdf["최저기온"],
        name="최저~최고 범위", marker_color="rgba(100,120,200,0.2)",
        hovertemplate="<b>%{customdata}</b><br>최저: %{base:.1f}℃ / 최고: %{y:.1f}℃<extra></extra>",
        customdata=sdf["학년도"],
    ))
    fig_s.add_trace(go.Scatter(
        x=sdf["시행연도"], y=sdf["평균기온"], mode="markers+lines", name="평균기온",
        marker=dict(size=11, color=mcolors, line=dict(color="#e8d5b7",width=1.5)),
        line=dict(color="#e8d5b7",width=1,dash="dot"),
        hovertemplate="<b>%{customdata[0]}</b><br>평균기온: %{y:.1f}℃<br>평년대비: %{customdata[1]}<extra></extra>",
        customdata=[[r["학년도"], f"{r['평년대비']:+.1f}℃" if r["평년대비"] is not None else "—"]
                    for _,r in sdf.iterrows()],
    ))
    fig_s.add_hline(y=sdf["평균기온"].mean(), line_dash="dash", line_color="#f39c12",
        annotation_text=f"수능 평균 {sdf['평균기온'].mean():.1f}℃",
        annotation_font_color="#f39c12")
    fig_s.add_hline(y=0, line_dash="dot", line_color="#5a7a9a", line_width=1)
    fig_s.update_layout(height=440, hovermode="x unified", **_DARK)
    fig_s.update_layout(xaxis=dict(showgrid=False, title="시행연도"), yaxis_title="기온 (℃)")
    st.plotly_chart(fig_s, use_container_width=True)
    st.caption("마커 색상: 🔴 평년보다 3℃+ 따뜻  🟡 평년과 유사  🔵 평년보다 3℃+ 추움  │ 범위 막대 = 최저~최고기온")

    # 차트 2: 평년 대비 편차
    st.markdown("#### 📉 수능 당일 평년 대비 기온 편차 (직전 30년 같은 날 평균 기준)")
    sdf_nn = sdf.dropna(subset=["평년대비"])
    fig_s2 = go.Figure(go.Bar(
        x=sdf_nn["시행연도"], y=sdf_nn["평년대비"],
        marker_color=["#e74c3c" if v>=0 else "#3498db" for v in sdf_nn["평년대비"]],
        text=[f"{v:+.1f}℃" for v in sdf_nn["평년대비"]],
        textposition="outside", textfont=dict(size=9,color="#e8d5b7"),
        hovertemplate="<b>%{customdata}</b><br>편차: %{y:+.1f}℃<extra></extra>",
        customdata=sdf_nn["학년도"],
    ))
    fig_s2.add_hline(y=0,line_dash="dot",line_color="#e8d5b7")
    fig_s2.update_layout(height=330,plot_bgcolor="#0f1923",paper_bgcolor="#0f1923",
        font=dict(color="#8a9bb0"),
        xaxis=dict(showgrid=False,title="시행연도"),
        yaxis=dict(showgrid=True,gridcolor="#1e2e3e",title="편차 (℃)"),
        margin=dict(t=40,b=20))
    st.plotly_chart(fig_s2, use_container_width=True)

    # 표
    st.markdown("#### 📋 수능 날짜별 상세 기온")
    disp = sdf[["학년도","날짜","평균기온","최저기온","최고기온","일교차","평년대비","비고"]].copy()
    disp.columns = ["학년도","날짜","평균(℃)","최저(℃)","최고(℃)","일교차(℃)","평년대비(℃)","비고"]

    def style_row(row):
        v = row["평균(℃)"]
        if pd.isna(v): return [""]*len(row)
        if v < 3:  return ["background-color:rgba(52,100,180,0.25)"]*len(row)
        if v > 15: return ["background-color:rgba(220,80,60,0.25)"]*len(row)
        return [""]*len(row)

    st.dataframe(
        disp.style.apply(style_row, axis=1).format({
            "평균(℃)":"{:.1f}","최저(℃)":"{:.1f}","최고(℃)":"{:.1f}","일교차(℃)":"{:.1f}",
            "평년대비(℃)": lambda x: f"{x:+.1f}" if pd.notna(x) else "—",
        }),
        use_container_width=True, height=620,
    )
    st.caption("🔵 파란 행: 평균기온 3℃ 미만(수능 한파)  🔴 붉은 행: 평균기온 15℃ 이상(이상 고온)")
    csv_s = disp.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ 수능 기온 데이터 다운로드", data=csv_s,
        file_name="suneung_temp.csv", mime="text/csv")

# ──────────────────────────────────────────────
# TAB 6 — 원본
# ──────────────────────────────────────────────
with tab6:
    st.subheader("📋 원본 데이터")
    yr_sel = st.selectbox("연도", sorted(fdf["연도"].unique(), reverse=True))
    vdf = fdf[fdf["연도"]==yr_sel][["날짜","지점","평균기온","최저기온","최고기온"]]
    st.dataframe(vdf.reset_index(drop=True), use_container_width=True, height=500)
    st.download_button("⬇️ 다운로드", vdf.to_csv(index=False,encoding="utf-8-sig"),
        file_name=f"temp_{yr_sel}.csv", mime="text/csv")
