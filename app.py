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
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Maharashtra Social Economic Index",
    page_icon="🗺️",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🗺️ District-wise Social Economic Rank in Maharashtra")

st.markdown(
    "**Maharashtra District Ranking – 2011**"
)

st.markdown("---")


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).parent

excel_file = (
    BASE_DIR /
    "Maharashtra_District_Ranking_Final_2011.xlsx"
)

geojson_file = (
    BASE_DIR /
    "maharashtra_district.geojson"
)


# =========================================================
# GEOJSON DOWNLOAD
# =========================================================

raw_url = (
    "https://raw.githubusercontent.com/"
    "udit-001/india-maps-data/main/"
    "geojson/states/maharashtra.geojson"
)


if (
    not geojson_file.exists()
    or geojson_file.stat().st_size < 50000
):

    with st.spinner(
        "Downloading Maharashtra district map..."
    ):

        try:

            urllib.request.urlretrieve(
                raw_url,
                geojson_file
            )

        except Exception as e:

            st.error(
                "GeoJSON download failed."
            )

            st.exception(e)

            st.stop()


# =========================================================
# CHECK EXCEL
# =========================================================

if not excel_file.exists():

    st.error(
        "Excel file not found:\n"
        + str(excel_file)
    )

    st.stop()


# =========================================================
# LOAD DATA
# =========================================================

try:

    map_df = gpd.read_file(
        geojson_file
    )

    df = pd.read_excel(
        excel_file
    )

except Exception as e:

    st.error(
        "Error while loading data."
    )

    st.exception(e)

    st.stop()


# =========================================================
# CHECK COLUMNS
# =========================================================

if "District" not in df.columns:

    st.error(
        "Excel मध्ये 'District' column सापडला नाही."
    )

    st.write(
        "Available columns:"
    )

    st.write(
        list(df.columns)
    )

    st.stop()


if "Rank" not in df.columns:

    st.error(
        "Excel मध्ये 'Rank' column सापडला नाही."
    )

    st.write(
        "Available columns:"
    )

    st.write(
        list(df.columns)
    )

    st.stop()


# =========================================================
# FIND GEOJSON DISTRICT COLUMN
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

    st.error(
        "GeoJSON मध्ये district name column सापडला नाही."
    )

    st.write(
        list(map_df.columns)
    )

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
# UPDATED DISTRICT NAMES
# =========================================================

rename_map = {

    "Ahmadnagar":
        "Ahilyanagar",

    "Ahmednagar":
        "Ahilyanagar",

    "Aurangabad":
        "Chatrapati Sambhaji Nagar",

    "Chhatrapati Sambhajinagar":
        "Chatrapati Sambhaji Nagar",

    "Osmanabad":
        "Dharashiv"
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
# MERGE
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
    figsize=(15, 13)
)

merged.plot(
    ax=ax,
    color=merged["color"],
    edgecolor="black",
    linewidth=0.8
)


# =========================================================
# DISTRICT LABELS
# =========================================================

for _, row in merged.iterrows():

    rank_val = row.get("Rank")

    dist_name = row.get(
        "dist_clean"
    )

    if (
        pd.notna(rank_val)
        and pd.notna(dist_name)
    ):

        try:

            point = (
                row["geometry"]
                .representative_point()
            )

            ax.annotate(

                text=(
                    f"{int(rank_val)}\n"
                    f"{dist_name}"
                ),

                xy=(
                    point.x,
                    point.y
                ),

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
# MAP TITLE
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
# SAVE MAP
# =========================================================

map_file = (
    BASE_DIR /
    "Final_Maharashtra_Map.png"
)

fig.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)


# =========================================================
# DISPLAY MAP
# =========================================================

st.subheader(
    "📍 Maharashtra District Map"
)

st.image(
    str(map_file),
    caption=(
        "District-wise Social Economic "
        "Rank in Maharashtra – 2011"
    ),
    use_container_width=True
)


# =========================================================
# SUMMARY
# =========================================================

st.markdown("---")

st.subheader(
    "📊 Summary"
)


col1, col2, col3, col4 = st.columns(4)


valid_ranks = (
    df["Rank"]
    .dropna()
)


with col1:

    st.metric(
        "Total Districts",
        len(df)
    )


with col2:

    st.metric(
        "Highest Rank",
        int(valid_ranks.min())
        if len(valid_ranks) > 0
        else "N/A"
    )


with col3:

    st.metric(
        "Lowest Rank",
        int(valid_ranks.max())
        if len(valid_ranks) > 0
        else "N/A"
    )


with col4:

    st.metric(
        "Average Rank",
        round(
            valid_ranks.mean(),
            2
        )
        if len(valid_ranks) > 0
        else "N/A"
    )


# =========================================================
# RANKING TABLE
# =========================================================

st.markdown("---")

st.subheader(
    "📋 District Ranking Table"
)


table_df = df.copy()


table_df = table_df[
    [
        "District",
        "Rank"
    ]
].copy()


table_df = table_df.sort_values(
    by="Rank",
    ascending=True
)


table_df = table_df.reset_index(
    drop=True
)


table_df.index = (
    table_df.index + 1
)


table_df.index.name = "No."


# Use st.table instead of st.dataframe
st.table(
    table_df
)


# =========================================================
# DOWNLOAD CSV
# =========================================================

csv_data = table_df.to_csv(
    index=True
).encode(
    "utf-8"
)


st.download_button(

    label="⬇️ Download Ranking Table (CSV)",

    data=csv_data,

    file_name=(
        "Maharashtra_Social_Economic_Ranking_2011.csv"
    ),

    mime="text/csv"
)


# =========================================================
# DOWNLOAD MAP
# =========================================================

with open(
    map_file,
    "rb"
) as file:

    map_bytes = file.read()


st.download_button(

    label="⬇️ Download Maharashtra Map (PNG)",

    data=map_bytes,

    file_name=(
        "Maharashtra_Social_Economic_Map_2011.png"
    ),

    mime="image/png"
)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Source: Maharashtra District Ranking Data – 2011"
)
