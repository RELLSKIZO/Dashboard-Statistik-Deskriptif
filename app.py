from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Statistik Deskriptif Mahasiswa", page_icon="📊", layout="wide")

LABEL = {"Age": "Umur", "Study_Hours": "Jam belajar", "Sleep_Hours": "Jam tidur", "Attendance": "Kehadiran (%)",
         "Exam_Score": "Nilai ujian", "Monthly_Spending": "Pengeluaran bulanan", "Screen_Hours": "Jam layar",
         "Satisfaction": "Kepuasan (1-10)"}
PEACH, MINT, LINE = "#ff9f7a", "#7fe0c3", "#34283f"
GC = {"F": "#e58bd0", "M": "#6ec5ff"}
GN = {"F": "Perempuan", "M": "Laki-laki"}


@st.cache_data
def load():
    return pd.read_csv(Path(__file__).parent / "data" / "latihan1.csv")


def fmt(x, d=2):
    s = f"{x:,.{d}f}".rstrip("0").rstrip(".") if d else f"{x:,.0f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def style(fig, h=380):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=10, r=10, t=30, b=10), font=dict(color="#f4ece8"))
    fig.update_xaxes(gridcolor=LINE)
    fig.update_yaxes(gridcolor=LINE)
    return fig


def describe(s):
    q1, q3 = s.quantile([.25, .75])
    iqr = q3 - q1
    return {"Mean": s.mean(), "Median": s.median(), "Modus": s.mode().iloc[0], "Std Dev": s.std(), "Variansi": s.var(),
            "Min": s.min(), "Q1": q1, "Q3": q3, "Maks": s.max(), "Range": s.max() - s.min(), "IQR": iqr,
            "Skewness": s.skew(), "Kurtosis": s.kurt(), "CV %": s.std() / s.mean() * 100,
            "Outlier": int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())}


full = load()
NUM = [c for c in full.columns if c not in ("Student_ID", "Gender")]
opt = dict(options=NUM, format_func=LABEL.get)

with st.sidebar:
    st.title("Statistik Deskriptif Mahasiswa")
    st.caption("Sumber: latihan1.csv")
    pick = st.radio("Filter data", ["Semua mahasiswa", "Perempuan", "Laki-laki"])
st.markdown("<style>[data-testid=stMetricValue]{font-size:1.6rem}[data-testid^=stMetricDeltaIcon]{display:none}</style>", unsafe_allow_html=True)
df = full if pick.startswith("Semua") else full[full.Gender == ("F" if pick == "Perempuan" else "M")]

# ---- Ringkasan
a, b, c, d = st.columns(4)
a.metric("Total mahasiswa", len(df), f"P {(df.Gender == 'F').sum()}, L {(df.Gender == 'M').sum()}", delta_color="off")
b.metric("Rentang nilai ujian", f"{fmt(df.Exam_Score.min(), 0)} - {fmt(df.Exam_Score.max(), 0)}")
c.metric("Rata-rata nilai ujian", fmt(df.Exam_Score.mean()), f"median {fmt(df.Exam_Score.median())}", delta_color="off")
d.metric("Rata-rata jam belajar", fmt(df.Study_Hours.mean()), f"median {fmt(df.Study_Hours.median())}", delta_color="off")

# ---- Satu variabel
st.subheader("Jelajahi satu variabel")
var = st.selectbox("Variabel", index=NUM.index("Exam_Score"), **opt)
st_ = describe(df[var])
left, right = st.columns([1.7, 1])
fig = px.histogram(df, x=var, nbins=max(5, int(np.log2(len(df))) + 1), marginal="box", color_discrete_sequence=[PEACH])
fig.add_vline(x=st_["Mean"], line_color=MINT, annotation_text="Mean", row=1, col=1)
fig.add_vline(x=st_["Median"], line_color="#f3e9dc", line_dash="dash", annotation_text="Median", annotation_position="bottom", row=1, col=1)
left.plotly_chart(style(fig, 420))
keys = ["Mean", "Median", "Modus", "Std Dev", "Variansi", "Range", "Q1", "Q3", "IQR", "Skewness", "CV %", "Outlier"]
for i in range(0, 12, 3):
    for col, k in zip(right.columns(3), keys[i:i + 3]):
        col.metric(k, fmt(st_[k], 0 if k == "Outlier" else 2))
sk = st_["Skewness"]
right.caption(f"Bentuk: {'simetris' if abs(sk) < .5 else 'condong kanan' if sk > 0 else 'condong kiri'}; "
              f"kurtosis {fmt(st_['Kurtosis'])} ({'lebih datar dari normal' if st_['Kurtosis'] < -.5 else 'lebih runcing dari normal' if st_['Kurtosis'] > .5 else 'mirip normal'}).")

# ---- Gender dan hubungan
g1, g2 = st.columns([1, 1.25])
with g1:
    st.subheader("Komposisi gender dan rata-rata")
    gv = st.selectbox("Variabel pembanding", index=NUM.index("Exam_Score"), key="gv", **opt)
    pie = px.pie(full, names=full.Gender.map(GN), hole=.6, color=full.Gender.map(GN),
                 color_discrete_map={GN[k]: v for k, v in GC.items()})
    bar = full.groupby("Gender")[gv].mean().reset_index()
    bar["Gender"] = bar.Gender.map(GN)
    bar_fig = px.bar(bar, x="Gender", y=gv, color="Gender", text_auto=".2f", color_discrete_map={GN[k]: v for k, v in GC.items()})
    p, q = st.columns(2)
    p.plotly_chart(style(pie, 300))
    q.plotly_chart(style(bar_fig, 300))
    st.caption("Bagian ini selalu memakai seluruh data dan tidak terpengaruh filter.")
with g2:
    st.subheader("Hubungan dua variabel")
    sx, sy = st.columns(2)
    x = sx.selectbox("Sumbu X", index=NUM.index("Study_Hours"), key="x", **opt)
    y = sy.selectbox("Sumbu Y", index=NUM.index("Exam_Score"), key="y", **opt)
    if x == y:
        st.warning("Pilih dua variabel yang berbeda.")
    else:
        sc = px.scatter(df, x=x, y=y, color=df.Gender.map(GN), labels={x: LABEL[x], y: LABEL[y], "color": "Gender"},
                        color_discrete_map={GN[k]: v for k, v in GC.items()})
        m, k0 = np.polyfit(df[x], df[y], 1)
        xs = np.array([df[x].min(), df[x].max()])
        sc.add_trace(go.Scatter(x=xs, y=m * xs + k0, mode="lines", line=dict(color="#f3e9dc", dash="dash"), name="Regresi"))
        st.plotly_chart(style(sc, 340))
        r = df[x].corr(df[y])
        st.caption(f"r = {fmt(r)}; R² = {fmt(r * r)}. {LABEL[y]} = {fmt(k0)} {'-' if m < 0 else '+'} {fmt(abs(m))} x {LABEL[x].lower()}.")

# ---- Korelasi dan tabel
st.subheader("Matriks korelasi Pearson")
corr = df[NUM].corr().rename(index=LABEL, columns=LABEL)
hm = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale=[[0, "#6ec5ff"], [.5, "#1c1526"], [1, PEACH]])
st.plotly_chart(style(hm, 520))

st.subheader("Tabel ringkasan statistik")
table = pd.DataFrame({LABEL[c]: describe(df[c]) for c in NUM}).T.round(2)
st.dataframe(table)
