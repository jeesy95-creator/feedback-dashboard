import os
import re
from collections import defaultdict

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")  # 헤드리스 서버에서 GUI 백엔드 요청 방지 — wordcloud 임포트 전에 설정해야 함
import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(page_title="고객 피드백 대시보드", layout="wide", page_icon="☕")

# ── 데이터 로드 ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "Day3_과제_feedback_정리.csv"))

df["별점_num"] = pd.to_numeric(df["별점"], errors="coerce")

def derive_sentiment(row):
    if str(row["감정"]) not in ["-", "", "nan"]:
        return row["감정"]
    score = row["별점_num"]
    if pd.isna(score):
        return "중립"
    return "긍정" if score >= 4 else ("중립" if score == 3 else "부정")

df["감정_전체"] = df.apply(derive_sentiment, axis=1)

date_min = df["받은날짜"].min()
date_max = df["받은날짜"].max()

# ── 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f8f9fa; border-radius: 10px;
    padding: 12px 18px; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center; font-size: 15px;
}
.metric-value { font-size: 22px; font-weight: 700; }
.complaint-card {
    padding: 12px 16px; margin-bottom: 10px;
    border-radius: 6px; background: #fafafa; font-size: 14px; line-height: 1.6;
}
.footer-text { text-align: center; color: #999; font-size: 13px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("☕ 고객 피드백 대시보드")
st.markdown("---")

# ── 상단: 유형별 개수 | 급한 불만 TOP 3 ─────────────────────
col_left, col_right = st.columns([1, 2])

TYPE_META = {
    "불만": ("🔴", "#F44336"),
    "문의": ("🔵", "#2196F3"),
    "칭찬": ("🟢", "#4CAF50"),
    "요청": ("🟡", "#FF9800"),
}

with col_left:
    st.subheader("📊 유형별 개수")
    type_counts = df["유형"].value_counts()
    for label, (icon, color) in TYPE_META.items():
        count = type_counts.get(label, 0)
        st.markdown(f"""
        <div class="metric-card">
            <span>{icon} <b>{label}</b></span>
            <span class="metric-value" style="color:{color}">{count}</span>
        </div>""", unsafe_allow_html=True)

with col_right:
    st.subheader("🚨 가장 급한 불만 TOP 3")
    complaints = (
        df[df["유형"] == "불만"]
        .sort_values("별점_num", ascending=True, na_position="last")
        .head(3)
        .reset_index(drop=True)
    )
    border_colors = ["#F44336", "#FF9800", "#FFC107"]
    for i, row in complaints.iterrows():
        rating_str = f"★ {int(row['별점_num'])}/5" if pd.notna(row["별점_num"]) else "별점 없음"
        st.markdown(f"""
        <div class="complaint-card" style="border-left: 5px solid {border_colors[i]};">
            <b>TOP {i+1}</b> &nbsp;
            <span style="color:#888; font-size:13px">{rating_str} · {row['경로']}</span><br>
            {row['내용']}
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── 중앙: 감정 분포 | 평균 별점 | 유형 바 그래프 ──────────────
col_a, col_b, col_c = st.columns(3)

SENTIMENT_COLORS = {"긍정": "#4CAF50", "중립": "#FFC107", "부정": "#F44336"}

with col_a:
    st.subheader("😊 감정 분포")
    sent = df["감정_전체"].value_counts().reset_index()
    sent.columns = ["감정", "개수"]
    fig_pie = px.pie(
        sent, values="개수", names="감정",
        color="감정", color_discrete_map=SENTIMENT_COLORS, hole=0.38,
    )
    fig_pie.update_traces(textinfo="percent+label", textfont_size=13)
    fig_pie.update_layout(
        margin=dict(t=10, b=30, l=10, r=10),
        legend=dict(orientation="h", y=-0.12),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("⭐ 평균 별점")
    avg = round(df["별점_num"].mean(), 2)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=avg,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"suffix": " / 5", "font": {"size": 30}, "valueformat": ".2f"},
        gauge={
            "axis": {"range": [1, 5], "tickwidth": 1, "tickvals": [1, 2, 3, 4, 5]},
            "bar": {"color": "#FF9800", "thickness": 0.28},
            "bgcolor": "white",
            "steps": [
                {"range": [1, 2.5], "color": "#FFCDD2"},
                {"range": [2.5, 3.5], "color": "#FFF9C4"},
                {"range": [3.5, 5],   "color": "#C8E6C9"},
            ],
            "threshold": {"line": {"color": "#333", "width": 4}, "thickness": 0.8, "value": avg},
        },
    ))
    fig_gauge.update_layout(height=290, margin=dict(t=20, b=10, l=30, r=30))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_c:
    st.subheader("📋 유형별 분포")
    type_bar = df["유형"].value_counts().reset_index()
    type_bar.columns = ["유형", "개수"]
    fig_bar = px.bar(
        type_bar, x="유형", y="개수",
        color="유형", color_discrete_map={k: v[1] for k, v in TYPE_META.items()},
        text="개수",
    )
    fig_bar.update_traces(textposition="outside", textfont_size=14)
    fig_bar.update_layout(
        showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(showgrid=True, gridcolor="#eee", title=""),
        xaxis=dict(title=""), plot_bgcolor="white", height=290,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── 워드클라우드 ─────────────────────────────────────────────
st.markdown("---")
st.subheader("☁️ 긍정 / 부정 워드클라우드")

# 불용어 (의미 없는 단어)
STOPWORDS = {
    '너무', '정말', '아주', '좀', '더', '자꾸', '자주', '항상', '완전', '진짜',
    '그냥', '이미', '것', '수', '때', '두', '세', '한', '또', '및',
    '나', '내', '우리', '저', '제', '이것', '저것', '그것', '그것도',
    '이런', '저런', '그런', '이번', '지난', '다음', '여기', '저기', '거기',
    '그리고', '하지만', '그런데', '그래도', '또한', '조금', '많이', '같이',
    '이상', '정도', '어디', '어떻게', '왜', '무엇', '분', '시간',
    '있어요', '없어요', '이에요', '예요', '에요', '해요', '됩니다', '합니다',
    '됐어요', '겠어요', '있나요', '되나요', '않나요', '이라고', '으면',
    '있으면', '없으면', '해주셔서', '해주세요', '드려요', '부탁드려요',
    '찾으러', '가도', '될까요', '싶어요', '올렸어요',
    '좋겠어요',  # 희망 표현 — 행 감정에 따라 색이 달라져 오분류됨
    '직원',      # 중립 명사 — 칭찬/불만 맥락 모두 등장
    # 동사 활용형 잔재
    '됐는데', '받았어요', '시켰는데', '쓰려는데', '주문하고',
    '번이나요', '울려서', '나왔으면', '많아서', '조금만',
    '가능하게', '앱에서', '인스타에', '확인',
}

# 카페 도메인 주제 명사 — 감정 없이 회색으로 표시
TOPIC_NOUNS = {
    '음료', '케이크', '라떼', '라떼아트', '아메리카노', '당도',
    '매장', '자리', '콘센트', '와이파이', '진동벨', '기프티콘',
    '카공하기', '주문', '결제', '포인트', '메뉴', '시즌', '한정',
    '강아지', '동반', '가격', '신메뉴', '옵션', '조절', '앱',
}

# 조사 제거 (긴 것부터 순서대로)
PARTICLES = sorted([
    '분들도', '분들이', '분들을', '분들은',
    '이라고', '이라면', '이라도',
    '에서도', '에서', '에도', '에게', '으로', '처럼',
    '이나', '이고', '이며',
    '이에요', '예요', '에요',
    '이', '가', '을', '를', '은', '는', '도', '와', '과', '의', '로',
], key=len, reverse=True)

# 자연스러운 단어로 정규화
NORMALIZE = {
    '맛있어요': '맛있음', '맛있는': '맛있음',
    '깨끗해서': '깨끗',   '친절하세요': '친절',
    '달아요': '달달',     '좁아요': '좁음',
    '불편해요': '불편',   '끊겨요': '와이파이끊김',
    '식었어요': '식음',   '기다렸어요': '대기',
    '올랐네요': '가격인상', '걸려요': '대기시간',
    '부담스러워요': '부담', '완벽해요': '완벽',
    '감사해요': '감사',   '예뻐서': '예쁨',
    '잘못': '주문오류',   '쌓였어요': '포인트오류',
}

def strip_particle(token):
    for p in PARTICLES:
        if token.endswith(p) and len(token) - len(p) >= 2:
            return token[:-len(p)]
    return token

def extract_words(text):
    text_kr = re.sub(r'[^가-힣\s]', ' ', str(text))
    result = []
    for token in text_kr.split():
        token = NORMALIZE.get(token, token)
        word = strip_particle(token)
        if len(word) >= 2 and word not in STOPWORDS:
            result.append(word)
    return result

# 긍정·부정 단어 빈도 계산
pos_freq: dict = defaultdict(int)
neg_freq: dict = defaultdict(int)

for _, row in df.iterrows():
    s = row["감정_전체"]
    if s == "중립":
        continue
    for word in extract_words(row["내용"]):
        (pos_freq if s == "긍정" else neg_freq)[word] += 1

# 단어별 감정·빈도 확정 (겹치면 빈도 높은 쪽으로)
word_meta: dict = {}
for word in set(pos_freq) | set(neg_freq):
    p, n = pos_freq.get(word, 0), neg_freq.get(word, 0)
    word_meta[word] = ("pos", p) if p >= n else ("neg", n)

word_freq = {w: max(pos_freq.get(w, 0), neg_freq.get(w, 0)) for w in word_meta}

# 색상 스케일: 강도 1(연) → 5(진)
GREEN = ["#C8E6C9", "#81C784", "#4CAF50", "#2E7D32", "#1B5E20"]
RED   = ["#FFCDD2", "#EF9A9A", "#F44336", "#C62828", "#B71C1C"]

pos_max = max((v for _, (s, v) in word_meta.items() if s == "pos"), default=1)
neg_max = max((v for _, (s, v) in word_meta.items() if s == "neg"), default=1)

def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    if word in TOPIC_NOUNS:
        return "#BDBDBD"  # 회색: 감정 없는 주제 명사
    if word not in word_meta:
        return "#aaaaaa"
    sentiment, freq = word_meta[word]
    max_f = pos_max if sentiment == "pos" else neg_max
    level = round((freq - 1) / max(max_f - 1, 1) * 4)   # 0~4 → 인덱스
    return GREEN[level] if sentiment == "pos" else RED[level]

FONT_PATH = next(
    (p for p in [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",    # Linux (Streamlit Cloud)
        "/Library/Fonts/NanumGothic.ttf",                      # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",          # macOS
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",  # macOS
    ] if os.path.exists(p)),
    None,
)

try:
    wc = WordCloud(
        width=1400, height=560,
        background_color="white",
        font_path=FONT_PATH,
        color_func=color_func,
        max_words=80,
        random_state=42,
        prefer_horizontal=0.65,
        min_font_size=12,
        max_font_size=120,
        collocations=False,
    ).generate_from_frequencies(word_freq)

    fig_wc, ax_wc = plt.subplots(figsize=(14, 5.5))
    ax_wc.imshow(wc, interpolation="bilinear")
    ax_wc.axis("off")
    plt.tight_layout(pad=0)
    st.pyplot(fig_wc)
    plt.close(fig_wc)
except Exception as e:
    st.warning(f"워드클라우드 생성 실패: {e}")

# 강도 범례
st.markdown("<br>", unsafe_allow_html=True)
lcol, mcol, rcol = st.columns(3)

def legend_html(colors, start_dark_idx):
    return " ".join([
        f'<span style="background:{c};color:{"#444" if i < start_dark_idx else "white"};'
        f'padding:4px 16px;border-radius:4px;margin-right:4px;font-size:13px">강도 {i+1}</span>'
        for i, c in enumerate(colors)
    ])

with lcol:
    st.markdown(f"🟢 **긍정 단어** &nbsp;&nbsp; {legend_html(GREEN, 2)}", unsafe_allow_html=True)
with mcol:
    st.markdown(f"🔴 **부정 단어** &nbsp;&nbsp; {legend_html(RED, 2)}", unsafe_allow_html=True)
with rcol:
    st.markdown(
        '<span style="background:#BDBDBD;color:#333;padding:4px 16px;'
        'border-radius:4px;font-size:13px">주제어</span>'
        '&nbsp; ⬜ <b>회색: 주제 명사</b> — 감정 중립 (음료·케이크·와이파이 등)',
        unsafe_allow_html=True,
    )

# ── 하단: 데이터 기간 안내 ────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<p class="footer-text">본 데이터는 {date_min} ~ {date_max} 까지의 데이터입니다</p>',
    unsafe_allow_html=True,
)
