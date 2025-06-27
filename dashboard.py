import streamlit as st
import pandas as pd
import altair as alt

# ----------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")

# ----------------------------------------------------------------------------
# Load & clean data
# ----------------------------------------------------------------------------
df = pd.read_csv("listings (2).csv.gz", compression="gzip")
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
st.sidebar.header("🔍 Filters")
room_types = ["All"] + sorted(df["room_type"].dropna().unique())
sel_room = st.sidebar.selectbox("Room type", room_types)

neighs = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
sel_neigh = st.sidebar.selectbox("Neighbourhood", neighs)

p_min, p_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider("Price range ($)", p_min, p_max, (p_min, p_max))

# ----------------------------------------------------------------------------
# Filter data
# ----------------------------------------------------------------------------
flt = df.copy()
if sel_room != "All":
    flt = flt[flt["room_type"] == sel_room]
if sel_neigh != "All":
    flt = flt[flt["neighbourhood_group_cleansed"] == sel_neigh]
flt = flt[flt["price"].between(*sel_price)]

if flt.empty:
    st.warning("No listings match your filters. Try widening the price range.")
    st.stop()

# ----------------------------------------------------------------------------
# Title and tabs
# ----------------------------------------------------------------------------
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(f"Showing **{len(flt):,} listings** filtered by your selections.")

tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# =============================================================================
# 📊 CHARTS TAB
# =============================================================================
with tab1:
    st.subheader("Price analytics by room type")

    # Shared selection (legend or bar click)
    selection = alt.selection_single(fields=["room_type"], bind="legend", empty="all")

    # -- Bar chart (average price) --
    avg_price = flt.groupby("room_type", as_index=False)["price"].mean()
    bar_chart = (
        alt.Chart(avg_price)
        .mark_bar()
        .encode(
            x="room_type:N",
            y=alt.Y("price:Q", title="Average price ($)"),
            color=alt.condition(selection, alt.value("#1f77b4"), alt.value("#d3d3d3")),
            tooltip=["room_type", alt.Tooltip("price:Q", format=".0f")]
        )
        .add_selection(selection)
        .properties(title="Average price by room type", width=650)
    )

    # -- Scatter plot (linked) --
    scatter = (
        alt.Chart(flt)
        .mark_circle(size=60, opacity=0.4)
        .encode(
            x=alt.X("minimum_nights:Q", title="Minimum nights"),
            y=alt.Y("price:Q", title="Price ($)"),
            color=alt.Color("room_type:N", legend=None),
            tooltip=["name", "room_type", "price", "minimum_nights"]
        )
        .transform_filter(selection)               # keeps it linked
        .properties(title="Price vs Minimum Nights", width=650)
    )

    # Display charts
    st.altair_chart(bar_chart, use_container_width=True)
    st.altair_chart(scatter, use_container_width=True)

# =============================================================================
# 🗺️ MAP TAB
# =============================================================================
with tab2:
    st.subheader("Listing Locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# =============================================================================
# 📋 DATA TAB
# =============================================================================
with tab3:
    st.subheader("Filtered Listings")
    st.dataframe(flt, use_container_width=True)

    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "filtered_listings.csv", "text/csv")
