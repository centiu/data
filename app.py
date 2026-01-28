import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Global Steel Routes", layout="wide")

# --- Load data ---
@st.cache_data
def load_data():
    path = pathlib.Path("steel_routes.csv")  # or "data/steel_routes.csv"

    # Read raw bytes, decode safely
    raw_bytes = path.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("cp1252", errors="replace")

    # Remove trailing semicolons at end of lines (your file has "... ;")
    # Also remove accidental empty columns due to trailing separators
    cleaned_lines = []
    for line in raw_text.splitlines():
        cleaned_lines.append(line.rstrip().rstrip(";"))
    cleaned_text = "\n".join(cleaned_lines)

    # Now parse as standard CSV (comma-delimited)
    df = pd.read_csv(StringIO(cleaned_text), sep=",", engine="python")

    # Standard cleanup
    df = df.replace("unknown", pd.NA)

    # Convert numeric columns (everything except Country)
    numeric_cols = [c for c in df.columns if c != "Country"]
    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)   # 1.014.117 -> 1014117
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop Global if present
    if "Global" in df["Country"].values:
        df = df[df["Country"] != "Global"]

    # Convert ttp a -> Mtpa
    df[numeric_cols] = df[numeric_cols] / 1000.0

    return df

# --- Header ---
st.title("🌍 Global steel production by route")
st.caption("Source: Global Energy Monitor – Global Iron & Steel Tracker")

# --- KPIs ---
total_pig_iron = df["Pig iron produced (ttpa)"].sum()
total_dri = df["DRI produced (ttpa)"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pig iron (BF–BOF)", f"{total_pig_iron:,.0f} Mtpa")
col2.metric("DRI (DRI–EAF)", f"{total_dri:,.0f} Mtpa")
col3.metric("DRI share", f"{(total_dri / (total_pig_iron + total_dri) * 100):.1f}%")
col4.metric("Producing countries", df[df["Pig iron produced (ttpa)"].notna()].shape[0])

# --- Top countries ---
top_n = st.slider("Top countries", 5, 25, 15)

top = (
    df[["Country", "Pig iron produced (ttpa)", "DRI produced (ttpa)"]]
    .fillna(0)
    .assign(Total=lambda x: x.sum(axis=1))
    .sort_values("Total", ascending=False)
    .head(top_n)
)

fig_bar = px.bar(
    top,
    x="Country",
    y=["Pig iron produced (ttpa)", "DRI produced (ttpa)"],
    title="Steel production by route (Top countries)",
    labels={"value": "Mtpa", "variable": "Production route"},
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Global share ---
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

# --- Data table ---
with st.expander("📊 View data"):
    st.dataframe(df, use_container_width=True)



