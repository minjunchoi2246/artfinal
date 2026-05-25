# Data Sources and Production Upgrade Guide

This prototype is structured so the CSV files can later be replaced with official public datasets.

Recommended official data sources:

1. Korea Expressway Corporation rest stop facility data
   - Useful for rest stop name, route, direction, operation status, facilities, and location.

2. Korea Expressway Corporation food menu data
   - Useful for menu name, store name, price, representative menu information, and nutrition data.

3. Korea Expressway Corporation sales ranking data
   - Useful for popular menu and store ranking charts.

4. Private expressway operator websites
   - Useful for supplementing rest stops not fully covered by Korea Expressway Corporation datasets.

Recommended merge key:

- Rest stop name
- Highway route
- Direction

Production database fields should preserve these presentation-friendly concepts:

- Rest Stop
- Direction
- Highway Route
- Region
- Food Area
- Menu Item
- Food Category
- Price
- Available Time
- Signature Food
- Recommended
- Rating
