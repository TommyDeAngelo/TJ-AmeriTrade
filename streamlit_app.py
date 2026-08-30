"""Streamlit Community Cloud entrypoint for TJ AmeriTrade.

The actual V6 application is preserved in TJ_AmeriTrade_V6.zip.
The root app.py handles extraction and execution so the packaged build
remains unchanged.
"""

import runpy

runpy.run_path("app.py", run_name="__main__")
