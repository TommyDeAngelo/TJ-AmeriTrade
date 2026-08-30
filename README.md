# TJ AmeriTrade

Stock-market analysis software built with Streamlit, yfinance, pandas, NumPy, and Plotly.

## Deploy on Streamlit Community Cloud

Use these settings when creating the app:

- Repository: `TommyDeAngelo/TJ-AmeriTrade`
- Branch: `main`
- Main file path: `streamlit_app.py`

The application entrypoint launches the preserved `TJ_AmeriTrade_V6.zip` build through the root `app.py` wrapper.

## Current structure

- `TJ_AmeriTrade_V6.zip` — preserved V6 application
- `app.py` — deployment launcher that extracts and runs V6
- `streamlit_app.py` — conventional Streamlit Community Cloud entrypoint
- `requirements.txt` — Python dependencies

## Commercial roadmap

For a paid version, keep market-data/API secrets server-side and add:

1. User authentication
2. Stripe Checkout for subscriptions
3. Stripe webhook handling to synchronize subscription status
4. Entitlement checks before premium tools are rendered
5. Account/billing portal
6. Usage limits and server-side protection for premium data/API calls

For an early YouTube-driven MVP, the Streamlit app can remain the analysis interface while authentication, subscription state, and payment handling are added around it. A later migration to a dedicated frontend/backend can be considered if traffic or product complexity outgrows Streamlit.
