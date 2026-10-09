# -*- coding: utf-8 -*-
"""
منصة التحليلات الذكية الشاملة  |  Ultimate Streamlit Analytics Dashboard
تشغيل:   streamlit run app.py
المتطلبات: pip install streamlit pandas plotly openpyxl numpy
"""
import io
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ───────────────────────── 1. إعدادات الصفحة والتصميم ─────────────────────────
st.set_page_config(page_title="منصة التحليلات الذكية", page_icon="🌐", layout="wide")

ACCENT = "#00f2fe"
TEMPLATE = "plotly_dark"
PALETTE = px.colors.qualitative.Bold

st.markdown(
    f"""
<style>
    .stApp {{ background-color: #0e1117; }}
    .main-header {{ font-size: 38px; font-weight: 800; color: {ACCENT}; text-align: center; margin-bottom: 4px; }}
    .sub-header {{ font-size: 18px; color: #a8b2c1; text-align: center; margin-bottom: 24px; }}
    div[data-testid="metric-container"] {{
        background-color: #1e2633; border-left: 5px solid {ACCENT};
        padding: 14px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,.5);
    }}
    .insight {{ background:#1a2230; border-right:4px solid {ACCENT}; padding:10px 14px;
               border-radius:8px; margin-bottom:8px; color:#dbe4f0; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; flex-wrap: wrap; }}
    .stTabs [data-baseweb="tab"] {{ background:#1e2633; border-radius:8px 8px 0 0; padding:8px 14px; }}
</style>
""",
    unsafe_allow_html=True,
)

AGGS = {"مجموع": "sum", "متوسط": "mean", "وسيط": "median", "عدد": "count", "أقصى": "max", "أدنى": "min"}
FREQS = {"يومي": "D", "أسبوعي": "W", "شهري": "MS", "ربع سنوي": "QS", "سنوي": "YS"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ───────────────────────── 2. دوال مساعدة ─────────────────────────
def show(fig, height=None):
    """رسم Plotly متوافق مع كل إصدارات Streamlit."""
    fig.update_layout(template=TEMPLATE, margin=dict(l=10, r=10, t=50, b=10),
                      colorway=PALETTE, legend_title_text="")
    if height:
        fig.update_layout(height=height)
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def show_df(d, **kw):
    try:
        st.dataframe(d, width="stretch", **kw)
    except TypeError:
        st.dataframe(d, use_container_width=True, **kw)


def fmt(v):
    """تنسيق الأرقام الكبيرة (K / M / B)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    a = abs(v)
    for lim, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= lim:
            return f"{v / lim:,.2f}{s}"
    return f"{v:,.2f}" if isinstance(v, (float, np.floating)) and v != int(v) else f"{int(v):,}"


def agg_frame(d, by, val, agg):
    """تجميع موحّد: by قائمة أعمدة، val عمود القيمة، agg اسم الدالة."""
    by = [by] if isinstance(by, str) else list(by)
    if _as_count(by, val, agg):
        return d.groupby(by, dropna=False).size().reset_index(name="عدد")
    return d.groupby(by, dropna=False)[val].agg(agg).reset_index()


def _as_count(by, val, agg):
    by = [by] if isinstance(by, str) else list(by)
    return agg == "count" or val is None or val in by


def vcol(frame, by, val, agg):
    return "عدد" if _as_count(by, val, agg) else val


def to_excel_bytes(d):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        d.to_excel(w, index=False, sheet_name="Data")
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def make_sample():
    """بيانات تجريبية: مبيعات سيارات لعلامة بفروع متعددة."""
    rng = np.random.default_rng(42)
    n = 1500
    branches = [("مدينة نصر", "القاهرة"), ("التجمع الخامس", "القاهرة"), ("6 أكتوبر", "الجيزة"),
                ("سموحة", "الإسكندرية"), ("المنصورة", "الدقهلية"), ("طنطا", "الغربية"),
                ("الزقازيق", "الشرقية"), ("الغردقة", "البحر الأحمر"), ("أسيوط", "أسيوط")]
    models = {"Falcon S": 650_000, "Falcon X SUV": 980_000, "Orion Hatch": 520_000,
              "Orion Sedan": 590_000, "Atlas Crossover": 1_150_000, "Nova Compact": 430_000}
    b = rng.choice(len(branches), n, p=np.array([1.5, 1.6, 1.3, 1.2, .8, .7, .6, .5, .5]) / 8.7)
    m = rng.choice(list(models), n)
    price = np.array([models[x] for x in m]) * rng.normal(1, .04, n)
    pay = np.where(rng.random(n) < 0.58, "تقسيط", "كاش")
    disc = np.where(pay == "كاش", rng.uniform(.02, .08, n), rng.uniform(0, .03, n)) * price
    down = np.where(pay == "تقسيط", price * rng.uniform(.1, .4, n), price)
    dates = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 640, n), unit="D")
    df = pd.DataFrame({
        "تاريخ البيع": dates, "الموديل": m,
        "الفرع": [branches[i][0] for i in b], "المحافظة": [branches[i][1] for i in b],
        "طريقة الدفع": pay, "سعر البيع": price.round(0), "الخصم": disc.round(0),
        "الدفعة المقدمة": down.round(0), "عمر العميل": rng.integers(22, 66, n),
        "تقييم العميل": rng.integers(1, 6, n),
        "عدد السيارات": rng.integers(1, 3, n),
    }).sort_values("تاريخ البيع").reset_index(drop=True)
    df["صافي الإيراد"] = (df["سعر البيع"] - df["الخصم"]) * df["عدد السيارات"]
    return df


@st.cache_data(show_spinner="جاري قراءة الملف...")
def load_file(raw: bytes, name: str, sheet):
    if name.lower().endswith(".csv"):
        for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=enc)
            except Exception:
                continue
        raise ValueError("تعذّر قراءة ملف CSV")
    return pd.read_excel(io.BytesIO(raw), sheet_name=sheet, engine="openpyxl")


@st.cache_data(show_spinner=False)
def sheet_names(raw: bytes):
    return pd.ExcelFile(io.BytesIO(raw), engine="openpyxl").sheet_names


@st.cache_data(show_spinner="جاري تجهيز البيانات...")
def prepare(df: pd.DataFrame):
    """تنظيف + اكتشاف أنواع الأعمدة (رقمي / تاريخ / فئوي / نصي)."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all").dropna(axis=1, how="all")
    for c in df.columns:
        if df[c].dtype == object:
            s = df[c].dropna()
            if s.empty:
                continue
            smp = s.astype(str).head(300)
            num = pd.to_numeric(smp.str.replace(",", "", regex=False), errors="coerce")
            if num.notna().mean() >= 0.95:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
                continue
            try:
                dt = pd.to_datetime(smp, errors="coerce", format="mixed")
            except Exception:
                dt = pd.Series(pd.NaT, index=smp.index)
            if dt.notna().mean() >= 0.9 and smp.str.contains(r"[-/:]").mean() > .8:
                df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed")
    num = df.select_dtypes(include=["number"]).columns.tolist()
    dates = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    cat, text = [], []
    for c in df.columns:
        if c in num or c in dates:
            continue
        nun = df[c].nunique(dropna=True)
        (cat if nun <= 60 or nun <= 0.2 * len(df) else text).append(c)
    # أعمدة رقمية قليلة القيم المميزة تصلح للتجميع أيضاً (مثل التقييم 1-5)
    low_num = [c for c in num if df[c].nunique() <= 12 and (df[c].dropna() % 1 == 0).all()]
    return df, num, dates, cat, text, low_num


