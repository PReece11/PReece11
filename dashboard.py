import streamlit as st
import pandas as pd
import altair as alt

# Set page config
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")

# Load the compressed dataset
df = pd.read_csv("listings (2).csv.gz", compression="gzip")

# Clean price column
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)

# Sidebar Filters
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique().tolist())
selected_room = st.sidebar.selectbox("Room Type", room_types)

neighborhoods = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique().tolist())
selected_neigh = st.sidebar.selectbox("Neighbourhood", neighborhoods)

price_min = int(df["price"].min())
price_max = int(df["price"].max())
selected_price = st.sidebar.slider("Price Range", min_value=price_min, max_value=price_max, value=(50, 500))

# Filter Data
filtered = df.copy()
if selected_room != "All":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_neigh != "All":
    filtered = filtered[filtered["neighbourhood_group_cleansed"] == selected_neigh]
filtered = filtered[filtered["price"].between(*selected_price)]

# Dashboard Title
st.title("🏠 Airbnb Listings Dashboard")

# Overview Text
st.markdown(
    f"Showing listings for **{selected_room if selected_room != 'All' else 'all room types'}** "
    f"in **{selected_neigh if selected_neigh != 'All' else 'all neighborhoods'}**, "
    f"priced between **${selected_price[0]}–${selected_price[1]}**."
)

# Visualization Tabs
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

with tab1:
    st.subheader("Average Price by Room Type")
    avg_price = filtered.groupby("room_type")["price"].mean().reset_index()
    bar_chart = alt.Chart(avg_price).mark_bar().encode(
        x=alt.X("room_type:N", title="Room Type"),
        y=alt.Y("price:Q", title="Average Price ($)"),
        tooltip=["room_type", "price"]
    ).properties(width=600)
    st.altair_chart(bar_chart, use_container_width=True)

    st.subheader("Price Distribution")
    hist_chart = alt.Chart(filtered).mark_bar().encode(
        x=alt.X("price:Q", bin=alt.Bin(maxbins=40), title="Price ($)"),
        y=alt.Y("count()", title="Number of Listings")
    ).properties(width=600)
    st.altair_chart(hist_chart, use_container_width=True)

with tab2:
    st.subheader("Listing Locations")
    st.map(filtered[["latitude", "longitude"]].dropna())

with tab3:
    st.subheader("Filtered Listings")
    st.dataframe(filtered)
