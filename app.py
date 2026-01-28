import pandas as pd
import streamlit as st
import plotly.express as px
import pathlib
from io import StringIO

st.set_page_config(page_title="Global Steel Routes", layout="wide")

# ----------------------------
# Theme (Light / Dark) styling
# ----------------------------

def inject_css(theme: str):
    """Inject an Apple-ish UI CSS theme (light/dark)."""
    if theme == "dark":
        bg = "#0b0b0f"
        panel = "rgba(255,255,255,0.06)"
        border = "rgba(255,255,255,0.10)"
        text = "rgba(255,255,255,0.92)"
        mutetext = "rgba(255,255,255,0.68)"
        shadow = "0 1px 2px rgba(0,0,0,0.35)"
        metric_bg = "rgba(255,255,255,0.06)"
        exp_bg = "rgba(255,255,255,0.05)"
    else:
        bg = "#ffffff"
        panel = "rgba(245,245,247,0.75)"
        border = "rgba(0,0,0,0.06)"
        text = "rgba(0,0,0,0.92)"
        mutetext = "rgba(0,0,0,0.65)"
        shadow = "0 1px 2px rgba(0,0,0,0.06)"
        metric_bg = "rgba(245,245,247,0.85)"
        exp_bg = "rgba(245,245,247,0.55)"

    st.markdown(
        f"""
        <style>
        .stApp {{
          background: {bg};
          color: {text};
        }}

        /* Layout width + padding */
        .block-container {{
          padding-top: 1.2rem;
          padding-bottom: 2rem;
          max-width: 1200px;
        }}

        /* Headings */
        h1, h2, h3 {{
          letter-spacing: -0.02em;
        }}

        /* Caption / text tone */
        .stCaption, .stMarkdown p {{
          color: {text};
        }}
        .muted {{
          color: {mutetext};
        }}

        /* Card wrapper */
        .card {{
          background: {panel};
          border: 1px solid {border};
          border-radius: 16px;
          padding: 16px 18px;
          box-shadow: {shadow};
        }}

        /* Metrics as tiles */
        [data-testid="stMetric"] {{
          background: {metric_bg};
          border: 1px solid {border};
          border-radius: 16px;
          padding: 14px 14px;
          box-shadow: {shadow};
        }}
        [data-testid="stMetricLabel"] p {{
          font-size: 0.9rem;
          opacity: 0.85;
          margin-bottom: 4px;
          letter-spacing: -0.01em;
        }}
        [data-testid="stMetricValue"] div {{
          font-size: 1.6rem;
          letter-spacing: -0.02em;
        }}

        /* Expanders */
        details {{
          border-radius: 14px;
          border: 1px solid {border};
          background: {exp_bg};
          padding: 6px 10px;
        }}

        /* Sidebar spacing */
        section[data-testid="stSidebar"] .block-container {{
          padding-top: 1rem;
        }}

        /* Subtle horizontal rule */
        hr {{
          border: none;
          border-top: 1px solid {border};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(fig, theme: str, title: str | None = None, subtitle: str | None = None):
    """Apply a clean dashboard style to Plotly figures, adapting to theme.
    Fix: place legend below plot; subtitle below title; avoid overlap.
    """
    if theme == "dark":
        font_color = "rgba(255,255,255,0.90)"
        sub_color = "rgba(255,255,255,0.65)"
        grid_color = "rgba(255,255,255,0.10)"
        axis_line = "rgba(255,255,255,0.18)"
        hover_bg = "rgba(20,20,26,0.95)"
        hover_border = "rgba(255,255,255,0.12)"
    else:
        font_color = "rgba(0,0,0,0.90)"
        sub_color = "rgba(0,0,0,0.60)"
        grid_color = "rgba(0,0,0,0.06)"
        axis_line = "rgba(0,0,0,0.12)"
        hover_bg = "rgba(255,255,255,0.95)"
        hover_border = "rgba(0,0,0,0.10)"

    fig.update_layout(
        template="plotly_white",
        title=dict(text=title or fig.layout.title.text, x=0.0, xanchor="left"),
        font=dict(
            family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial",
            size=13,
            color=font_color,
        ),
        # More top space for title/subtitle; more bottom for legend
        margin=dict(l=10, r=10, t=90, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            title_text="",
            orientation="h",
            yanchor="top",
            y=-0.18,  # legend below plot area
            xanchor="left",
            x=0,
            font=dict(color=font_color),
        ),
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font=dict(color=font_color),
        ),
    )

    # Less “chart ink”
    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        showline=False,
        linecolor=axis_line,
        ticks="outside",
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        linecolor=axis_line,
        ticks="outside",
    )

    # Subtitle: below title, above plot
    if subtitle:
        fig.update_layout(
            annotations=[
                dict(
                    text=subtitle,
                    x=0,
                    y=1.07,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    align="left",
                    font=dict(size=12, color=sub_color),
                )
            ]
        )

    return fig


def style_table(df: pd.DataFrame, theme: str):
    """Force dataframe to match theme (Streamlit grid can ignore CSS)."""
    if theme == "dark":
        bg = "#0b0b0f"
        panel = "rgba(255,255,255,0.06)"
        border = "rgba(255,255,255,0.10)"
        text = "rgba(255,255,255,0.90)"
    else:
        bg = "#ffffff"
        panel = "rgba(245,245,247,0.85)"
        border = "rgba(0,0,0,0.06)"
        text = "rgba(0,0,0,0.90)"

    return (
        df.style
        .set_table_styles([
            {"selector": "thead th", "props": [
                ("background-color", panel),
                ("color", text),
                ("border-bottom", f"1px solid {border}"),
                ("font-weight", "600"),
            ]},
            {"selector": "tbody td", "props": [
                ("background-color", panel),
                ("color", text),
                ("border-bottom", f"1px solid {border}"),
            ]},
            {"selector": "table", "props": [
                ("background-color", bg),
                ("border-collapse", "collapse"),
            ]},
        ])
        .set_properties(**{"border": f"1px solid {border}"})
    )


# Sidebar theme toggle
with st.sidebar:
    st.header("Settings")
    dark_mode = st.toggle("Dark mode", value=False)

THEME = "dark" if dark_mode else "light"
inject_css(THEME)

# ----------------------------
# Data loading / cleaning
# ----------------------------

ROUTE_COLS = {
    "Pig iron produced (ttpa)": "BF–BOF (Pig iron)",
    "DRI produced (ttpa)": "DRI–EAF",
}
UNIT_DIVISOR = 1000.0  # ttpa -> Mtpa


@st.cache_data
def load_data():
    path = pathlib.Path("./steel_routes.csv")

    raw_bytes = path.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("cp1252", errors="replace")

    cleaned_lines = [line.rstrip().rstrip(";") for line in raw_text.splitlines()]
    cleaned_text = "\n".join(cleaned_lines)

    raw_df = pd.read_csv(StringIO(cleaned_text), sep=",", engine="python")
    df = raw_df.copy()

    df = df.replace("unknown", pd.NA)

    expected = ["Country", *ROUTE_COLS.keys()]
    present = [c for c in expected if c in df.columns]
    df = df[present]

    for col in ROUTE_COLS.keys():
        if col not in df.columns:
            continue
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Country" in df.columns and "Global" in df["Country"].astype(str).values:
        df = df[df["Country"] != "Global"]

    numeric_cols = [c for c in ROUTE_COLS.keys() if c in df.columns]
    df[numeric_cols] = df[numeric_cols] / UNIT_DIVISOR

    return raw_df, df


raw_df, df = load_data()

# ----------------------------
# UI Header / framing
# ----------------------------

st.title("🌍 Global primary steelmaking routes")
st.caption("Source: Global Energy Monitor – Global Iron & Steel Tracker")

st.markdown(
    """
<div class="card">
  <div class="muted">
    This dashboard compares <b>primary steelmaking routes</b>:
    <ul>
      <li><b>BF–BOF</b> via pig iron production (blast furnace → basic oxygen furnace)</li>
      <li><b>DRI–EAF</b> via direct reduced iron production (DRI → electric arc furnace)</li>
    </ul>
    The intent is not to forecast output, but to highlight <b>structural differences</b> relevant to
    energy use, emissions intensity, and decarbonisation pathways.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# ----------------------------
# KPIs
# ----------------------------

pig_col = "Pig iron produced (ttpa)"
dri_col = "DRI produced (ttpa)"

total_pig = df[pig_col].sum(skipna=True) if pig_col in df.columns else 0.0
total_dri = df[dri_col].sum(skipna=True) if dri_col in df.columns else 0.0
total_primary = total_pig + total_dri
dri_share = (total_dri / total_primary * 100) if total_primary > 0 else None
countries_any = int(df["Country"].nunique()) if "Country" in df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("BF–BOF (Pig iron)", f"{total_pig:,.0f} Mtpa")
c2.metric("DRI–EAF (DRI)", f"{total_dri:,.0f} Mtpa")
c3.metric("DRI share of primary routes", f"{dri_share:.1f}%" if dri_share is not None else "—")
c4.metric("Countries (any production)", countries_any)

st.write("")

# ----------------------------
# Top countries chart
# ----------------------------

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
fig_bar.update_traces(marker_line_width=0, opacity=0.95)
fig_bar.update_layout(barmode="stack")
fig_bar.update_traces(hovertemplate="<b>%{y}</b><br>%{x:,.1f} Mtpa<extra></extra>")
fig_bar = style_plotly(
    fig_bar,
    THEME,
    title="Primary steelmaking routes (Top countries)",
    subtitle="BF–BOF via pig iron vs DRI–EAF via direct reduced iron (Mtpa)",
)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.plotly_chart(fig_bar, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Global share donut
# ----------------------------

share_df = pd.DataFrame({
    "Route": ["BF–BOF (Pig iron)", "DRI–EAF"],
    "Production (Mtpa)": [total_pig, total_dri],
})

fig_pie = px.pie(
    share_df,
    names="Route",
    values="Production (Mtpa)",
    hole=0.42,
    title="Global primary steelmaking route split",
)

# Improve donut readability across themes
if THEME == "dark":
    fig_pie.update_traces(textfont_color="rgba(255,255,255,0.92)")
else:
    fig_pie.update_traces(textfont_color="rgba(0,0,0,0.85)")

fig_pie.update_traces(
    textposition="inside",
    textinfo="percent",
    hovertemplate="<b>%{label}</b><br>%{value:,.0f} Mtpa<br>%{percent}<extra></extra>",
)

fig_pie = style_plotly(
    fig_pie,
    THEME,
    title="Global primary steelmaking route split",
    subtitle="Share of BF–BOF vs DRI–EAF within primary routes",
)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.plotly_chart(fig_pie, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Country route mix table
# ----------------------------

st.subheader("Country route mix")

show_mix = st.checkbox("Show DRI share by country (table)", value=True)
if show_mix and pig_col in df.columns and dri_col in df.columns:
    mix = df[["Country", pig_col, dri_col]].copy().fillna(0)
    mix["Total (Mtpa)"] = mix[pig_col] + mix[dri_col]
    mix["DRI share (%)"] = mix.apply(
        lambda r: (r[dri_col] / r["Total (Mtpa)"] * 100) if r["Total (Mtpa)"] > 0 else pd.NA,
        axis=1
    )
    mix = mix.sort_values("Total (Mtpa)", ascending=False)

    display_mix = mix.rename(columns={
        pig_col: "BF–BOF (Pig iron) Mtpa",
        dri_col: "DRI–EAF (DRI) Mtpa",
    })

    styled_mix = style_table(display_mix, THEME)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.dataframe(styled_mix, use_container_width=True, height=460)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# ----------------------------
# Transparency / QA sections
# ----------------------------

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
