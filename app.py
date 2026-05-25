import os
from datetime import datetime

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Korean Highway Rest Stop Food Dashboard",
    page_icon="🍜",
    layout="wide",
)

DATA_DIR = "data"
RATINGS_PATH = os.path.join(DATA_DIR, "ratings.csv")


@st.cache_data
def load_data():
    rest_stops = pd.read_csv(os.path.join(DATA_DIR, "rest_stops.csv"))
    menu_items = pd.read_csv(os.path.join(DATA_DIR, "menu_items.csv"))
    stores = pd.read_csv(os.path.join(DATA_DIR, "stores.csv"))

    if os.path.exists(RATINGS_PATH):
        ratings = pd.read_csv(RATINGS_PATH)
    else:
        ratings = pd.DataFrame(
            columns=["timestamp", "rest_stop_id", "rest_stop_name", "rating", "comment"]
        )

    return rest_stops, menu_items, stores, ratings


def format_krw(value):
    try:
        return f"₩{int(value):,}"
    except Exception:
        return value


def natural_table(df, column_map):
    view = df.rename(columns=column_map)
    return view[list(column_map.values())]


def render_stars(score):
    if pd.isna(score):
        return "No rating yet"
    full = int(round(score))
    return "★" * full + "☆" * (5 - full)


def make_map(rest_stops, selected_id=None):
    center_lat = rest_stops["latitude"].mean()
    center_lon = rest_stops["longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="CartoDB positron",
        control_scale=True,
    )

    for _, row in rest_stops.iterrows():
        is_focus = row["traffic_group"] == "High"
        is_selected = selected_id == row["rest_stop_id"]

        color = "red" if is_focus else "blue"
        if is_selected:
            color = "green"

        popup_html = f"""
        <div style="font-family: Arial; width: 260px;">
            <h4 style="margin-bottom: 4px;">{row['rest_stop_name']}</h4>
            <b>Direction:</b> {row['direction']}<br>
            <b>Route:</b> {row['highway_route']}<br>
            <b>Area:</b> {row['region']}<br>
            <b>Operating Hours:</b> {row['general_hours']}<br>
            <b>Traffic Priority:</b> {row['traffic_group']}<br>
            <b>Dashboard Rating:</b> {row['avg_rating']} / 5<br>
            <p style="margin-top: 8px;">{row['summary']}</p>
        </div>
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            tooltip=f"{row['rest_stop_name']} | {row['direction']}",
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(m)

    return m


def save_rating(rest_stop_id, rest_stop_name, rating, comment):
    new_row = pd.DataFrame(
        [
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "rest_stop_id": rest_stop_id,
                "rest_stop_name": rest_stop_name,
                "rating": rating,
                "comment": comment,
            }
        ]
    )

    if os.path.exists(RATINGS_PATH):
        old = pd.read_csv(RATINGS_PATH)
        updated = pd.concat([old, new_row], ignore_index=True)
    else:
        updated = new_row

    updated.to_csv(RATINGS_PATH, index=False)


rest_stops, menu_items, stores, ratings = load_data()

st.title("Korean Highway Rest Stop Food Dashboard")
st.caption(
    "Explore rest stop food options, store types, operating hours, menu prices, and user ratings. "
    "This version uses expanded demo data and is designed to be replaced with official public data later."
)

with st.sidebar:
    st.header("Dashboard Controls")

    view_mode = st.radio(
        "Rest stop coverage",
        ["High-traffic focus", "All rest stops"],
        help="High-traffic focus shows representative major rest stops first. All rest stops shows the expanded dataset.",
    )

    route_options = ["All routes"] + sorted(rest_stops["highway_route"].unique().tolist())
    selected_route = st.selectbox("Highway route", route_options)

    category_options = ["All food categories"] + sorted(menu_items["category"].unique().tolist())
    selected_category = st.selectbox("Food category", category_options)

    search_text = st.text_input("Search by rest stop or menu", placeholder="e.g. Deokpyeong, Udon, Pork Cutlet")

    st.divider()
    st.caption("Map legend")
    st.markdown("🔴 High-traffic focus stop  \n🔵 Additional stop  \n🟢 Selected stop")


filtered_stops = rest_stops.copy()

if view_mode == "High-traffic focus":
    filtered_stops = filtered_stops[filtered_stops["traffic_group"] == "High"]

if selected_route != "All routes":
    filtered_stops = filtered_stops[filtered_stops["highway_route"] == selected_route]

if search_text:
    matching_menu_ids = menu_items[
        menu_items["menu_name"].str.contains(search_text, case=False, na=False)
        | menu_items["category"].str.contains(search_text, case=False, na=False)
    ]["rest_stop_id"].unique()

    filtered_stops = filtered_stops[
        filtered_stops["rest_stop_name"].str.contains(search_text, case=False, na=False)
        | filtered_stops["region"].str.contains(search_text, case=False, na=False)
        | filtered_stops["rest_stop_id"].isin(matching_menu_ids)
    ]

if filtered_stops.empty:
    st.warning("No rest stops match the current filters. Try changing the route or search keyword.")
    st.stop()

top_metric_1, top_metric_2, top_metric_3, top_metric_4 = st.columns(4)
top_metric_1.metric("Rest Stops Shown", f"{len(filtered_stops):,}")
top_metric_2.metric("Menu Items Available", f"{len(menu_items[menu_items['rest_stop_id'].isin(filtered_stops['rest_stop_id'])]):,}")
top_metric_3.metric("Average Menu Price", format_krw(menu_items[menu_items["rest_stop_id"].isin(filtered_stops["rest_stop_id"])]["price_krw"].mean()))
top_metric_4.metric("Average Dashboard Rating", f"{filtered_stops['avg_rating'].mean():.1f} / 5")

st.divider()

map_col, detail_col = st.columns([1.25, 1])

with map_col:
    st.subheader("Navigation-Style Rest Stop Map")
    st.caption("Click a marker to see a quick pop-up. Use the selector on the right for full menu details.")
    map_obj = make_map(filtered_stops)
    st_folium(map_obj, height=620, use_container_width=True)

with detail_col:
    st.subheader("Selected Rest Stop")

    selected_label = st.selectbox(
        "Choose a rest stop for detailed food information",
        filtered_stops.apply(lambda x: f"{x['rest_stop_name']} — {x['direction']}", axis=1),
    )
    selected_row = filtered_stops[
        filtered_stops.apply(lambda x: f"{x['rest_stop_name']} — {x['direction']}", axis=1) == selected_label
    ].iloc[0]
    selected_id = selected_row["rest_stop_id"]

    selected_menu = menu_items[menu_items["rest_stop_id"] == selected_id].copy()
    selected_stores = stores[stores["rest_stop_id"] == selected_id].copy()

    if selected_category != "All food categories":
        selected_menu = selected_menu[selected_menu["category"] == selected_category]

    st.markdown(f"### {selected_row['rest_stop_name']}")
    st.write(f"**Direction:** {selected_row['direction']}")
    st.write(f"**Highway Route:** {selected_row['highway_route']}")
    st.write(f"**Area:** {selected_row['region']}")
    st.write(f"**General Operating Hours:** {selected_row['general_hours']}")
    st.write(f"**Dashboard Rating:** {render_stars(selected_row['avg_rating'])}  {selected_row['avg_rating']} / 5")
    st.info(selected_row["summary"])

    signature = menu_items[(menu_items["rest_stop_id"] == selected_id) & (menu_items["is_signature"] == True)]
    if not signature.empty:
        sig = signature.iloc[0]
        st.success(
            f"Signature Food: {sig['menu_name']} — {format_krw(sig['price_krw'])}\n\n{sig['description']}"
        )

    st.markdown("#### Rate This Rest Stop")
    with st.form("rating_form", clear_on_submit=True):
        user_rating = st.slider("Your rating", min_value=1, max_value=5, value=4)
        user_comment = st.text_area("Short comment", placeholder="e.g. Good late-night food options.")
        submitted = st.form_submit_button("Submit Rating")

    if submitted:
        save_rating(selected_id, selected_row["rest_stop_name"], user_rating, user_comment)
        st.cache_data.clear()
        st.success("Your rating has been saved. Refresh the app to update the rating table.")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Menu Overview", "Store Types & Hours", "Charts", "User Ratings"]
)

visible_menu = menu_items[menu_items["rest_stop_id"].isin(filtered_stops["rest_stop_id"])].copy()

if selected_category != "All food categories":
    visible_menu = visible_menu[visible_menu["category"] == selected_category]

if search_text:
    visible_menu = visible_menu[
        visible_menu["menu_name"].str.contains(search_text, case=False, na=False)
        | visible_menu["category"].str.contains(search_text, case=False, na=False)
        | visible_menu["store_name"].str.contains(search_text, case=False, na=False)
    ]

visible_menu = visible_menu.merge(
    rest_stops[["rest_stop_id", "rest_stop_name", "direction", "highway_route"]],
    on="rest_stop_id",
    how="left",
)

visible_stores = stores[stores["rest_stop_id"].isin(filtered_stops["rest_stop_id"])].copy()
visible_stores = visible_stores.merge(
    rest_stops[["rest_stop_id", "rest_stop_name", "direction", "highway_route"]],
    on="rest_stop_id",
    how="left",
)

with tab1:
    st.subheader("Food Menu Database")
    st.caption("The table uses presentation-friendly column names instead of raw code-style field names.")

    display_menu = visible_menu.copy()
    display_menu["Price"] = display_menu["price_krw"].apply(format_krw)
    display_menu["Signature Food"] = display_menu["is_signature"].map({True: "Yes", False: "No"})
    display_menu["Recommended"] = display_menu["is_recommended"].map({True: "Yes", False: "No"})
    display_menu["Sample Rating"] = display_menu["sample_rating"].apply(lambda x: f"{x:.1f} / 5")

    menu_columns = {
        "rest_stop_name": "Rest Stop",
        "direction": "Direction",
        "highway_route": "Highway Route",
        "store_name": "Food Area / Store",
        "menu_name": "Menu Item",
        "category": "Food Category",
        "Price": "Price",
        "operating_hours": "Menu Availability",
        "Signature Food": "Signature Food",
        "Recommended": "Recommended",
        "Sample Rating": "Sample Rating",
    }

    st.dataframe(
        natural_table(display_menu, menu_columns),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

with tab2:
    st.subheader("Restaurant Types and Operating Hours")

    store_columns = {
        "rest_stop_name": "Rest Stop",
        "direction": "Direction",
        "highway_route": "Highway Route",
        "store_name": "Restaurant / Store Area",
        "store_type": "Type of Food Service",
        "opening_time": "Opening Time",
        "closing_time": "Closing Time",
        "description": "What You Can Find There",
    }

    st.dataframe(
        natural_table(visible_stores, store_columns),
        use_container_width=True,
        hide_index=True,
        height=430,
    )

with tab3:
    st.subheader("Visual Food Analysis")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        price_by_category = (
            visible_menu.groupby("category", as_index=False)["price_krw"]
            .mean()
            .sort_values("price_krw", ascending=False)
        )
        fig_price = px.bar(
            price_by_category,
            x="category",
            y="price_krw",
            labels={"category": "Food Category", "price_krw": "Average Price (KRW)"},
            title="Average Menu Price by Food Category",
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with chart_col2:
        category_count = visible_menu["category"].value_counts().reset_index()
        category_count.columns = ["Food Category", "Number of Menu Items"]
        fig_category = px.pie(
            category_count,
            names="Food Category",
            values="Number of Menu Items",
            title="Menu Category Distribution",
        )
        st.plotly_chart(fig_category, use_container_width=True)

    traffic_chart_data = filtered_stops.sort_values("traffic_index", ascending=False)
    fig_traffic = px.bar(
        traffic_chart_data,
        x="rest_stop_name",
        y="traffic_index",
        color="traffic_group",
        labels={
            "rest_stop_name": "Rest Stop",
            "traffic_index": "Traffic Priority Index",
            "traffic_group": "Dashboard Group",
        },
        title="Traffic Priority Index by Rest Stop",
    )
    fig_traffic.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_traffic, use_container_width=True)

with tab4:
    st.subheader("User Ratings")
    st.caption("Ratings are saved locally in data/ratings.csv. For a public app, connect this to Google Sheets, Supabase, or Firebase.")

    if ratings.empty:
        st.info("No user ratings yet.")
    else:
        display_ratings = ratings.copy()
        rating_columns = {
            "timestamp": "Submitted At",
            "rest_stop_name": "Rest Stop",
            "rating": "User Rating",
            "comment": "Comment",
        }
        st.dataframe(
            natural_table(display_ratings, rating_columns),
            use_container_width=True,
            hide_index=True,
        )

st.divider()
st.caption(
    "Data note: This prototype removes phone numbers and uses expanded demonstration data. "
    "For production use, replace the CSV files with official public data from Korea Expressway Corporation or the Public Data Portal."
)
