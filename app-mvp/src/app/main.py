"""SEA Retailer Top Selling Intelligence - Streamlit Demo App."""

import streamlit as st

st.set_page_config(
    page_title="SEA Retailer - Top Selling Intelligence",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar: Mode selector and metadata
st.sidebar.title("SEA Retailer Intelligence")
st.sidebar.markdown("---")

data_mode = st.sidebar.radio(
    "Data Mode",
    ["Stub Data", "Live (best-effort)"],
    index=0,
    help="Stub: uses pre-built sample data. Live: attempts real data fetch with stub fallback.",
)

is_stub = data_mode == "Stub Data"

# Mode badge
if is_stub:
    st.sidebar.info("**Mode: STUB** - Using sample data")
else:
    st.sidebar.warning("**Mode: LIVE** - Best-effort with fallback")

st.sidebar.markdown("---")
st.sidebar.markdown("**Configuration**")
st.sidebar.markdown(f"- Schema Version: `1.0.0`")
st.sidebar.markdown(f"- Rule Version: `1.0.0`")
st.sidebar.markdown(f"- Category: `personal_care`")
st.sidebar.markdown(f"- Site: `TH`")
st.sidebar.markdown(f"- Top N: `200`")
st.sidebar.markdown(f"- Window: `14 days`")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built for **SEA Retailer Top Selling Intelligence** FDE Case"
)

# Main page content
st.title("Top Selling Intelligence Dashboard")
st.markdown(
    """
    Welcome to the SEA Retailer Top Selling Intelligence platform.
    Use the sidebar to navigate between pages:

    - **Overview** - Key metrics, overlap analysis, price distribution
    - **Top Items** - Browse and filter top-selling items across platforms
    - **Alerts & Opportunities** - View alerts and actionable opportunities
    - **Review Queue** - Review and decide on matching pairs
    - **Run Pipeline** - Trigger a pipeline + matching run
    """
)

# Quick stats if data available
try:
    from data.loader import load_overview_stats

    stats = load_overview_stats(stub=is_stub)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TikTok Items", stats.get("tiktok_count", "N/A"))
        col2.metric("Shopee Items", stats.get("shopee_count", "N/A"))
        col3.metric("Match Rate", f"{stats.get('match_rate', 0):.1f}%")
        col4.metric("Needs Review", stats.get("needs_review", "N/A"))
except Exception:
    st.info("Run the pipeline first to see overview statistics.")