# ───────────────────────── 3. رأس الصفحة + مصدر البيانات ─────────────────────────
st.markdown('<div class="main-header">🌐 منصة التحليلات الذكية الشاملة</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ارفع ملف بياناتك (Excel / CSV) واحصل على تحليل كامل: مؤشرات، فئات، زمن، علاقات، توزيعات، '
            'قيم شاذة، وجداول محورية — كلها تفاعلية</div>', unsafe_allow_html=True)

st.sidebar.header("📂 مصدر البيانات")
up = st.sidebar.file_uploader("ارفع الملف", type=["xlsx", "xls", "csv"])
use_sample = st.sidebar.checkbox("استخدام بيانات تجريبية (مبيعات سيارات)", value=False)

raw_df = None
src_name = ""
if up is not None:
    try:
        raw = up.getvalue()
        sheet = 0
        if not up.name.lower().endswith(".csv"):
            names = sheet_names(raw)
            if len(names) > 1:
                sheet = st.sidebar.selectbox("الشيت:", names)
        raw_df = load_file(raw, up.name, sheet)
        src_name = up.name
    except Exception as e:
        st.error(f"تعذّر قراءة الملف: {e}")
        st.stop()
elif use_sample:
    raw_df, src_name = make_sample(), "بيانات تجريبية"

if raw_df is None:
    st.info("👈 ارفع ملفك من القائمة الجانبية، أو فعّل «البيانات التجريبية» لتجربة اللوحة. "
            "اللوحة تتكيّف تلقائياً مع أي أعمدة في ملفك.")
    st.stop()

df, num_cols, date_cols, cat_cols, text_cols, low_num = prepare(raw_df)
if df.empty:
    st.error("الملف لا يحتوي على بيانات صالحة.")
    st.stop()
group_cols = cat_cols + [c for c in low_num if c not in cat_cols]

# ───────────────────────── 4. الفلاتر ─────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("🔍 الفلاتر")
mask = pd.Series(True, index=df.index)

