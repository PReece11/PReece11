import streamlit as st
import pandas as pd
import altair as alt

# ---------- Page config ----------
st.set_page_config(page_title="Airbnb Dashboard",
                   page_icon="🏠",
                   layout="wide")

# ---------- Load & clean data ----------
DATA_FILE = "listings (2).csv.gz"               # <— make sure the name matches your repo
df = pd.read_csv(DATA_FILE, compression="gzip")

# Clean price column
df["price"] = (
    df["price"]
      .replace({r"[\$,]": ""}, regex=True)
      .astype(float, errors="ignore")
)

# ---------- Sidebar filters ----------
st.sidebar.header("🔍 Filters")

room_types = ["All"] + sorted(df["room_type"].dropna().unique())
sel_room   = st.sidebar.selectbox("Room type", room_types, index=0)

neigh_opts = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique())
sel_neigh  = st.sidebar.selectbox("Neighbourhood", neigh_opts, index=0)

p_min, p_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider("Price range ($)", p_min, p_max, (p_min, p_max))

# ---------- Apply filters ----------
flt = df.copy()
if sel_room != "All":
    flt = flt[flt["room_type"] == sel_room]
if sel_neigh != "All":
    flt = flt[flt["neighbourhood_group_cleansed"] == sel_neigh]
flt = flt[flt["price"].between(*sel_price)]

# Warn if no data
if flt.empty:
    st.warning("⚠️ No listings match these filters. "
               "Try widening the price range or selecting ‘All’.")
    st.stop()

# ---------- Intro ----------
st.title("🏠 Airbnb Listings Dashboard")
st.markdown(
    f"Showing **{len(flt):,} listings** for "
    f"**{sel_room if sel_room!='All' else 'all room types'}** "
    f"in **{sel_neigh if sel_neigh!='All' else 'all neighbourhoods'}**, "
    f"priced **${sel_price[0]:,} – ${sel_price[1]:,}**."
)

# ---------- Tabs ----------
tab_charts, tab_map, tab_data = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ==============================
# TAB 1 – CHARTS
# ==============================
with tab_charts:
    st.subheader("Price analytics by room type")
    
    # Altair selection (legend or bar click)
    selection = alt.selection_single(
        fields=["room_type"],
        bind="legend",
        empty="all",
        name="Select"
    )

    # ----- Bar chart: average price -----
    avg_price = (
        flt.groupby("room_type", as_index=False)["price"]
           .mean()
    )

    bar = (alt.Chart(avg_price)
           .mark_bar()
           .encode(
               x=alt.X("room_type:N", title="Room type"),
               y=alt.Y("price:Q", title="Average price ($)"),
               color=alt.condition(selection,
                                   alt.value("#1f77b4"),
                                   alt.value("#d3d3d3")),
               tooltip=["room_type",
                        alt.Tooltip("price:Q", format=".0f", title="Avg price")]
           )
           .add_selection(selection)
           .properties(title="Average price by room type", width=650)
    )

    # ----- Box plot: linked distribution -----
    box = (alt.Chart(flt)
           .mark_boxplot(extent="min-max")
           .encode(
               x=alt.X("room_type:N", title="Room type"),
               y=alt.Y("price:Q", title="Price ($)"),
               color=alt.Color("room_type:N", legend=None),
               tooltip=["room_type", "price"]
           )
           .transform_filter(selection)        # link to bar selection
           .properties(title="Price distribution (box plot)", width=650)
    )

    st.altair_chart(bar, use_container_width=True)
    st.altair_chart(box, use_container_width=True)

# ==============================
# TAB 2 – MAP
# ==============================
with tab_map:
    st.subheader("Listing locations")
    st.map(flt[["latitude", "longitude"]].dropna(), zoom=10)

# ==============================
# TAB 3 – DATA
# ==============================
with tab_data:
    st.subheader("Filtered listings")
    st.dataframe(flt, use_container_width=True)

    csv = flt.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV",
                       csv,
                       file_name="filtered_listings.csv",
                       mime="text/csv")
