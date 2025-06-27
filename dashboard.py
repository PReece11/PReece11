import streamlit as st
import pandas as pd
import altair as alt

# Set page config
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("listings (2).csv.gz", compression="gzip")
    df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)
    df["estimated_revenue_l365d"] = df["price"] * df["availability_365"]
    return df

df = load_data()

# Sidebar Filters
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

# Title and summary
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(f"Showing **{len(flt):,} listings** filtered by your selections.")

# Tabs
tab_charts, tab_map, tab_data = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ============================
# 📊 CHARTS TAB
# ============================
with tab_charts:
    st.subheader("Price analytics by room type")

    # Selection for linking charts
    selection = alt.selection_single(fields=["room_type"], bind="legend", empty="all")

    # Bar Chart: Average Price
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
        .properties(title="Average price by room type", width=500, height=400)
    )

    # Scatterplot: Estimated Revenue
    scatter = (
        alt.Chart(flt)
        .mark_circle(size=60, opacity=0.5)
        .encode(
            x=alt.X("room_type:N", title="Room type"),
            y=alt.Y("estimated_revenue_l365d:Q", title="Estimated revenue (last 365 days $)"),
            color=alt.Color("room_type:N", legend=None),
            tooltip=["name", "room_type", "price", "estimated_revenue_l365d"]
        )
        .transform_filter(selection)
        .properties(title="Estimated revenue by room type", width=500, height=400)
    )

    # Display side-by-side
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(bar, use_container_width=True)
    with col2:
        st.altair_chart(scatter, use_container_width=True)

# ============================
# 🗺️ MAP TAB
# ============================
with tab_map:
    st.subheader("Listing Locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# ============================
# 📋 DATA TAB
# ============================
with tab_data:
    st.subheader("Filtered Listings")
    st.dataframe(flt, use_container_width=True)
    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "filtered_listings.csv", "text/csv")
