import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------------------------
# 0.  Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Airbnb Listings Dashboard",
    page_icon="🏠",
    layout="wide"
)

# -------------------------------------------------
# 1.  Load & clean data
# -------------------------------------------------
DATA_FILE = "listings (2).csv.gz"       # name in your repo
df = pd.read_csv(DATA_FILE, compression="gzip")

# Clean "price" to numeric
df["price"] = (
    df["price"]
      .replace({r"[\$,]": ""}, regex=True)
      .astype(float, errors="ignore")
)

# -------------------------------------------------
# 2.  Sidebar filters
# -------------------------------------------------
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique())
sel_room   = st.sidebar.selectbox("Room type", room_types, index=0)

neighs = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
sel_neigh  = st.sidebar.selectbox("Neighbourhood", neighs, index=0)

p_min, p_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider(
    "Price range ($)",
    min_value=p_min,
    max_value=p_max,
    value=(p_min, p_max)              # default = full range so nothing is hidden
)

# -------------------------------------------------
# 3.  Apply filters
# -------------------------------------------------
flt = df.copy()
if sel_room != "All":
    flt = flt[flt["room_type"] == sel_room]
if sel_neigh != "All":
    flt = flt[flt["neighbourhood_group_cleansed"] == sel_neigh]
flt = flt[flt["price"].between(*sel_price)]

# If nothing left, show a friendly warning
if flt.empty:
    st.warning("⚠️ No listings match the current filter combination. "
               "Try widening your price range or choosing ‘All’.")
    st.stop()

# -------------------------------------------------
# 4.  Intro text
# -------------------------------------------------
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(
    f"Showing **{len(flt):,} listings** for "
    f"**{sel_room if sel_room != 'All' else 'all room types'}** "
    f"in **{sel_neigh if sel_neigh != 'All' else 'all neighbourhoods'}**, "
    f"priced **${sel_price[0]:,} – ${sel_price[1]:,}**."
)

# -------------------------------------------------
# 5.  Tabs
# -------------------------------------------------
tab_charts, tab_map, tab_data = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ---------- TAB: Charts ----------
with tab_charts:
    # interactive selection
    sel = alt.selection_single(fields=["room_type"], name="Pick",
                               bind="legend", empty="all")

    # 5a bar — avg price by room type
    avg = flt.groupby("room_type", as_index=False)["price"].mean()
    bar = (alt.Chart(avg)
           .mark_bar()
           .encode(
               x="room_type:N",
               y=alt.Y("price:Q", title="Avg price ($)"),
               color=alt.condition(sel, alt.value("#1f77b4"), alt.value("#d3d3d3")),
               tooltip=["room_type", alt.Tooltip("price:Q", format=".0f")]
           )
           .add_selection(sel)
           .properties(title="Average price by room type", width=600))

    # 5b histogram — linked
    hist = (alt.Chart(flt)
            .mark_bar(color="#1f77b4")
            .encode(
                x=alt.X("price:Q", bin=alt.Bin(maxbins=40), title="Price ($)"),
                y=alt.Y("count()", title="Listing count")
            )
            .transform_filter(sel)
            .properties(title="Price distribution", width=600))

    st.altair_chart(bar, use_container_width=True)
    st.altair_chart(hist, use_container_width=True)

# ---------- TAB: Map ----------
with tab_map:
    st.subheader("Listing locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# ---------- TAB: Data ----------
with tab_data:
    st.subheader("Filtered listings")
    st.dataframe(flt)

    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv,
                       file_name="filtered_listings.csv",
                       mime="text/csv")
