import pandas as pd
import streamlit as st
import plotly.express as px
import pathlib
from io import StringIO

st.set_page_config(page_title="Global Steel Routes", layout="wide")

@st.cache_data
def load_data():
    path = pathlib.Path("data/steel_routes.csv")

    raw_bytes = path.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("cp1252", errors="replace")

    cleaned_lines = [line.rstrip().rstrip(";") for line in raw_text.splitlines()]
    cleaned_text = "\n".join(cleaned_lines)

    df = pd.read_csv(StringIO(cleaned_text), sep=",", engine="python")

    df = df.replace("unknown", pd.NA)

    numeric_cols = [c for c in df.columns if c != "Country"]
    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Global" in df["Country"].astype(str).values:
        df = df[df["Country"] != "Global"]

    df[numeric_cols] = df[numeric_cols] / 1000.0  # ttp a -> Mtpa
    return df


df = load_data()

st.title("🌍 Global steel production by route")
st.caption("Source: Global Energy Monitor – Global Iron & Steel Tracker")

# KPIs
total_pig_iron = df["Pig iron produced (ttpa)"].sum(skipna=True)
total_dri = df["DRI produced (ttpa)"].sum(skipna=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pig iron (BF–BOF)", f"{total_pig_iron:,.0f} Mtpa")
col2.metric("DRI (DRI–EAF)", f"{total_dri:,.0f} Mtpa")
col3.metric(
    "DRI share",
    f"{(total_dri / (total_pig_iron + total_dri) * 100):.1f}%" if (total_pig_iron + total_dri) else "—"
)
col4.metric("Countries (any production)", int(df["Country"].nunique()))

# Top countries chart
top_n = st.slider("Top countries", 5, 25, 15)

top = (
    df[["Country", "Pig iron produced (ttpa)", "DRI produced (ttpa)"]]
    .fillna(0)
    .assign(Total=lambda x: x["Pig iron produced (ttpa)"] + x["DRI produced (ttpa)"])
    .sort_values("Total", ascending=False)
    .head(top_n)
)

top_long = top.melt(
    id_vars=["Country"],
    value_vars=["Pig iron produced (ttpa)", "DRI produced (ttpa)"],
    var_name="Route",
    value_name="Mtpa"
)

fig_bar = px.bar(
    top_long,
    x="Mtpa",
    y="Country",
    color="Route",
    orientation="h",
    title="Steel production by route (Top countries)",
)
st.plotly_chart(fig_bar, use_container_width=True)

# Global share donut
share_df = pd.DataFrame({
    "Route": ["BF–BOF (Pig iron)", "DRI–EAF"],
    "Production (Mtpa)": [total_pig_iron, total_dri],
})

fig_pie = px.pie(
    share_df,
    names="Route",
    values="Production (Mtpa)",
    hole=0.4,
    title="Global production share by route",
)
st.plotly_chart(fig_pie, use_container_width=True)

with st.expander("📊 View data"):
    st.dataframe(df, use_container_width=True)
