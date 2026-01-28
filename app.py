import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Steel & Mining Data Dashboard", layout="wide")

st.title("Steel & Mining Data Dashboard")
st.caption("A public-data portfolio project focused on Australia iron ore and global steelmaking routes.")

# --- OPTIONAL: Google Analytics (GA4) ---
# Replace G-XXXXXXXXXX with your Measurement ID
GA_MEASUREMENT_ID = "G-XXXXXXXXXX"
st.components.v1.html(
    f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    """,
    height=0,
)

# --- Load sample data (replace with real sources later) ---
DATA_DIR = Path("data")
iron_ore_path = DATA_DIR / "iron_ore_australia_sample.csv"
steel_routes_path = DATA_DIR / "steel_routes_sample.csv"

col1, col2 = st.columns(2)

with col1:
    st.subheader("Australia Iron Ore (sample)")
    if iron_ore_path.exists():
        df_iron = pd.read_csv(iron_ore_path)
        st.dataframe(df_iron, use_container_width=True)

        fig = px.line(df_iron, x="year", y="value", title="Sample trend")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add data/iron_ore_australia_sample.csv to see this chart.")

with col2:
    st.subheader("Steelmaking Routes (sample)")
    if steel_routes_path.exists():
        df_routes = pd.read_csv(steel_routes_path)
        st.dataframe(df_routes, use_container_width=True)

        fig2 = px.bar(df_routes, x="route", y="plants", title="Plants by route (sample)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Add data/steel_routes_sample.csv to see this chart.")

st.markdown("---")
st.subheader("Sources & notes")
st.write(
    "This dashboard is built from public datasets and reports. Each chart includes attribution in the project README."
)
