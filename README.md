# Korean Highway Rest Stop Food Dashboard

A Streamlit dashboard for exploring Korean highway rest stop food information.

## Features

- Navigation-style rest stop map
- High-traffic focus mode
- Expanded dataset with 30+ rest stops
- 10+ menu items per rest stop
- Store type and operating-hour tables
- Signature food section
- Menu price and category charts
- User rating form

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data Notes

This version removes phone numbers and uses expanded demo data. The structure is designed so that the CSV files can be replaced later with official public data.

Required files:

```text
data/rest_stops.csv
data/menu_items.csv
data/stores.csv
data/ratings.csv
```

## Suggested Official Data Sources

- Korea Expressway Corporation rest stop status and facility data
- Korea Expressway Corporation rest stop food menu API
- Public Data Portal rest stop traffic and visitor datasets
- Korea Expressway Corporation monthly store sales ranking data
