import json
import os
import urllib.request
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from matplotlib import patheffects as pe

# --- Step 1: Raw GeoJSON Download ---
geojson_file = "maharashtra_district.geojson"
raw_url = "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/states/maharashtra.geojson"

if not os.path.exists(geojson_file) or os.path.getsize(geojson_file) < 50000:
    print("Downloading correct GeoJSON file...")
    urllib.request.urlretrieve(raw_url, geojson_file)
    print("Downloaded successfully!")

# --- Step 2: Files Load karein ---
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

excel_file = str(existing_file)
df = pd.read_excel(excel_file)
print(f"Loaded Excel file: {excel_file}")

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

# --- 3 DISTRICTS KE NAAM UPDATE KAREIN ---
rename_map = {
    # Ahmadnagar -> Ahilyanagar
    "Ahmadnagar": "Ahilyanagar",
    "Ahmednagar": "Ahilyanagar",
    # Aurangabad -> Chatrapati Sambhaji Nagar
    "Aurangabad": "Chatrapati Sambhaji Nagar",
    "Chhatrapati Sambhajinagar": "Chatrapati Sambhaji Nagar",
    # Osmanabad -> Dharashiv
    "Osmanabad": "Dharashiv",
}

# Dono me replace karein taaki merge bhi ho aur map par naya naam dikhe
map_df["dist_clean"] = map_df["dist_clean"].replace(rename_map)
df["dist_clean"] = df["dist_clean"].replace(rename_map)

# --- MUMBAI ADDITION / HANDLING ---
if not df["dist_clean"].str.contains("Mumbai").any():
    mumbai_data = pd.DataFrame([{
        "District": "Mumbai",
        "dist_clean": "Mumbai",
        "Rank": 1
    }])
    df = pd.concat([df, mumbai_data], ignore_index=True)

mumbai_rank = df.loc[df["dist_clean"].str.contains("Mumbai"), "Rank"].values
if len(mumbai_rank) > 0:
    target_rank = mumbai_rank[0]
    for m_variant in ["Mumbai", "Mumbai City", "Mumbai Suburban"]:
        if not (df["dist_clean"] == m_variant).any():
            df = pd.concat([df, pd.DataFrame([{"District": m_variant, "dist_clean": m_variant, "Rank": target_rank}])], ignore_index=True)

# --- Step 3: Merge karein ---
merged = map_df.merge(df, on="dist_clean", how="left")

# --- Step 4: Color Function (Rank ke basis par) ---
def get_color(rank):
    if pd.isna(rank):
        return "#D3D3D3"  # Grey (No data)
    elif rank <= 12:
        return "#478848"  # Green (High)
    elif rank <= 24:
        return "#F8B756"  # Orange/Yellow (Medium)
    else:
        return "#E85342"  # Red (Low)

merged["color"] = merged["Rank"].apply(get_color)

# --- Step 5: Plotting ---
fig, ax = plt.subplots(figsize=(12, 10))
merged.plot(ax=ax, color=merged["color"], edgecolor="black", linewidth=0.8)

# Legend setup
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

# Add rank and district-name labels (Naye naamo ke sath)
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
            path_effects=[
                pe.withStroke(linewidth=2, foreground="white", alpha=0.9)
            ],
        )

ax.set_title(
    "District-wise Social Economic Rank in Maharashtra",
    fontsize=20,
    fontweight="bold",
    pad=20
)
ax.set_axis_off()
plt.tight_layout()
plt.savefig("Final_Maharashtra_Map.png", dpi=300)
plt.show()
print("Saved: Final_Maharashtra_Map.png")