if date_cols:
    dcol_f = st.sidebar.selectbox("فلتر التاريخ حسب:", date_cols, key="f_date_col")
    dmin, dmax = df[dcol_f].min(), df[dcol_f].max()
    if pd.notna(dmin) and dmin != dmax:
        rng = st.sidebar.date_input("الفترة:", (dmin.date(), dmax.date()),
                                    min_value=dmin.date(), max_value=dmax.date(), key="f_date")
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            mask &= df[dcol_f].between(pd.Timestamp(rng[0]), pd.Timestamp(rng[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)) \
                    | df[dcol_f].isna()

filter_cats = [c for c in cat_cols if df[c].nunique() <= 60]
if filter_cats:
    with st.sidebar.expander("فلاتر الأعمدة الفئوية", expanded=True):
        for c in filter_cats[:8]:
            vals = sorted(df[c].dropna().astype(str).unique().tolist())
            sel = st.multiselect(c, vals, default=vals, key=f"f_cat_{c}")
            if len(sel) != len(vals):
                mask &= df[c].astype(str).isin(sel)

if num_cols:
    with st.sidebar.expander("فلاتر الأعمدة الرقمية"):
        pick = st.multiselect("اختر أعمدة للفلترة بالمدى:", num_cols, key="f_num_pick")
        for c in pick:
            lo, hi = float(df[c].min()), float(df[c].max())
            if lo < hi:
                a, b = st.slider(c, lo, hi, (lo, hi), key=f"f_num_{c}")
                mask &= df[c].between(a, b) | df[c].isna()

dff = df[mask].copy()
st.sidebar.success(f"الصفوف بعد الفلترة: {len(dff):,} من {len(df):,}")
if dff.empty:
    st.warning("لا توجد بيانات مطابقة للفلاتر الحالية. خفّف الفلاتر من القائمة الجانبية.")
    st.stop()

# ───────────────────────── 5. مؤشرات الأداء ─────────────────────────
st.markdown(f"### 📊 مؤشرات الأداء — {src_name}")
measure = None
if num_cols:
    measure = st.selectbox("العمود الرقمي الرئيسي للمؤشرات:", num_cols, key="kpi_measure")

k = st.columns(6)
k[0].metric("عدد الصفوف", f"{len(dff):,}")
k[1].metric("عدد الأعمدة", f"{dff.shape[1]}")
k[2].metric("القيم المفقودة", f"{dff.isna().mean().mean() * 100:.1f}%")
k[3].metric("صفوف مكررة", f"{dff.duplicated().sum():,}")
if measure:
    k[4].metric(f"إجمالي {measure}", fmt(dff[measure].sum()))
    k[5].metric(f"متوسط {measure}", fmt(dff[measure].mean()))
    k2 = st.columns(4)
    k2[0].metric("الوسيط", fmt(dff[measure].median()))
    k2[1].metric("الأقصى", fmt(dff[measure].max()))
    k2[2].metric("الأدنى", fmt(dff[measure].min()))
    k2[3].metric("الانحراف المعياري", fmt(dff[measure].std()))
st.markdown("---")

# ───────────────────────── 6. التبويبات ─────────────────────────
tabs = st.tabs(["🧭 نظرة عامة", "📊 الفئات والمقارنات", "📈 التحليل الزمني", "🔗 العلاقات والارتباط",
                "📦 التوزيع والقيم الشاذة", "🧮 جداول محورية وترتيب", "🎨 منشئ رسوم حر", "📋 البيانات"])

# ===== 6.1 نظرة عامة =====
with tabs[0]:
    st.markdown("#### 💡 رؤى تلقائية")
    ins = []
    ins.append(f"البيانات تحتوي على <b>{len(dff):,}</b> صف و<b>{dff.shape[1]}</b> عمود "
               f"({len(num_cols)} رقمي، {len(group_cols)} فئوي، {len(date_cols)} تاريخ).")
    miss = dff.isna().mean().sort_values(ascending=False)
    if miss.iloc[0] > 0:
        ins.append(f"أكثر عمود فيه قيم مفقودة: <b>{miss.index[0]}</b> بنسبة {miss.iloc[0] * 100:.1f}%.")
    if measure and cat_cols:
        c0 = cat_cols[0]
        g = dff.groupby(c0)[measure].sum().sort_values(ascending=False)
        if len(g) and g.sum() != 0:
            ins.append(f"أعلى فئة في <b>{c0}</b> من حيث {measure}: <b>{g.index[0]}</b> بنسبة {g.iloc[0] / g.sum() * 100:.1f}% من الإجمالي.")
    if len(num_cols) >= 2:
        cfull = dff[num_cols].corr()
        arr = cfull.abs().to_numpy(copy=True)
        np.fill_diagonal(arr, 0)
        if np.nanmax(arr) > 0:
            a, b = np.unravel_index(np.nanargmax(arr), arr.shape)
            ins.append(f"أقوى ارتباط بين <b>{cfull.index[a]}</b> و<b>{cfull.columns[b]}</b> "
                       f"(معامل {cfull.iloc[a, b]:.2f}).")
    if measure:
        q1, q3 = dff[measure].quantile([.25, .75])
        iqr = q3 - q1
        n_out = int(((dff[measure] < q1 - 1.5 * iqr) | (dff[measure] > q3 + 1.5 * iqr)).sum())
        ins.append(f"عدد القيم الشاذة في <b>{measure}</b> (IQR): <b>{n_out:,}</b>.")
    if date_cols and measure:
        d0 = date_cols[0]
        s = dff.dropna(subset=[d0]).set_index(d0)[measure].resample("MS").sum()
        if len(s) >= 2 and s.iloc[-2] != 0:
            ch = (s.iloc[-1] / s.iloc[-2] - 1) * 100
            ins.append(f"آخر شهر مقابل السابق في {measure}: <b>{ch:+.1f}%</b>.")
    for t in ins:
        st.markdown(f'<div class="insight">{t}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🧬 أنواع الأعمدة")
        info = pd.DataFrame({"العمود": dff.columns, "النوع": dff.dtypes.astype(str).values,
                             "قيم مميزة": [dff[c].nunique() for c in dff.columns],
                             "مفقود %": (dff.isna().mean().values * 100).round(1)})
        show_df(info, hide_index=True)
    with c2:
        st.markdown("#### 🕳️ القيم المفقودة")
        m = (dff.isna().mean() * 100).round(2).reset_index()
        m.columns = ["العمود", "نسبة المفقود %"]
        show(px.bar(m.sort_values("نسبة المفقود %"), x="نسبة المفقود %", y="العمود", orientation="h",
                    title="نسبة المفقود لكل عمود", color="نسبة المفقود %", color_continuous_scale="Reds"))
    if num_cols:
        st.markdown("#### 📐 إحصاءات وصفية")
        desc = dff[num_cols].describe().T
        desc["skew"] = dff[num_cols].skew()
        desc["مجموع"] = dff[num_cols].sum()
        show_df(desc.round(2))
    if cat_cols:
        st.markdown("#### 🏷️ ملخص الأعمدة الفئوية")
        show_df(pd.DataFrame({
            "العمود": cat_cols,
            "عدد الفئات": [dff[c].nunique() for c in cat_cols],
            "الأكثر تكراراً": [dff[c].mode().iloc[0] if not dff[c].mode().empty else "—" for c in cat_cols],
            "نسبته %": [round(dff[c].value_counts(normalize=True).iloc[0] * 100, 1) if dff[c].notna().any() else 0 for c in cat_cols],
        }), hide_index=True)

# ===== 6.2 الفئات والمقارنات =====
with tabs[1]:
    if not group_cols:
        st.info("لا توجد أعمدة فئوية في البيانات.")
    else:
        st.markdown("#### 📊 مقارنة الفئات")
        c1, c2, c3, c4 = st.columns(4)
        bx = c1.selectbox("الفئة:", group_cols, key="b_x")
        by_ = c2.selectbox("القيمة:", num_cols, key="b_y") if num_cols else None
        bag = c3.selectbox("الدالة:", list(AGGS), key="b_agg")
        topn = c4.slider("أعلى N:", 3, 50, 15, key="b_top")
        orient = st.radio("الاتجاه:", ["أفقي", "رأسي"], horizontal=True, key="b_or")
        bd = agg_frame(dff, bx, by_, AGGS[bag])
        vc = vcol(bd, bx, by_, AGGS[bag])
        bd = bd.sort_values(vc, ascending=False).head(topn)
        bd[bx] = bd[bx].astype(str)
        if orient == "أفقي":
            fig = px.bar(bd.sort_values(vc), y=bx, x=vc, orientation="h", color=vc, text_auto=".3s",
                         color_continuous_scale="Blues", title=f"{bag} {vc} حسب {bx}")
        else:
            fig = px.bar(bd, x=bx, y=vc, color=vc, text_auto=".3s", color_continuous_scale="Blues",
                         title=f"{bag} {vc} حسب {bx}")
        show(fig)

        r1, r2 = st.columns(2)
        with r1:
            pd_ = bd.copy()
            show(px.pie(pd_, names=bx, values=vc, hole=.45, title=f"نسبة كل فئة من {vc}"))
        with r2:
            show(px.treemap(pd_, path=[bx], values=vc, color=vc, color_continuous_scale="Teal",
                            title="خريطة شجرية (Treemap)"))

        st.markdown("#### 🏆 تحليل باريتو (80/20)")
        pa = agg_frame(dff, bx, by_, "sum" if by_ else "count")
        pv = vcol(pa, bx, by_, "sum" if by_ else "count")
        pa = pa.sort_values(pv, ascending=False).head(30)
        pa["تراكمي %"] = pa[pv].cumsum() / pa[pv].sum() * 100
        pa[bx] = pa[bx].astype(str)
        fp = go.Figure()
        fp.add_bar(x=pa[bx], y=pa[pv], name=pv, marker_color=ACCENT)
        fp.add_scatter(x=pa[bx], y=pa["تراكمي %"], name="تراكمي %", yaxis="y2", mode="lines+markers",
                       line=dict(color="#ff7a59"))
        fp.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="%"),
                         title=f"باريتو — {pv} حسب {bx}")
        show(fp)

        if len(group_cols) >= 2:
            st.markdown("#### 🔀 مقارنة بين فئتين")
            d1, d2 = st.columns(2)
            ca = d1.selectbox("الفئة الأولى:", group_cols, key="m_a")
            cb = d2.selectbox("الفئة الثانية:", [c for c in group_cols if c != ca], key="m_b")
            md = agg_frame(dff, [ca, cb], by_, AGGS[bag])
            mv = vcol(md, [ca, cb], by_, AGGS[bag])
            md[ca], md[cb] = md[ca].astype(str), md[cb].astype(str)
            kind = st.radio("نوع الرسم:", ["أعمدة مجمّعة", "أعمدة متراكمة", "متراكمة 100%", "خريطة حرارية", "Sunburst"],
                            horizontal=True, key="m_kind")
            if kind == "أعمدة مجمّعة":
                show(px.bar(md, x=ca, y=mv, color=cb, barmode="group", title=f"{mv}: {ca} × {cb}"))
            elif kind == "أعمدة متراكمة":
                show(px.bar(md, x=ca, y=mv, color=cb, barmode="stack", title=f"{mv}: {ca} × {cb}"))
            elif kind == "متراكمة 100%":
                show(px.bar(md, x=ca, y=mv, color=cb, barnorm="percent", title=f"التركيب النسبي: {ca} × {cb}"))
            elif kind == "خريطة حرارية":
                pv_ = md.pivot_table(index=ca, columns=cb, values=mv, aggfunc="sum", fill_value=0)
                show(px.imshow(pv_, text_auto=".3s", aspect="auto", color_continuous_scale="Viridis",
                               title=f"خريطة حرارية {ca} × {cb}"))
            else:
                show(px.sunburst(md, path=[ca, cb], values=mv, title=f"Sunburst: {ca} ← {cb}"))

        st.markdown("#### 🔢 تكرار الفئات (عدد السجلات)")
        cnt_col = st.selectbox("العمود:", group_cols, key="cnt_col")
        vc_ = dff[cnt_col].astype(str).value_counts().head(30).reset_index()
        vc_.columns = [cnt_col, "عدد"]
        show(px.bar(vc_, x=cnt_col, y="عدد", text_auto=True, color="عدد", color_continuous_scale="Tealgrn",
                    title=f"عدد السجلات لكل {cnt_col}"))

