import os
import urllib.request
from pathlib import Path

import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from matplotlib import patheffects as pe


# =========================================================
# PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="Maharashtra Social Economic Map",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ District-wise Social Economic Rank in Maharashtra")
st.write("Maharashtra District Ranking – 2011")


# =========================================================
# FILE PATHS
# =========================================================
BASE_DIR = Path(__file__).parent

excel_file = BASE_DIR / "Maharashtra_District_Ranking_Final_2011.xlsx"
geojson_file = BASE_DIR / "maharashtra_district.geojson"


# =========================================================
# DOWNLOAD GEOJSON IF NOT AVAILABLE
# =========================================================
raw_url = (
    "https://raw.githubusercontent.com/udit-001/"
    "india-maps-data/main/geojson/states/maharashtra.geojson"
)

if not geojson_file.exists() or geojson_file.stat().st_size < 50000:

    with st.spinner("Downloading Maharashtra district map..."):

        urllib.request.urlretrieve(
            raw_url,
            geojson_file
        )


# =========================================================
# CHECK EXCEL FILE
# =========================================================
if not excel_file.exists():

    st.error(
        "Excel file not found: "
        + str(excel_file)
    )

    st.stop()


# =========================================================
# LOAD FILES
# =========================================================
try:

    map_df = gpd.read_file(geojson_file)

    df = pd.read_excel(excel_file)

except Exception as e:

    st.error("Error while loading files:")
    st.exception(e)

    st.stop()


# =========================================================
# CHECK REQUIRED COLUMNS
# =========================================================
if "District" not in df.columns:

    st.error(
        "Excel file मध्ये 'District' column सापडला नाही."
    )

    st.write("Available columns:")
    st.write(list(df.columns))

    st.stop()


if "Rank" not in df.columns:

    st.error(
        "Excel file मध्ये 'Rank' column सापडला नाही."
    )

    st.write("Available columns:")
    st.write(list(df.columns))

    st.stop()


# =========================================================
# FIND DISTRICT COLUMN IN GEOJSON
# =========================================================
possible_geo_columns = [
    "district",
    "District",
    "dtname",
    "NAME_2",
    "stname",
    "name"
]

geo_dist_col = None

for col in possible_geo_columns:

    if col in map_df.columns:

        geo_dist_col = col
        break


if geo_dist_col is None:

    st.error("GeoJSON मध्ये district name column सापडला नाही.")

    st.write("GeoJSON columns:")
    st.write(list(map_df.columns))

    st.stop()


# =========================================================
# STANDARDIZE DISTRICT NAMES
# =========================================================
map_df["dist_clean"] = (
    map_df[geo_dist_col]
    .astype(str)
    .str.strip()
    .str.title()
)

df["dist_clean"] = (
    df["District"]
    .astype(str)
    .str.strip()
    .str.title()
)


# =========================================================
# DISTRICT NAME CHANGES
# =========================================================
rename_map = {

    "Ahmadnagar": "Ahilyanagar",
    "Ahmednagar": "Ahilyanagar",

    "Aurangabad": "Chatrapati Sambhaji Nagar",
    "Chhatrapati Sambhajinagar":
        "Chatrapati Sambhaji Nagar",

    "Osmanabad": "Dharashiv"
}


map_df["dist_clean"] = (
    map_df["dist_clean"]
    .replace(rename_map)
)

df["dist_clean"] = (
    df["dist_clean"]
    .replace(rename_map)
)


# =========================================================
# MERGE DATA
# =========================================================
merged = map_df.merge(
    df,
    on="dist_clean",
    how="left"
)


# =========================================================
# COLOR FUNCTION
# =========================================================
def get_color(rank):

    if pd.isna(rank):

        return "#D3D3D3"

    elif rank <= 12:

        return "#478848"

    elif rank <= 24:

        return "#F8B756"

    else:

        return "#E85342"


merged["color"] = (
    merged["Rank"]
    .apply(get_color)
)


# =========================================================
# CREATE MAP
# =========================================================
fig, ax = plt.subplots(
    figsize=(14, 12)
)

merged.plot(
    ax=ax,
    color=merged["color"],
    edgecolor="black",
    linewidth=0.8
)


# =========================================================
# ADD DISTRICT LABELS
# =========================================================
for _, row in merged.iterrows():

    rank_val = row.get("Rank")
    dist_name = row.get("dist_clean")

    if (
        pd.notna(rank_val)
        and pd.notna(dist_name)
    ):

        try:

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
                path_effects=[
                    pe.withStroke(
                        linewidth=2,
                        foreground="white",
                        alpha=0.9
                    )
                ]
            )

        except Exception:
            pass


# =========================================================
# LEGEND
# =========================================================
legend_handles = [

    mpatches.Patch(
        facecolor="#478848",
        edgecolor="black",
        label="High (1–12)"
    ),

    mpatches.Patch(
        facecolor="#F8B756",
        edgecolor="black",
        label="Medium (13–24)"
    ),

    mpatches.Patch(
        facecolor="#E85342",
        edgecolor="black",
        label="Low (25+)"
    ),

    mpatches.Patch(
        facecolor="#D3D3D3",
        edgecolor="black",
        label="No Data"
    )
]


ax.legend(
    handles=legend_handles,
    title="District Rank",
    loc="lower right",
    fontsize=11,
    title_fontsize=12,
    frameon=True
)


# =========================================================
# TITLE
# =========================================================
ax.set_title(
    "District-wise Social Economic Rank in Maharashtra",
    fontsize=20,
    fontweight="bold",
    pad=20
)

ax.set_axis_off()

plt.tight_layout()


# =========================================================
# MOST IMPORTANT: SHOW MAP IN STREAMLIT
# =========================================================
st.pyplot(fig, use_container_width=True)


# =========================================================
# DATA TABLE
# =========================================================
st.subheader("District Ranking Data")

display_columns = [
    "District",
    "Rank"
]

available_columns = [
    col for col in display_columns
    if col in df.columns
]

st.dataframe(
    df[available_columns],
    use_container_width=True
)
