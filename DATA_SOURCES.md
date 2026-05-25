# Data Source Plan

This project currently uses expanded demonstration data for presentation and prototyping.

## Removed Field

The phone number field has been removed because incomplete or incorrect phone number data can reduce user trust.

## Recommended Official Sources for Future Replacement

1. Korea Expressway Corporation Rest Stop Status
   - Useful for rest stop names, highway routes, direction, facilities, and general information.

2. Korea Expressway Corporation Food Menu API
   - Useful for menu names, prices, store names, representative menu labels, and food information.

3. Public Data Portal Rest Stop Visitor and Traffic Dataset
   - Useful for ranking rest stops by visitor and traffic volume.

4. Korea Expressway Corporation Monthly Store Sales Ranking
   - Useful for popularity charts and top-selling food/store analysis.

## CSV Replacement Strategy

Keep the same column names in the CSV files when replacing demo data with official data:

- rest_stops.csv
- menu_items.csv
- stores.csv
- ratings.csv
