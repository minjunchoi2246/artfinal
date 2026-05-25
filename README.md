# Korean Highway Rest Stop Food Dashboard

This is a Streamlit dashboard for exploring Korean highway rest stop food information.

## Main Features

- National map-based dashboard
- High-traffic rest stop focus
- Reinforced Seoul–Chungcheong–Jeolla corridor data
- Clickable map markers with food area, menu, price, and opening-hour preview
- Detailed rest stop panel
- Menu price charts and food-category charts
- Simple traveler rating feature

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data Structure

The project uses CSV files in the `data/` folder.

- `rest_stops.csv`: rest stop location, route, direction, region, and traffic focus
- `menu_items.csv`: menu item, food area, food category, price, availability, signature/recommended labels
- `stores.csv`: food area/store type and opening hours
- `ratings.csv`: locally saved user ratings

## Important Note

This version uses demo seed data so the dashboard can run immediately.
For a final public release, replace the CSV files with official open-data exports from Korea Expressway Corporation or the Public Data Portal.
