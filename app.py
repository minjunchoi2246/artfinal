
import math
from datetime import datetime
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RATINGS_PATH = DATA_DIR / "ratings.csv"

st.set_page_config(
    page_title="Korean Highway Rest Stop Food Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Data loading ----------
@st.cache_data
def load_data():
    rest_stops = pd.read_csv(DATA_DIR / "rest_stops.csv")
    menus = pd.read_csv(DATA_DIR / "menu_items.csv")
    stores = pd.read_csv(DATA_DIR / "stores.csv")

    if RATINGS_PATH.exists():
        ratings = pd.read_csv(RATINGS_PATH)
    else:
        ratings = pd.DataFrame(columns=["created_at", "rest_stop_id", "rating", "comment"])

    return rest_stops, menus, stores, ratings


def format_price(value):
    try:
        return f"₩{int(value):,}"
    except Exception:
        return value


def display_menu_table(df):
    show = df.copy()
    show["Price"] = show["price_krw"].apply(format_price)
    show = show.rename(
        columns={
            "food_area": "Food Area",
            "menu_item": "Menu Item",
            "food_category": "Food Category",
            "availability": "Available Time",
            "is_signature": "Signature Food",
            "recommended": "Recommended",
            "sample_rating": "Sample Rating",
        }
    )
    columns = [
        "Food Area",
        "Menu Item",
        "Food Category",
        "Price",
        "Available Time",
        "Signature Food",
        "Recommended",
        "Sample Rating",
    ]
    st.dataframe(show[columns], use_container_width=True, hide_index=True)


def display_store_table(df):
    show = df.copy().rename(
        columns={
            "food_area": "Food Area",
            "store_type": "Store Type",
            "description": "What You Can Find",
            "operating_hours": "Opening Hours",
        }
    )
    st.dataframe(
        show[["Food Area", "Store Type", "What You Can Find", "Opening Hours"]],
        use_container_width=True,
        hide_index=True,
    )


def nearest_rest_stop(lat, lon, rest_stops):
    if lat is None or lon is None:
        return None

    best_id = None
    best_dist = 10**9

    for _, row in rest_stops.iterrows():
        d = math.sqrt((float(row["latitude"]) - lat) ** 2 + (float(row["longitude"]) - lon) ** 2)
        if d < best_dist:
            best_dist = d
            best_id = row["rest_stop_id"]

    # Marker clicks are usually very close. This threshold avoids accidental map clicks.
    return best_id if best_dist < 0.08 else None


def build_popup(rest_stop, menus, stores):
    rid = rest_stop["rest_stop_id"]
    menu_preview = menus[menus["rest_stop_id"] == rid].head(5)
    store_preview = stores[stores["rest_stop_id"] == rid].head(4)

    store_lines = "".join(
        f"<li><b>{row['food_area']}</b> · {row['operating_hours']}</li>"
        for _, row in store_preview.iterrows()
    )
    menu_lines = "".join(
        f"<li>{row['menu_item']} — <b>{format_price(row['price_krw'])}</b></li>"
        for _, row in menu_preview.iterrows()
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 310px;">
        <h4 style="margin-bottom: 4px;">{rest_stop['rest_stop_name']}</h4>
        <div style="font-size: 12px; color: #555; margin-bottom: 8px;">
            {rest_stop['direction']} · {rest_stop['highway_route']} · {rest_stop['region']}
        </div>
        <div style="font-size: 12px; margin-bottom: 8px;">
            <b>General Hours:</b> {rest_stop['general_hours']}
        </div>
        <div style="font-size: 12px; margin-bottom: 4px;"><b>Food Areas</b></div>
        <ul style="font-size: 12px; padding-left: 18px; margin-top: 2px;">{store_lines}</ul>
        <div style="font-size: 12px; margin-bottom: 4px;"><b>Menu Preview</b></div>
        <ul style="font-size: 12px; padding-left: 18px; margin-top: 2px;">{menu_lines}</ul>
        <div style="font-size: 11px; color: #777; margin-top: 8px;">
            Click the marker, then check the detail panel below the map.
        </div>
    </div>
    """
    return folium.Popup(html, max_width=340)


def make_map(filtered_rest_stops, menus, stores):
    m = folium.Map(
        location=[36.35, 127.8],
        zoom_start=7,
        tiles="CartoDB positron",
        control_scale=True,
    )

    for _, rs in filtered_rest_stops.iterrows():
        is_high = rs["traffic_group"] == "High-traffic"
        is_boost = rs["is_corridor_boost"] == "Yes"

        if is_high:
            color = "red"
            icon = "star"
        elif is_boost:
            color = "green"
            icon = "cutlery"
        else:
            color = "blue"
            icon = "cutlery"

        tooltip = f"{rs['rest_stop_name']} · {rs['direction']}"

        folium.Marker(
            location=[rs["latitude"], rs["longitude"]],
            tooltip=tooltip,
            popup=build_popup(rs, menus, stores),
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(m)

    return m


# ---------- App ----------
rest_stops, menus, stores, ratings = load_data()

st.title("Korean Highway Rest Stop Food Dashboard")
st.caption(
    "A map-based dashboard for browsing rest stop food areas, menus, prices, opening hours, and traveler ratings."
)

with st.sidebar:
    st.header("Explore Rest Stops")

    view_mode = st.radio(
        "Dashboard View",
        [
            "National overview",
            "High-traffic rest stops",
            "Seoul–Chungcheong–Jeolla corridor",
            "All rest stops",
        ],
        index=0,
    )

    route_options = ["All routes"] + sorted(rest_stops["highway_route"].dropna().unique().tolist())
    selected_route = st.selectbox("Highway Route", route_options)

    region_options = ["All regions"] + sorted(rest_stops["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Region", region_options)

    category_options = ["All food categories"] + sorted(menus["food_category"].dropna().unique().tolist())
    selected_category = st.selectbox("Food Category", category_options)

    keyword = st.text_input("Search by rest stop or menu", placeholder="e.g. Udon, Jeonju, Hoengseong")

    st.divider()
    st.markdown(
        """
        **Marker guide**  
        🔴 High-traffic focus  
        🟢 Reinforced Chungcheong / Jeolla corridor  
        🔵 Other national rest stops
        """
    )

filtered = rest_stops.copy()

if view_mode == "High-traffic rest stops":
    filtered = filtered[filtered["traffic_group"] == "High-traffic"]
elif view_mode == "Seoul–Chungcheong–Jeolla corridor":
    filtered = filtered[filtered["is_corridor_boost"] == "Yes"]
elif view_mode == "National overview":
    # Keep the dashboard national by default, but prioritize high-traffic and corridor data visually.
    filtered = filtered.copy()
elif view_mode == "All rest stops":
    filtered = filtered.copy()

if selected_route != "All routes":
    filtered = filtered[filtered["highway_route"] == selected_route]

if selected_region != "All regions":
    filtered = filtered[filtered["region"] == selected_region]

if keyword.strip():
    q = keyword.strip().lower()
    matched_menu_ids = menus[menus["menu_item"].str.lower().str.contains(q, na=False)]["rest_stop_id"].unique()
    filtered = filtered[
        filtered["rest_stop_name"].str.lower().str.contains(q, na=False)
        | filtered["highway_route"].str.lower().str.contains(q, na=False)
        | filtered["rest_stop_id"].isin(matched_menu_ids)
    ]

if selected_category != "All food categories":
    ids = menus[menus["food_category"] == selected_category]["rest_stop_id"].unique()
    filtered = filtered[filtered["rest_stop_id"].isin(ids)]

if filtered.empty:
    st.warning("No rest stops match your current filters. Try clearing one of the filters.")
    st.stop()

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rest Stops Shown", f"{len(filtered):,}")
col2.metric("Menu Items Available", f"{menus[menus['rest_stop_id'].isin(filtered['rest_stop_id'])].shape[0]:,}")
col3.metric("Food Areas / Stores", f"{stores[stores['rest_stop_id'].isin(filtered['rest_stop_id'])].shape[0]:,}")
col4.metric(
    "High-traffic Stops",
    f"{filtered[filtered['traffic_group'] == 'High-traffic'].shape[0]:,}",
)

st.subheader("Map View")
st.write(
    "Click a rest stop marker to open a food preview popup. The detail panel below the map will also update to the nearest clicked marker."
)

map_col, list_col = st.columns([2.1, 1])

with map_col:
    m = make_map(filtered, menus, stores)
    map_data = st_folium(
        m,
        height=560,
        width=None,
        returned_objects=["last_object_clicked"],
        use_container_width=True,
    )

with list_col:
    st.markdown("### Rest Stop Selector")
    select_labels = (
        filtered["rest_stop_name"]
        + " · "
        + filtered["direction"]
        + " · "
        + filtered["highway_route"]
    ).tolist()
    label_to_id = dict(zip(select_labels, filtered["rest_stop_id"]))

    default_id = None
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        default_id = nearest_rest_stop(clicked.get("lat"), clicked.get("lng"), filtered)

    if default_id and default_id in filtered["rest_stop_id"].values:
        default_idx = filtered["rest_stop_id"].tolist().index(default_id)
    else:
        default_idx = 0

    selected_label = st.selectbox("Choose a rest stop", select_labels, index=default_idx)
    selected_id = label_to_id[selected_label]

    selected_rs = rest_stops[rest_stops["rest_stop_id"] == selected_id].iloc[0]
    st.markdown("### Quick Summary")
    st.write(f"**{selected_rs['rest_stop_name']}**")
    st.write(f"{selected_rs['direction']} · {selected_rs['highway_route']}")
    st.write(f"Region: {selected_rs['region']}")
    st.write(f"General hours: {selected_rs['general_hours']}")
    st.write(selected_rs["short_description"])

selected_rs = rest_stops[rest_stops["rest_stop_id"] == selected_id].iloc[0]
selected_menus = menus[menus["rest_stop_id"] == selected_id].copy()
selected_stores = stores[stores["rest_stop_id"] == selected_id].copy()

st.divider()
st.subheader(f"Food Details — {selected_rs['rest_stop_name']} ({selected_rs['direction']})")

detail_col1, detail_col2 = st.columns([1, 1])

with detail_col1:
    st.markdown("### Food Areas and Opening Hours")
    display_store_table(selected_stores)

with detail_col2:
    st.markdown("### Signature and Recommended Menu")
    highlights = selected_menus[
        (selected_menus["is_signature"] == "Yes") | (selected_menus["recommended"] == "Yes")
    ].copy()
    display_menu_table(highlights)

st.markdown("### Full Menu")
display_menu_table(selected_menus)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_price = px.bar(
        selected_menus.sort_values("price_krw", ascending=False),
        x="menu_item",
        y="price_krw",
        color="food_category",
        title="Menu Price Comparison",
        labels={
            "menu_item": "Menu Item",
            "price_krw": "Price (KRW)",
            "food_category": "Food Category",
        },
    )
    fig_price.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_price, use_container_width=True)

with chart_col2:
    category_counts = (
        selected_menus.groupby("food_category")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    fig_cat = px.pie(
        category_counts,
        names="food_category",
        values="count",
        title="Food Category Mix",
        labels={"food_category": "Food Category", "count": "Number of Menu Items"},
    )
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()
st.subheader("Traveler Rating")

rating_col1, rating_col2 = st.columns([1, 2])
with rating_col1:
    rating_value = st.slider("Your rating", min_value=1, max_value=5, value=4)
with rating_col2:
    rating_comment = st.text_input("Short comment", placeholder="e.g. Good for a quick meal before Daejeon.")

if st.button("Save Rating"):
    new_row = pd.DataFrame(
        [
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "rest_stop_id": selected_id,
                "rating": rating_value,
                "comment": rating_comment,
            }
        ]
    )

    existing = pd.read_csv(RATINGS_PATH) if RATINGS_PATH.exists() else pd.DataFrame(
        columns=["created_at", "rest_stop_id", "rating", "comment"]
    )
    updated = pd.concat([existing, new_row], ignore_index=True)
    updated.to_csv(RATINGS_PATH, index=False)
    st.success("Rating saved. Refresh the app to include it in the rating summary.")

current_ratings = ratings[ratings["rest_stop_id"] == selected_id].copy()
if not current_ratings.empty:
    st.write(f"Average traveler rating: **{current_ratings['rating'].mean():.1f} / 5.0**")
    rating_show = current_ratings.rename(
        columns={
            "created_at": "Submitted At",
            "rating": "Rating",
            "comment": "Comment",
        }
    )
    st.dataframe(rating_show[["Submitted At", "Rating", "Comment"]], use_container_width=True, hide_index=True)
else:
    st.info("No saved ratings yet for this rest stop.")

st.divider()
st.subheader("National Menu Dataset")
st.write(
    "Use this table as the raw dashboard database. Column names are written for presentation, not for code."
)

merged = (
    menus.merge(rest_stops, on="rest_stop_id", how="left")
    .sort_values(["highway_route", "rest_stop_name", "menu_item"])
)
merged["Price"] = merged["price_krw"].apply(format_price)
merged_show = merged.rename(
    columns={
        "rest_stop_name": "Rest Stop",
        "direction": "Direction",
        "highway_route": "Highway Route",
        "region": "Region",
        "food_area": "Food Area",
        "menu_item": "Menu Item",
        "food_category": "Food Category",
        "availability": "Available Time",
        "is_signature": "Signature Food",
        "recommended": "Recommended",
        "sample_rating": "Sample Rating",
        "traffic_group": "Traffic Focus",
    }
)
st.dataframe(
    merged_show[
        [
            "Rest Stop",
            "Direction",
            "Highway Route",
            "Region",
            "Traffic Focus",
            "Food Area",
            "Menu Item",
            "Food Category",
            "Price",
            "Available Time",
            "Signature Food",
            "Recommended",
            "Sample Rating",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Demo note: this project uses seed data for immediate dashboard testing. Replace the CSV files with official open-data exports for production use."
)
