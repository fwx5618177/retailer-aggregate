"""Run Pipeline Page - Trigger data pipeline and matching."""

import subprocess
import tempfile
from pathlib import Path

import yaml
import streamlit as st

from data.loader import DATA_PIPELINE_DIR, MATCHING_ENGINE_DIR

st.set_page_config(page_title="Run Pipeline", page_icon="\u25b6\ufe0f", layout="wide")
st.title("Run Pipeline")

st.markdown("""
This page allows you to trigger a full pipeline run:
1. **Ingest** data from platforms (or use stub data)
2. **Standardize** brand, spec, and price fields
3. **Run DQ checks** to validate data quality
4. **Export** serving data to DuckDB/Parquet
5. **Run matching** engine to produce cross-platform matches
6. **Generate alerts** based on ranking changes and price anomalies
""")

# Resolve venv python executables for each sub-project
_pipeline_python = str(Path(DATA_PIPELINE_DIR) / ".venv" / "bin" / "python")
_matching_python = str(Path(MATCHING_ENGINE_DIR) / ".venv" / "bin" / "python")

mode = st.radio(
    "Run Mode",
    ["Stub (no network required)", "Live (best-effort with fallback)"],
    index=0,
)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pipeline Configuration")
    category = st.text_input("Category", value="personal_care")
    site = st.text_input("Site", value="th")
    top_n = st.number_input("Top N", value=200, min_value=10, max_value=1000)
    window_days = st.selectbox("Window (days)", [7, 14, 30], index=1)

with col2:
    st.subheader("Matching Configuration")
    auto_threshold = st.slider("Auto-accept threshold", 0.5, 1.0, 0.85, 0.05)
    review_threshold = st.slider("Needs-review threshold", 0.3, 0.9, 0.65, 0.05)
    st.markdown(f"- Auto accept: >= {auto_threshold}")
    st.markdown(f"- Needs review: {review_threshold} - {auto_threshold}")
    st.markdown(f"- No match: < {review_threshold}")

st.markdown("---")

if st.button("Run Full Pipeline", type="primary"):
    is_stub = mode.startswith("Stub")

    # Build runtime config override from UI parameters
    pipeline_override = {
        "scope": {
            "categories": [category],
            "sites": [site],
            "top_n": int(top_n),
            "window_days": int(window_days),
        },
        "ingestion": {
            "use_stub": is_stub,
        },
    }

    matching_override = {
        "matching": {
            "auto_accept_threshold": float(auto_threshold),
            "review_threshold": float(review_threshold),
        },
    }

    # Step 1: Data Pipeline
    st.subheader("Step 1: Data Pipeline")
    with st.spinner("Running data pipeline..."):
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", prefix="pipeline_override_", delete=False,
            ) as f:
                yaml.dump(pipeline_override, f, default_flow_style=False)
                override_path = f.name

            cmd = [
                _pipeline_python, "-m", "sea_pipeline", "run",
                "--config", "config/default.yaml",
                "--config-override", override_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=300,
                cwd=DATA_PIPELINE_DIR,
            )
            Path(override_path).unlink(missing_ok=True)

            if result.returncode == 0:
                st.success("Data pipeline completed successfully!")
                if result.stdout:
                    with st.expander("Pipeline Output"):
                        st.code(result.stdout)
            else:
                st.error(f"Pipeline failed: {result.stderr}")
        except FileNotFoundError:
            st.warning("Data pipeline not found. Make sure sea-pipeline is installed.")
        except subprocess.TimeoutExpired:
            st.error("Pipeline timed out after 5 minutes.")
        except Exception as e:
            st.error(f"Error: {e}")

    # Step 2: Matching Engine
    st.subheader("Step 2: Matching Engine")
    with st.spinner("Running matching engine..."):
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", prefix="matching_override_", delete=False,
            ) as f:
                yaml.dump(matching_override, f, default_flow_style=False)
                match_override_path = f.name

            cmd = [
                _matching_python, "-m", "sea_matching",
                "--config", "config/default.yaml",
                "--config-override", match_override_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=300,
                cwd=MATCHING_ENGINE_DIR,
            )
            Path(match_override_path).unlink(missing_ok=True)

            if result.returncode == 0:
                st.success("Matching engine completed successfully!")
                if result.stdout:
                    with st.expander("Matching Output"):
                        st.code(result.stdout)
            else:
                st.error(f"Matching failed: {result.stderr}")
        except FileNotFoundError:
            st.warning("Matching engine not found. Make sure sea-matching is installed.")
        except subprocess.TimeoutExpired:
            st.error("Matching timed out after 5 minutes.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.balloons()
    st.success("Pipeline run complete! Navigate to other pages to view results.")
