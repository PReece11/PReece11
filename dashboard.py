import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --------------------------------------------------
# Page & Altair setup
# --------------------------------------------------
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")
alt.data_transformers.disable_max_rows()      # allow >5k rows

# --------------------------------------------------
# 1  Load & clean data
# --------------------------------------------------
DATA_FILE = "listings (2).csv.gz"             # adjust name if different
df = pd.read_csv(DATA_FILE, compression="gzip")

# price → numeric
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float, errors="ignore")

# --------------------------------------------------
# 2  Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique())
sel_room   = st.sidebar.selectbox("Room type", room_types)

neigh_opts = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
sel_neigh  = st.sidebar.selectbox("Neighbourhood", neigh_opts)

p_min, p_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider("Price range ($)", p_min, p_max, (p_min, p_max))

# --------------------------------------------------
# 3  Apply filters
# --------------------------------------------------
flt = df.copy()
if sel_room != "All":
    flt = flt[flt["room_type"] == sel_room]
if sel_neigh != "All":
    flt = flt[flt["neighbourhood_group_cleansed"] == sel_neigh]
flt = flt[flt["price"].between(*sel_price)]

if flt.empty:
    st.warning("No listings match your filters. Try widening the price range.")
    st.stop()

# --------------------------------------------------
# 4  Layout tabs
# --------------------------------------------------
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(
    f"Showing **{len(flt):,} listings** "
    f"({sel_room if sel_room!='All' else 'all room types'}, "
    f"{sel_neigh if sel_neigh!='All' else 'all neighbourhoods'}, "
    f"${sel_price[0]}–${sel_price[1]})"
)

tab_charts, tab_map, tab_data = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ============================================================================
# 📊 Charts tab
# ============================================================================
with tab_charts:
    st.subheader("Average price & estimated revenue")

    # shared Altair selection
    selection = alt.selection_single(fields=["room_type"], bind="legend", empty="all")

    # --‑ Bar chart: avg price per room type
    avg_price = flt.groupby("room_type", as_index=False)["price"].mean()
    bar = (
        alt.Chart(avg_price)
        .mark_bar()
        .encode(
            x=alt.X("room_type:N", title="Room type"),
            y=alt.Y("price:Q", title="Average price ($)"),
            color=alt.condition(selection, alt.value("#1f77b4"), alt.value("#d3d3d3")),
            tooltip=["room_type", alt.Tooltip("price:Q", format=".0f")]
        )
        .add_selection(selection)
        .properties(title="Average price by room type", width=650)
    )
    st.altair_chart(bar, use_container_width=True)

    # --‑ Scatter plot: estimated revenue (linked)
    rev_data = flt.dropna(subset=["estimated_revenue_l365d"]).copy()
    # jitter x for clearer dots & facet by room type
    rev_data["jitter"] = np.random.normal(0, 0.15, size=len(rev_data))

    scatter = (
        alt.Chart(rev_data)
        .mark_circle(size=45, opacity=0.45)
        .encode(
            x=alt.X("jitter:Q", axis=None, title=None),
            column=alt.Column("room_type:N", title="Room type",
                              header=alt.Header(labelAngle=-45)),
            y=alt.Y("estimated_revenue_l365d:Q",
                    title="Est. revenue last 365 days ($)",
                    scale=alt.Scale(zero=False)),
            color=alt.Color("room_type:N", legend=None),
            tooltip=["name", "room_type",
                     alt.Tooltip("estimated_revenue_l365d:Q",
                                 format=",.0f", title="Est. revenue")]
        )
        .transform_filter(selection)
        .properties(title="Estimated revenue per listing", width=180, height=320)
    )
    st.altair_chart(scatter, use_container_width=True)

# ============================================================================
# 🗺️ Map tab
# ============================================================================
with tab_map:
    st.subheader("Listing locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# ============================================================================
# 📋 Data tab
# ============================================================================
with tab_data:
    st.subheader("Filtered listings")
    st.dataframe(flt, use_container_width=True)

    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  Download CSV", csv,
                       file_name="filtered_listings.csv",
                       mime="text/csv")
