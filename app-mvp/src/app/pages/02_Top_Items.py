"""Top Items Browser Page."""

import streamlit as st

st.set_page_config(page_title="Top Items", page_icon="\U0001f4cb", layout="wide")
st.title("Top Selling Items")

try:
    import pandas as pd

    from data.loader import load_top_items

    @st.cache_data(ttl=60)
    def load_items():
        return load_top_items(limit=500)

    df = load_items()

    if df.empty:
        st.warning("No items available. Please run the pipeline first.")
        st.stop()

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    platforms = ["All"] + sorted(df["platform"].unique().tolist())
    selected_platform = col1.selectbox("Platform", platforms)

    brands = ["All"]
    if "brand_std" in df.columns:
        brands += sorted(df["brand_std"].dropna().unique().tolist())
    selected_brand = col2.selectbox("Brand", brands)

    price_min = col3.number_input("Min Price (THB)", value=0, min_value=0)
    price_max = col4.number_input("Max Price (THB)", value=10000, min_value=0)

    # Apply filters
    filtered = df.copy()
    if selected_platform != "All":
        filtered = filtered[filtered["platform"] == selected_platform]
    if selected_brand != "All":
        filtered = filtered[filtered["brand_std"] == selected_brand]
    if "list_price" in filtered.columns:
        filtered = filtered[
            (filtered["list_price"].fillna(0) / 100 >= price_min)
            & (filtered["list_price"].fillna(999999) / 100 <= price_max)
        ]

    st.markdown(f"**Showing {len(filtered)} items**")

    # Display table
    display_cols = ["platform", "rank", "title", "brand_std", "size_value", "size_unit"]
    if "list_price" in filtered.columns:
        filtered["price_thb"] = (filtered["list_price"].fillna(0) / 100).round(2)
        display_cols.append("price_thb")
    if "currency" in filtered.columns:
        display_cols.append("currency")

    available_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[available_cols].reset_index(drop=True),
        use_container_width=True,
        height=600,
    )

    # Item detail expander
    st.markdown("---")
    st.subheader("Item Detail")
    if not filtered.empty:
        selected_idx = st.number_input(
            "Enter row number to view details", min_value=0,
            max_value=len(filtered) - 1, value=0,
        )
        item = filtered.iloc[selected_idx]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Title:** {item.get('title', 'N/A')}")
            st.markdown(f"**Platform:** {item.get('platform', 'N/A')}")
            st.markdown(f"**Rank:** {item.get('rank', 'N/A')}")
            st.markdown(f"**Brand:** {item.get('brand_std', item.get('brand_raw', 'N/A'))}")
        with col2:
            st.markdown(f"**Spec:** {item.get('size_value', 'N/A')} {item.get('size_unit', '')}")
            price = item.get("list_price", 0)
            st.markdown(f"**Price:** {price / 100:.2f} THB" if price else "**Price:** N/A")
            st.markdown(f"**URL:** {item.get('url', 'N/A')}")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the data pipeline has been run.")