# ===== 6.3 التحليل الزمني =====
with tabs[2]:
    if not date_cols:
        st.info("لا يوجد عمود تاريخ في البيانات (يتم اكتشافه تلقائياً من النص أو التاريخ).")
    else:
        c1, c2, c3, c4 = st.columns(4)
        dc = c1.selectbox("عمود التاريخ:", date_cols, key="t_d")
        tv = c2.selectbox("القيمة:", num_cols, key="t_v") if num_cols else None
        tag = c3.selectbox("الدالة:", list(AGGS), key="t_a")
        fr = c4.selectbox("التجميع:", list(FREQS), index=2, key="t_f")
        split = st.selectbox("تقسيم الخط حسب فئة (اختياري):", ["بدون"] + group_cols, key="t_split")
        td = dff.dropna(subset=[dc])
        a = AGGS[tag] if (tv and tv != split) else "count"
        if td.empty:
            st.warning("لا توجد تواريخ صالحة.")
        else:
            if split == "بدون":
                if tv and a != "count":
                    ts = td.groupby(pd.Grouper(key=dc, freq=FREQS[fr]))[tv].agg(a).reset_index()
                else:
                    ts = td.groupby(pd.Grouper(key=dc, freq=FREQS[fr])).size().reset_index(name="عدد")
                tcol = ts.columns[1]
                win = st.slider("نافذة المتوسط المتحرك:", 1, 12, 3, key="t_win")
                ts["متوسط متحرك"] = ts[tcol].rolling(win, min_periods=1).mean()
                ts["تراكمي"] = ts[tcol].cumsum()
                ts["نمو %"] = ts[tcol].pct_change() * 100
                f = go.Figure()
                f.add_scatter(x=ts[dc], y=ts[tcol], name=tcol, mode="lines+markers", line=dict(color=ACCENT), fill="tozeroy",
                              fillcolor="rgba(0,242,254,.12)")
                f.add_scatter(x=ts[dc], y=ts["متوسط متحرك"], name=f"متوسط متحرك ({win})", line=dict(color="#ff7a59", dash="dash"))
                f.update_layout(title=f"{tag} {tcol} عبر الزمن ({fr})")
                show(f)
                g1, g2 = st.columns(2)
                with g1:
                    show(px.area(ts, x=dc, y="تراكمي", title="المجموع التراكمي"))
                with g2:
                    gg = ts.dropna(subset=["نمو %"]).copy()
                    gg["اتجاه"] = np.where(gg["نمو %"] >= 0, "ارتفاع", "انخفاض")
                    show(px.bar(gg, x=dc, y="نمو %", color="اتجاه",
                                color_discrete_map={"ارتفاع": "#2ecc71", "انخفاض": "#e74c3c"},
                                title="نسبة النمو عن الفترة السابقة %"))
            else:
                if tv and a != "count":
                    ts = td.groupby([pd.Grouper(key=dc, freq=FREQS[fr]), split])[tv].agg(a).reset_index()
                else:
                    ts = td.groupby([pd.Grouper(key=dc, freq=FREQS[fr]), split]).size().reset_index(name="عدد")
                tcol = ts.columns[2]
                ts[split] = ts[split].astype(str)
                ch = st.radio("الشكل:", ["خطوط", "مساحات متراكمة", "أعمدة متراكمة"], horizontal=True, key="t_ch")
                if ch == "خطوط":
                    show(px.line(ts, x=dc, y=tcol, color=split, markers=True, title=f"{tcol} عبر الزمن حسب {split}"))
                elif ch == "مساحات متراكمة":
                    show(px.area(ts, x=dc, y=tcol, color=split, title=f"{tcol} عبر الزمن حسب {split}"))
                else:
                    show(px.bar(ts, x=dc, y=tcol, color=split, title=f"{tcol} عبر الزمن حسب {split}"))

            st.markdown("#### 🗓️ الموسمية")
            tdd = td.copy()
            tdd["اليوم"] = tdd[dc].dt.day_name()
            tdd["الشهر"] = tdd[dc].dt.month
            tdd["السنة"] = tdd[dc].dt.year
            s1, s2 = st.columns(2)
            with s1:
                w = agg_frame(tdd, "اليوم", tv, a)
                wv = vcol(w, "اليوم", tv, a)
                w["اليوم"] = pd.Categorical(w["اليوم"], WEEKDAYS, ordered=True)
                show(px.bar(w.sort_values("اليوم"), x="اليوم", y=wv, color=wv, color_continuous_scale="Blues",
                            title="الأداء حسب أيام الأسبوع"))
            with s2:
                mo = agg_frame(tdd, "الشهر", tv, a)
                mv_ = vcol(mo, "الشهر", tv, a)
                show(px.bar(mo.sort_values("الشهر"), x="الشهر", y=mv_, color=mv_, color_continuous_scale="Teal",
                            title="الأداء حسب الشهر"))
            hm = tdd.pivot_table(index="اليوم", columns="الشهر", values=tv if (tv and a != "count") else dc,
                                 aggfunc=a if (tv and a != "count") else "count", fill_value=0)
            hm = hm.reindex([d for d in WEEKDAYS if d in hm.index])
            show(px.imshow(hm, aspect="auto", color_continuous_scale="Magma", text_auto=".2s",
                           title="خريطة حرارية: اليوم × الشهر"))
            if tdd["السنة"].nunique() > 1:
                ys = agg_frame(tdd, ["السنة", "الشهر"], tv, a)
                yv = vcol(ys, ["السنة", "الشهر"], tv, a)
                ys["السنة"] = ys["السنة"].astype(str)
                show(px.line(ys.sort_values("الشهر"), x="الشهر", y=yv, color="السنة", markers=True,
                             title="مقارنة السنوات شهراً بشهر"))

