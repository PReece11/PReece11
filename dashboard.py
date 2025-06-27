import streamlit as st
import pandas as pd
import altair as alt

# ---------- Page settings ----------
st.set_page_config(
    page_title="Airbnb Listings Dashboard",
    page_icon="🏠",
    layout="wide"
)

# ---------- Load data ----------
DATA_PATH = "listings (2).csv.gz"   # <— make sure this name matches your repo
df = pd.read_csv(DATA_PATH, compression="gzip")

# Clean price column (remove $ and , then cast to float)
df["price"] = (
    df["price"]
      .replace({r"[\$,]": ""}, regex=True)
      .astype(float, errors="ignore")
)

# ---------- Sidebar filters ----------
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique())
selected_room = st.sidebar.selectbox("Room Type", room_types)

neigh_opts = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
selected_neigh = st.sidebar.selectbox("Neighbourhood", neigh_opts)

# Price slider (min/max rounded to nearest $10 for nicer UX)
pmin, pmax = int(df["price"].min()), int(df["price"].max())
selected_price = st.sidebar.slider(
    "Price Range ($)",
    min_value=pmin,
    max_value=pmax,
    value=(pmin, min(pmax, 500))  # default upper bound 500 for readability
)

# ---------- Apply filters ----------
filtered = df.copy()
if selected_room != "All":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_neigh != "All":
    filtered = filtered[filtered["neighbourhood_group_cleansed"] == selected_neigh]
filtered = filtered[filtered["price"].between(*selected_price)]

# ---------- App title ----------
st.title("🏠 Airbnb Listings Dashboard")

st.markdown(
    f"Listings for **{selected_room if selected_room!='All' else 'all room types'}** "
    f"in **{selected_neigh if selected_neigh!='All' else 'all neighbourhoods'}**, "
    f"priced **${selected_price[0]:,} – ${selected_price[1]:,}**"
)

# ------------------------------------------------------------
# Tabs: Charts | Map | Data
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ---------- TAB 1 : Charts ----------
with tab1:
    # Altair selection for interactive linking
    click = alt.selection_single(
        fields=["room_type"],
        bind="legend",
        name="Select",
        clear="doubleclick"
    )

    # ---- 1. Bar chart: avg price by room type ----
    avg_price = (
        filtered
        .groupby("room_type", as_index=False)["price"]
        .mean()
    )

    bar = (
        alt.Chart(avg_price)
        .mark_bar()
        .encode(
            x=alt.X("room_type:N", title="Room Type"),
            y=alt.Y("price:Q", title="Average Price ($)"),
            color=alt.condition(
                click, alt.value("#1f77b4"), alt.value("#d3d3d3")   
            ),
            tooltip=["room_type", alt.Tooltip("price:Q", format=".0f", title="Avg Price")]
        )
        .add_selection(click)
        .properties(title="Average Price by Room Type", width=600)
    )

    st.altair_chart(bar, use_container_width=True)

    # ---- 2. Histogram: price distribution, filtered by bar-click ----
    hist = (
        alt.Chart(filtered)
        .mark_bar(color="#1f77b4")
        .encode(
            x=alt.X("price:Q", bin=alt.Bin(maxbins=40), title="Price ($)"),
            y=alt.Y("count()", title="Number of Listings")
        )
        .transform_filter(click)       
        .properties(title="Price Distribution", width=600)
    )
    st.altair_chart(hist, use_container_width=True)

# ---------- TAB 2 : Map ----------
with tab2:
    st.subheader("Listing Locations")
    st.map(
        filtered[["latitude", "longitude"]].dropna(),
        zoom=10,
        use_container_width=True
    )

# ---------- TAB 3 : Data ----------
with tab3:
    st.subheader("Filtered Listings")
    st.dataframe(filtered)

    # Optional download button
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        csv,
        file_name="airbnb_filtered_listings.csv",
        mime="text/csv"
    )
