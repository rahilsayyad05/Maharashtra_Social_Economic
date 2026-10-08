import os
import urllib.request
from pathlib import Path
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib import patheffects as pe

st.set_page_config(page_title="Maharashtra Socio-Economic Rank", layout="wide")
st.title("Maharashtra Socio-Economic District Ranking")

# --- Step 1: Raw GeoJSON Download ---
geojson_file = "maharashtra_district.geojson"
raw_url = "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/states/maharashtra.geojson"

if not os.path.exists(geojson_file) or os.path.getsize(geojson_file) < 50000:
    with st.spinner("Downloading GeoJSON map data..."):
        urllib.request.urlretrieve(raw_url, geojson_file)

# --- Step 2: Caching Data Load ---
@st.cache_data
def load_and_prep_data():
    excel_file = "Maharashtra_District_Ranking_Final_2011.xlsx"
    map_df = gpd.read_file(geojson_file)

    possible_files = [
        Path(excel_file),
        Path("Maharashtra_District_Ranking_Final.xlsx"),
        Path("/content/Maharashtra_District_Ranking_Final.xlsx"),
    ]

    existing_file = next((path for path in possible_files if path.exists()), None)
    if existing_file is None:
        raise FileNotFoundError(
            "Ranking Excel file not found. Checked:\n"
            + "\n".join(str(path) for path in possible_files)
        )

    df = pd.read_excel(str(existing_file))

    # District column pehchanein
    geo_dist_col = None
    for col in ["district", "District", "dtname", "NAME_2", "stname"]:
        if col in map_df.columns:
            geo_dist_col = col
            break
    if geo_dist_col is None:
        geo_dist_col = map_df.columns[0]

    # Standardize district names
    map_df["dist_clean"] = map_df[geo_dist_col].astype(str).str.strip().str.title()
    df["dist_clean"] = df["District"].astype(str).str.strip().str.title()

    # Rename updated districts
    rename_map = {
        "Ahmadnagar": "Ahilyanagar",
        "Ahmednagar": "Ahilyanagar",
        "Aurangabad": "Chatrapati Sambhaji Nagar",
        "Chhatrapati Sambhajinagar": "Chatrapati Sambhaji Nagar",
        "Osmanabad": "Dharashiv",
    }
    map_df["dist_clean"] = map_df["dist_clean"].replace(rename_map)
    df["dist_clean"] = df["dist_clean"].replace(rename_map)

    # Mumbai Handling
    if not df["dist_clean"].str.contains("Mumbai").any():
        mumbai_data = pd.DataFrame([{"District": "Mumbai", "dist_clean": "Mumbai", "Rank": 1}])
        df = pd.concat([df, mumbai_data], ignore_index=True)

    mumbai_rank = df.loc[df["dist_clean"].str.contains("Mumbai"), "Rank"].values
    if len(mumbai_rank) > 0:
        target_rank = mumbai_rank[0]
        for m_variant in ["Mumbai", "Mumbai City", "Mumbai Suburban"]:
            if not (df["dist_clean"] == m_variant).any():
                df = pd.concat([df, pd.DataFrame([{"District": m_variant, "dist_clean": m_variant, "Rank": target_rank}])], ignore_index=True)

    # Merge
    merged = map_df.merge(df, on="dist_clean", how="left")

    def get_color(rank):
        if pd.isna(rank):
            return "#D3D3D3"
        elif rank <= 12:
            return "#478848"
        elif rank <= 24:
            return "#F8B756"
        else:
            return "#E85342"

    merged["color"] = merged["Rank"].apply(get_color)
    return merged, df

merged, df = load_and_prep_data()

# --- Step 3: Plotting Function ---
@st.cache_resource
def generate_plot():
    fig, ax = plt.subplots(figsize=(12, 10))
    merged.plot(ax=ax, color=merged["color"], edgecolor="black", linewidth=0.8)

    legend_handles = [
        mpatches.Patch(facecolor="#478848", edgecolor="black", label="High (1–12)"),
        mpatches.Patch(facecolor="#F8B756", edgecolor="black", label="Medium (13–24)"),
        mpatches.Patch(facecolor="#E85342", edgecolor="black", label="Low (25+)"),
        mpatches.Patch(facecolor="#D3D3D3", edgecolor="black", label="No Data"),
    ]
    ax.legend(
        handles=legend_handles,
        title="District Rank",
        loc="lower right",
        fontsize=11,
        title_fontsize=12,
        frameon=True,
    )

    for _, row in merged.iterrows():
        rank_val = row.get("Rank")
        dist_name = row.get("dist_clean")
        if pd.notna(rank_val) and pd.notna(dist_name):
            pt = row["geometry"].representative_point()
            ax.annotate(
                text=f"{int(rank_val)}\n{dist_name}",
                xy=(pt.x, pt.y),
                ha="center",
                va="center",
                fontsize=7,
                fontweight="bold",
                color="#111111",
                linespacing=0.85,
                path_effects=[pe.withStroke(linewidth=2, foreground="white", alpha=0.9)],
            )

    ax.set_title("District-wise Social Economic Rank in Maharashtra", fontsize=18, fontweight="bold", pad=20)
    ax.set_axis_off()
    plt.tight_layout()
    return fig

fig = generate_plot()

# Streamlit UI par show karein
col1, col2 = st.columns([2, 1])
with col1:
    st.pyplot(fig)

with col2:
    st.subheader("Data Overview")
    st.dataframe(df[["dist_clean", "Rank"]].dropna().sort_values("Rank").reset_index(drop=True), height=500)