# ===== 6.4 العلاقات =====
with tabs[3]:
    if len(num_cols) < 2:
        st.info("نحتاج عمودين رقميين على الأقل.")
    else:
        method = st.radio("طريقة الارتباط:", ["pearson", "spearman", "kendall"], horizontal=True, key="cor_m")
        sel = st.multiselect("الأعمدة:", num_cols, default=num_cols[:12], key="cor_cols")
        if len(sel) >= 2:
            cm = dff[sel].corr(method=method)
            show(px.imshow(cm, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto",
                           title=f"مصفوفة الارتباط ({method})"), height=520)
            pairs = cm.where(np.triu(np.ones(cm.shape), 1).astype(bool)).stack().reset_index()
            pairs.columns = ["العمود 1", "العمود 2", "الارتباط"]
            pairs["القوة"] = pairs["الارتباط"].abs()
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("**أقوى الارتباطات**")
                show_df(pairs.sort_values("القوة", ascending=False).head(10).drop(columns="القوة").round(3), hide_index=True)
            with p2:
                st.markdown("**الارتباط مع عمود محدد**")
                tgt = st.selectbox("العمود الهدف:", sel, key="cor_t")
                ct = cm[tgt].drop(tgt).sort_values().reset_index()
                ct.columns = ["العمود", "الارتباط"]
                show(px.bar(ct, x="الارتباط", y="العمود", orientation="h", title=f"الارتباط مع {tgt}",
                            color="الارتباط", color_continuous_scale="RdBu_r", range_color=[-1, 1]))

        st.markdown("#### 📍 مخطط الانتشار")
        s1, s2, s3, s4 = st.columns(4)
        sx = s1.selectbox("X:", num_cols, index=0, key="sc_x")
        sy = s2.selectbox("Y:", num_cols, index=1, key="sc_y")
        scol = s3.selectbox("تلوين حسب:", ["بدون"] + group_cols, key="sc_c")
        ssz = s4.selectbox("حجم النقاط:", ["بدون"] + num_cols, key="sc_s")
        sd = dff if len(dff) <= 20000 else dff.sample(20000, random_state=1)
        fs = px.scatter(sd, x=sx, y=sy, color=None if scol == "بدون" else sd[scol].astype(str),
                        size=None if ssz == "بدون" else sd[ssz].abs().fillna(0), opacity=.7,
                        title=f"علاقة {sy} بـ {sx}")
        xy = dff[[sx, sy]].dropna() if sx != sy else dff[[sx]].dropna()
        if sx != sy and len(xy) > 2 and xy[sx].nunique() > 1:
            sl, ic = np.polyfit(xy[sx], xy[sy], 1)
            r = xy[sx].corr(xy[sy])
            xs = np.linspace(xy[sx].min(), xy[sx].max(), 50)
            fs.add_trace(go.Scatter(x=xs, y=sl * xs + ic, mode="lines", name=f"اتجاه (r={r:.2f}, R²={r * r:.2f})",
                                    line=dict(color="#ff7a59", width=3, dash="dash")))
        show(fs, height=560)

        if len(num_cols) >= 3:
            st.markdown("#### 🧩 مصفوفة الانتشار")
            sm = st.multiselect("الأعمدة (3-5):", num_cols, default=num_cols[:4], key="sm_cols")
            if len(sm) >= 2:
                show(px.scatter_matrix(sd, dimensions=sm[:6], color=None if scol == "بدون" else sd[scol].astype(str),
                                       opacity=.5, title="Scatter Matrix"), height=650)
        if len(num_cols) >= 3:
            st.markdown("#### 🌐 إحداثيات متوازية")
            pc = st.multiselect("الأعمدة:", num_cols, default=num_cols[:5], key="pc_cols")
            if len(pc) >= 2:
                show(px.parallel_coordinates(sd.dropna(subset=pc), dimensions=pc, color=pc[0],
                                             color_continuous_scale="Turbo", title="Parallel Coordinates"))

