import streamlit as st
import pandas as pd
import altair as alt

# Page configuration
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")

# Load & clean data
df = pd.read_csv("listings (2).csv.gz", compression="gzip")
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)

# Sidebar filters
st.sidebar.header("🔍 Filters")
room_types = ["All"] + sorted(df["room_type"].dropna().unique())
sel_room = st.sidebar.selectbox("Room type", room_types)

neighs = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
sel_neigh = st.sidebar.selectbox("Neighbourhood", neighs)

p_min, p_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider("Price range ($)", p_min, p_max, (p_min, p_max))

# Filter data
flt = df.copy()
if sel_room != "All":
    flt = flt[flt["room_type"] == sel_room]
if sel_neigh != "All":
    flt = flt[flt["neighbourhood_group_cleansed"] == sel_neigh]
flt = flt[flt["price"].between(*sel_price)]

# Show message if no data
if flt.empty:
    st.warning("No listings match your filters. Try widening the price range.")
    st.stop()

# Title and summary
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(f"Showing **{len(flt):,} listings** filtered by your selections.")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ====================================
# 📊 CHARTS TAB
# ====================================
with tab1:
    st.subheader("Price analytics by room type")

    selection = alt.selection_single(fields=["room_type"], bind="legend", empty="all")

    avg_price = flt.groupby("room_type", as_index=False)["price"].mean()
    bar_chart = (
        alt.Chart(avg_price)
        .mark_bar()
        .encode(
            x=alt.X("room_type:N", title="Room type"),
            y=alt.Y("price:Q", title="Average price ($)"),
            color=alt.condition(selection, alt.value("#1f77b4"), alt.value("#d3d3d3")),
            tooltip=["room_type", alt.Tooltip("price:Q", format=".0f", title="Avg price")]
        )
        .add_selection(selection)
        .properties(title="Average price by room type", width=650)
    )

    # Show all room types even if filtered, to always have box plot visible
    box_data = df[df["price"].between(*sel_price)]
    if sel_neigh != "All":
        box_data = box_data[box_data["neighbourhood_group_cleansed"] == sel_neigh]

    box_chart = (
        alt.Chart(box_data)
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X("room_type:N", title="Room type"),
            y=alt.Y("price:Q", title="Price ($)"),
            color=alt.Color("room_type:N", legend=None),
            tooltip=["room_type", "price"]
        )
        .transform_filter(selection)
        .properties(title="Price distribution by room type (box plot)", width=650)
    )

    st.altair_chart(bar_chart, use_container_width=True)
    st.altair_chart(box_chart, use_container_width=True)

# ====================================
# 🗺️ MAP TAB
# ====================================
with tab2:
    st.subheader("Listing Locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# ====================================
# 📋 DATA TAB
# ====================================
with tab3:
    st.subheader("Filtered Listings")
    st.dataframe(flt, use_container_width=True)
    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "filtered_listings.csv", "text/csv")
