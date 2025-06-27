# app.py
import pandas as pd
import altair as alt
import streamlit as st

# ---------- 1. Load & clean data ----------
df = pd.read_csv("listings.csv")
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)

# ---------- 2. Sidebar filters ----------
st.sidebar.header("🔍 Filters")

acc_options = ["All"] + sorted(df["accommodates"].unique())
selected_acc = st.sidebar.selectbox("Accommodates", acc_options)

room_types = ["All"] + sorted(df["room_type"].unique())
selected_room = st.sidebar.selectbox("Room type", room_types)

neigh_options = ["All"] + sorted(df["neighbourhood"].unique())
selected_neigh = st.sidebar.selectbox("Neighborhood", neigh_options)

min_nights = st.sidebar.slider(
    "Minimum nights", int(df["minimum_nights"].min()), int(df["minimum_nights"].max()), (1, 30)
)

pmin, pmax = int(df["price"].min()), int(df["price"].max())
selected_price = st.sidebar.slider("Price range ($)", pmin, pmax, (pmin, pmax))

# ---------- 3. Apply filters ----------
filtered = df.copy()
if selected_acc != "All":
    filtered = filtered[filtered["accommodates"] == selected_acc]
if selected_room != "All":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_neigh != "All":
    filtered = filtered[filtered["neighbourhood"] == selected_neigh]

filtered = filtered[filtered["minimum_nights"].between(*min_nights)]
filtered = filtered[filtered["price"].between(*selected_price)]

# ---------- 4. Build visuals ----------
# 4a. Average price bar chart
avg_price = filtered.groupby("room_type")["price"].mean().reset_index()
bar_chart = (
    alt.Chart(avg_price)
    .mark_bar()
    .encode(
        x=alt.X("room_type:N", title="Room type"),
        y=alt.Y("price:Q", title="Average price ($)"),
        tooltip=["room_type", "price"],
    )
    .properties(title="Average price by room type")
)

# 4b. Price distribution histogram
hist_chart = (
    alt.Chart(filtered)
    .mark_bar()
    .encode(
        x=alt.X("price:Q", bin=alt.Bin(maxbins=50), title="Price ($)"),
        y=alt.Y("count()", title="Number of listings"),
        tooltip=["count()"],
    )
    .properties(title="Distribution of listing prices")
)

# ---------- 5. Layout with tabs ----------
st.title("🏠 Airbnb Listings Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📄 Data table", "📊 Avg price chart", "📈 Price distribution", "🗺️ Map"]
)

with tab1:
    st.subheader("Filtered listings")
    st.dataframe(filtered)

with tab2:
    st.subheader("Average price by room type")
    st.altair_chart(bar_chart, use_container_width=True)

with tab3:
    st.subheader("Distribution of listing prices")
    st.altair_chart(hist_chart, use_container_width=True)

with tab4:
    st.subheader("Listing map")
    st.map(filtered[["latitude", "longitude"]])
