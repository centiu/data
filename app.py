import pandas as pd
import streamlit as st
import plotly.express as px
import pathlib
from io import StringIO

st.set_page_config(page_title="Global Steel Routes", layout="wide")

# Explicit schema (more robust than "everything except Country")
ROUTE_COLS = {
    "Pig iron produced (ttpa)": "BF–BOF (Pig iron)",
    "DRI produced (ttpa)": "DRI–EAF",
}

UNIT_DIVISOR = 1000.0  # ttp a -> Mtpa


@st.cache_data
def load_data():
    path = pathlib.Path("./steel_routes.csv")

    raw_bytes = path.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("cp1252", errors="replace")

    # Clean up common export issues (trailing semicolons, whitespace)
    cleaned_lines = [line.rstrip().rstrip(";") for line in raw_text.splitlines()]
    cleaned_text = "\n".join(cleaned_lines)

    raw_df = pd.read_csv(StringIO(cleaned_text), sep=",", engine="python")

    df = raw_df.copy()

    # Standardise missing markers
    df = df.replace("unknown", pd.NA)

    # Keep only expected columns if present (safer when dataset evolves)
    expected = ["Country", *ROUTE_COLS.keys()]
    present = [c for c in expected if c in df.columns]
    df = df[present]

    # Coerce numeric route columns
    for col in ROUTE_COLS.keys():
        if col not in df.columns:
            continue
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)  # handle 1.234.567 style
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove global aggregate row if present
    if "Country" in df.columns and "Global" in df["Country"].astype(str).values:
        df = df[df["Country"] != "Global"]

    # Unit conversion
    numeric_cols = [c for c in ROUTE_COLS.keys() if c in df.columns]
    df[numeric_cols] = df[numeric_cols] / UNIT_DIVISOR  # Mtpa

    return raw_df, df


raw_df, df = load_data()

# --- Page header & framing ---
st.title("🌍 Global primary steelmaking routes")
st.caption("Source: Global Energy Monitor – Global Iron & Steel Tracker")

st.markdown("""
This dashboard focuses on **primary steelmaking routes**, comparing:
- **BF–BOF** via pig iron production (blast furnace → basic oxygen furnace)
- **DRI–EAF** via direct reduced iron production (DRI → electric arc furnace)

The goal is not to forecast output, but to highlight **structural differences**
in how steel is produced globally — relevant to energy use, emissions intensity,
and decarbonisation pathways.
""")

# --- KPIs ---
pig_col = "Pig iron produced (ttpa)"
dri_col = "DRI produced (ttpa)"

total_pig = df[pig_col].sum(skipna=True) if pig_col in df.columns else 0.0
total_dri = df[dri_col].sum(skipna=True) if dri_col in df.columns else 0.0
total_primary = total_pig + total_dri

dri_share = (total_dri / total_primary * 100) if total_primary > 0 else None

countries_any = int(df["Country"].nunique()) if "Country" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("BF–BOF (Pig iron)", f"{total_pig:,.0f} Mtpa")
col2.metric("DRI–EAF (DRI)", f"{total_dri:,.0f} Mtpa")
col3.metric("DRI share of primary routes", f"{dri_share:.1f}%" if dri_share is not None else "—")
col4.metric("Countries (any production)", countries_any)

st.divider()

# --- Top countries chart ---
top_n = st.slider("Top countries", 5, 25, 15)

plot_cols = ["Country"] + [c for c in ROUTE_COLS.keys() if c in df.columns]
top = (
    df[plot_cols]
    .fillna(0)
    .assign(Total=lambda x: sum(x[c] for c in ROUTE_COLS.keys() if c in x.columns))
    .sort_values("Total", ascending=False)
    .head(top_n)
)

top_long = top.melt(
    id_vars=["Country"],
    value_vars=[c for c in ROUTE_COLS.keys() if c in top.columns],
    var_name="Source column",
    value_name="Mtpa"
)
top_long["Route"] = top_long["Source column"].map(ROUTE_COLS)

fig_bar = px.bar(
    top_long,
    x="Mtpa",
    y="Country",
    color="Route",
    orientation="h",
    title="Primary steelmaking routes (Top countries)",
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Global share donut ---
share_df = pd.DataFrame({
    "Route": ["BF–BOF (Pig iron)", "DRI–EAF"],
    "Production (Mtpa)": [total_pig, total_dri],
})

fig_pie = px.pie(
    share_df,
    names="Route",
    values="Production (Mtpa)",
    hole=0.4,
    title="Global primary steelmaking route split",
)
st.plotly_chart(fig_pie, use_container_width=True)

# --- Optional: DRI share by country (high-signal view) ---
st.subheader("Country route mix")

show_mix = st.checkbox("Show DRI share by country (table)", value=True)
if show_mix and pig_col in df.columns and dri_col in df.columns:
    mix = df[["Country", pig_col, dri_col]].copy()
    mix = mix.fillna(0)
    mix["Total (Mtpa)"] = mix[pig_col] + mix[dri_col]
    mix["DRI share (%)"] = mix.apply(
        lambda r: (r[dri_col] / r["Total (Mtpa)"] * 100) if r["Total (Mtpa)"] > 0 else pd.NA,
        axis=1
    )
    mix = mix.sort_values("Total (Mtpa)", ascending=False)
    st.dataframe(
        mix.rename(columns={
            pig_col: "BF–BOF (Pig iron) Mtpa",
            dri_col: "DRI–EAF (DRI) Mtpa",
        }),
        use_container_width=True
    )

# --- Data quality / transparency section ---
with st.expander("🔍 Data quality notes"):
    st.markdown(f"""
- Rows loaded (raw): **{len(raw_df):,}**
- Rows after cleaning/filtering: **{len(df):,}**
- Aggregate rows removed: **Global** (if present)
- Numeric coercion: non-numeric values → **NaN**
- Units: values displayed as **Mtpa** (converted from ttpa ÷ {UNIT_DIVISOR:g})
""")

with st.expander("📊 View cleaned data"):
    st.dataframe(df, use_container_width=True)