# ===== 6.5 التوزيع =====
with tabs[4]:
    if not num_cols:
        st.info("لا توجد أعمدة رقمية.")
    else:
        d1, d2, d3 = st.columns(3)
        dcn = d1.selectbox("العمود الرقمي:", num_cols, key="d_col")
        dgrp = d2.selectbox("تقسيم حسب:", ["بدون"] + group_cols, key="d_grp")
        bins = d3.slider("عدد الفئات (Bins):", 5, 100, 30, key="d_bins")
        g = None if dgrp == "بدون" else dgrp
        dd = dff.copy()
        if g:
            dd[g] = dd[g].astype(str)
        show(px.histogram(dd, x=dcn, color=g, nbins=bins, marginal="box", barmode="overlay", opacity=.75,
                          title=f"توزيع {dcn}"), height=480)
        e1, e2 = st.columns(2)
        with e1:
            show(px.box(dd, x=g, y=dcn, color=g, points="outliers", title=f"Box Plot — {dcn}"))
        with e2:
            show(px.violin(dd, x=g, y=dcn, color=g, box=True, points=False, title=f"Violin — {dcn}"))
        f1, f2 = st.columns(2)
        with f1:
            show(px.ecdf(dd, x=dcn, color=g, title="التوزيع التراكمي (ECDF)"))
        with f2:
            if g:
                show(px.histogram(dd, x=dcn, color=g, nbins=bins, histnorm="probability density", barmode="overlay",
                                  opacity=.6, title="الكثافة الاحتمالية حسب المجموعة"))
            else:
                q = dff[dcn].dropna().quantile([.01, .05, .25, .5, .75, .95, .99]).reset_index()
                q.columns = ["المئين", dcn]
                q["المئين"] = (q["المئين"] * 100).astype(int).astype(str) + "%"
                show(px.bar(q, x="المئين", y=dcn, text_auto=".3s", title="المئينات (Percentiles)"))

        st.markdown("#### 🚨 القيم الشاذة (طريقة IQR و Z-Score)")
        rows = []
        for c in num_cols:
            s = dff[c].dropna()
            if s.empty:
                continue
            q1, q3 = s.quantile([.25, .75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            n_iqr = int(((s < lo) | (s > hi)).sum())
            z = (s - s.mean()) / (s.std() or 1)
            rows.append({"العمود": c, "حد أدنى": round(lo, 2), "حد أعلى": round(hi, 2), "شاذة (IQR)": n_iqr,
                         "% شاذة": round(n_iqr / len(s) * 100, 2), "شاذة (|Z|>3)": int((z.abs() > 3).sum()),
                         "Skew": round(s.skew(), 2), "Kurtosis": round(s.kurt(), 2)})
        show_df(pd.DataFrame(rows), hide_index=True)
        s = dff[dcn].dropna()
        q1, q3 = s.quantile([.25, .75])
        iqr = q3 - q1
        out = dff[(dff[dcn] < q1 - 1.5 * iqr) | (dff[dcn] > q3 + 1.5 * iqr)]
        with st.expander(f"عرض صفوف القيم الشاذة في {dcn} ({len(out):,})"):
            show_df(out)

        if len(num_cols) >= 2:
            st.markdown("#### 🎻 مقارنة توزيع عدة أعمدة (مُوحَّدة 0-1)")
            mc = st.multiselect("الأعمدة:", num_cols, default=num_cols[:5], key="d_multi")
            if mc:
                nz = (dff[mc] - dff[mc].min()) / (dff[mc].max() - dff[mc].min()).replace(0, 1)
                show(px.box(nz.melt(var_name="العمود", value_name="قيمة مُوحَّدة"), x="العمود", y="قيمة مُوحَّدة",
                            color="العمود", title="Box Plot مُوحَّد"))

# ===== 6.6 جداول محورية وترتيب =====
with tabs[5]:
    if not group_cols:
        st.info("نحتاج أعمدة فئوية.")
    else:
        st.markdown("#### 🧮 جدول محوري")
        p1, p2, p3, p4 = st.columns(4)
        pr = p1.selectbox("الصفوف:", group_cols, key="p_r")
        pcn = p2.selectbox("الأعمدة:", ["بدون"] + [c for c in group_cols if c != pr], key="p_c")
        pvv = p3.selectbox("القيمة:", num_cols, key="p_v") if num_cols else None
        pag = p4.selectbox("الدالة:", list(AGGS), key="p_a")
        use_cnt = pvv is None or AGGS[pag] == "count"
        work = dff.copy()
        if use_cnt or pvv in (pr, pcn):
            work["_val"], pa_ = 1, "sum"
            vlabel = "عدد"
        else:
            work["_val"], pa_ = work[pvv], AGGS[pag]
            vlabel = pvv
        cols_ = None if pcn == "بدون" else pcn
        pt = work.pivot_table(index=pr, columns=cols_, values="_val", aggfunc=pa_, fill_value=0)
        overall = work["_val"].agg(pa_)
        if cols_:
            pt["الإجمالي"] = work.groupby(pr)["_val"].agg(pa_)
            ct = work.groupby(cols_)["_val"].agg(pa_)
            pt.loc["الإجمالي"] = [ct.get(c, 0) for c in pt.columns[:-1]] + [overall]
        else:
            pt.columns = [vlabel]
            pt.loc["الإجمالي"] = [overall]
        show_df(pt.round(2))
        st.download_button("💾 تحميل الجدول المحوري (Excel)", to_excel_bytes(pt.reset_index()),
                           "pivot_table.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if num_cols:
            st.markdown("#### 🥇 الأعلى والأدنى أداءً")
            r1, r2, r3 = st.columns(3)
            rk = r1.selectbox("الفئة:", group_cols, key="r_c")
            rv = r2.selectbox("المقياس:", [c for c in num_cols if c != rk] or num_cols, key="r_v")
            rn = r3.slider("N:", 3, 20, 10, key="r_n")
            if rk == rv:  # حالة نادرة: المقياس هو نفسه الفئة -> نستخدم العدد
                rg = dff.groupby(rk).size().reset_index(name="count")
                rg["sum"], rg["mean"] = rg["count"], 1.0
            else:
                rg = dff.groupby(rk)[rv].agg(["sum", "mean", "count"]).reset_index()
            rg["% من الإجمالي"] = rg["sum"] / rg["sum"].sum() * 100
            rg = rg.sort_values("sum", ascending=False)
            t1, t2 = st.columns(2)
            with t1:
                st.markdown(f"**أعلى {rn}**")
                show_df(rg.head(rn).round(2), hide_index=True)
            with t2:
                st.markdown(f"**أدنى {rn}**")
                show_df(rg.tail(rn).sort_values("sum").round(2), hide_index=True)
            show(px.scatter(rg, x="count", y="mean", size=rg["sum"].clip(lower=0), color=rk, hover_name=rk,
                            title=f"مصفوفة الأداء: عدد السجلات × متوسط {rv} (حجم الفقاعة = المجموع)"))
            wf = rg.head(10)
            show(px.funnel(wf, x="sum", y=rk, title=f"قمع الترتيب (Funnel) — {rv}"))

        if len(group_cols) >= 2 and num_cols:
            st.markdown("#### 🌳 هرم تفصيلي (Treemap متعدد المستويات)")
            lv = st.multiselect("المستويات بالترتيب:", group_cols, default=group_cols[:2], key="tm_lv")
            tmv = st.selectbox("القيمة:", [c for c in num_cols if c not in lv] or num_cols, key="tm_v")
            if lv and tmv not in lv:
                tm = dff.dropna(subset=lv).copy()
                tm[lv] = tm[lv].astype(str)
                tm = tm.groupby(lv)[tmv].sum().reset_index()
                tm = tm[tm[tmv] > 0]
                if not tm.empty:
                    show(px.treemap(tm, path=lv, values=tmv, color=tmv, color_continuous_scale="Viridis",
                                    title=f"{tmv} — " + " ← ".join(lv)), height=560)

# ===== 6.7 منشئ رسوم حر =====
with tabs[6]:
    st.markdown("#### 🎨 ابنِ أي رسم تريده")
    allc = dff.columns.tolist()
    kinds = ["أعمدة", "خطوط", "مساحة", "انتشار", "فقاعات", "هيستوجرام", "Box", "Violin", "دائرة", "قمع", "كثافة حرارية"]
    b1, b2, b3, b4 = st.columns(4)
    ck = b1.selectbox("نوع الرسم:", kinds, key="cb_k")
    cx = b2.selectbox("المحور X:", allc, key="cb_x")
    cy = b3.selectbox("المحور Y:", ["—"] + num_cols, key="cb_y")
    cc = b4.selectbox("لون حسب:", ["بدون"] + group_cols, key="cb_c")
    b5, b6, b7 = st.columns(3)
    cagg = b5.selectbox("الدالة (للتجميع):", list(AGGS), key="cb_a")
    csz = b6.selectbox("حجم (للفقاعات):", ["—"] + num_cols, key="cb_s")
    cfc = b7.selectbox("تقسيم لوحات (Facet):", ["بدون"] + [c for c in group_cols if dff[c].nunique() <= 8], key="cb_f")
    color = None if cc == "بدون" else cc
    facet = None if cfc == "بدون" else cfc
    yv = None if cy == "—" else cy
    d0 = dff.copy()
    for c in {color, facet} - {None}:
        d0[c] = d0[c].astype(str)
    try:
        if ck in ("أعمدة", "خطوط", "مساحة", "دائرة", "قمع"):
            keys = [cx] + [c for c in {color, facet} if c and c != cx]
            ag = agg_frame(d0, keys, yv, AGGS[cagg])
            vv = vcol(ag, keys, yv, AGGS[cagg])
            if ck in ("خطوط", "مساحة"):
                ag = ag.sort_values(cx)
            if ck == "أعمدة":
                fg = px.bar(ag, x=cx, y=vv, color=color, facet_col=facet, barmode="group")
            elif ck == "خطوط":
                fg = px.line(ag, x=cx, y=vv, color=color, facet_col=facet, markers=True)
            elif ck == "مساحة":
                fg = px.area(ag, x=cx, y=vv, color=color, facet_col=facet)
            elif ck == "دائرة":
                fg = px.pie(ag.sort_values(vv, ascending=False).head(15), names=cx, values=vv, hole=.4)
            else:
                fg = px.funnel(ag.sort_values(vv, ascending=False).head(12), x=vv, y=cx, color=color)
        else:
            dsm = d0 if len(d0) <= 20000 else d0.sample(20000, random_state=1)
            if ck == "انتشار":
                fg = px.scatter(dsm, x=cx, y=yv, color=color, facet_col=facet, opacity=.7)
            elif ck == "فقاعات":
                fg = px.scatter(dsm, x=cx, y=yv, size=None if csz == "—" else dsm[csz].abs().fillna(0),
                                color=color, facet_col=facet, opacity=.7)
            elif ck == "هيستوجرام":
                fg = px.histogram(dsm, x=cx, y=yv, color=color, facet_col=facet, barmode="overlay", opacity=.75)
            elif ck == "Box":
                fg = px.box(dsm, x=cx, y=yv, color=color, facet_col=facet)
            elif ck == "Violin":
                fg = px.violin(dsm, x=cx, y=yv, color=color, facet_col=facet, box=True)
            else:
                fg = px.density_heatmap(dsm, x=cx, y=yv, facet_col=facet, color_continuous_scale="Viridis")
        fg.update_layout(title=f"{ck}: {cx}" + (f" × {yv}" if yv else ""))
        show(fg, height=520)
    except Exception as e:
        st.warning(f"هذا الدمج من الأعمدة لا يناسب نوع الرسم المختار ({e}). جرّب اختيارات أخرى (مثلاً اختر عموداً رقمياً للمحور Y).")

# ===== 6.8 البيانات =====
with tabs[7]:
    st.markdown("#### 📋 استعراض البيانات بعد الفلترة")
    q = st.text_input("🔎 بحث نصي في كل الأعمدة:", key="q_txt")
    view = dff
    if q:
        m = dff.astype(str).apply(lambda s: s.str.contains(q, case=False, na=False)).any(axis=1)
        view = dff[m]
    cols_show = st.multiselect("الأعمدة المعروضة:", dff.columns.tolist(), default=dff.columns.tolist(), key="q_cols")
    show_df(view[cols_show] if cols_show else view)
    st.caption(f"{len(view):,} صف معروض")
    d1, d2 = st.columns(2)
    d1.download_button("💾 تحميل CSV", view.to_csv(index=False).encode("utf-8-sig"), "filtered_data.csv", "text/csv")
    d2.download_button("💾 تحميل Excel", to_excel_bytes(view), "filtered_data.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
