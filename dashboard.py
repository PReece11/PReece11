import pandas as pdAdd commentMore actions
import altair as alt

# Set page config
st.set_page_config(page_title="Airbnb Dashboard", page_icon="🏠", layout="wide")
# ---------- Page settings ----------
st.set_page_config(
    page_title="Airbnb Listings Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Load the compressed dataset
df = pd.read_csv("listings (2).csv.gz", compression="gzip")
# ---------- Load data ----------
DATA_PATH = "listings (2).csv.gz"   # <— make sure this name matches your repo
df = pd.read_csv(DATA_PATH, compression="gzip")

# Clean price column
df["price"] = df["price"].replace({r"[\$,]": ""}, regex=True).astype(float)
# Clean price column (remove $ and , then cast to float)
df["price"] = (
    df["price"]
      .replace({r"[\$,]": ""}, regex=True)
      .astype(float, errors="ignore")
)

# Sidebar Filters
# ---------- Sidebar filters ----------
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique().tolist())
room_types = ["All"] + sorted(df["room_type"].dropna().unique())
selected_room = st.sidebar.selectbox("Room Type", room_types)

neighborhoods = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique().tolist())
selected_neigh = st.sidebar.selectbox("Neighbourhood", neighborhoods)
neigh_opts = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
selected_neigh = st.sidebar.selectbox("Neighbourhood", neigh_opts)

price_min = int(df["price"].min())
price_max = int(df["price"].max())
selected_price = st.sidebar.slider("Price Range", min_value=price_min, max_value=price_max, value=(50, 500))
# Price slider (min/max rounded to nearest $10 for nicer UX)
pmin, pmax = int(df["price"].min()), int(df["price"].max())
selected_price = st.sidebar.slider(
    "Price Range ($)",
    min_value=pmin,
    max_value=pmax,
    value=(pmin, min(pmax, 500))  # default upper bound 500 for readability
)

# Filter Data
# ---------- Apply filters ----------
filtered = df.copy()
if selected_room != "All":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_neigh != "All":
    filtered = filtered[filtered["neighbourhood_group_cleansed"] == selected_neigh]
filtered = filtered[filtered["price"].between(*selected_price)]

# Dashboard Title
# ---------- App title ----------
st.title("🏠 Airbnb Listings Dashboard")

# Overview Text
st.markdown(
    f"Showing listings for **{selected_room if selected_room != 'All' else 'all room types'}** "
    f"in **{selected_neigh if selected_neigh != 'All' else 'all neighborhoods'}**, "
    f"priced between **${selected_price[0]}–${selected_price[1]}**."
    f"Listings for **{selected_room if selected_room!='All' else 'all room types'}** "
    f"in **{selected_neigh if selected_neigh!='All' else 'all neighbourhoods'}**, "
    f"priced **${selected_price[0]:,} – ${selected_price[1]:,}**"
)

# Visualization Tabs
# ------------------------------------------------------------
# Tabs: Charts | Map | Data
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ---------- TAB 1 : Charts ----------
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
    st.map(filtered[["latitude", "longitude"]].dropna())
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
