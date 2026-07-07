import streamlit as st
import pandas as pd
import numpy as np
import math
import io

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="A Comprehensive Measure of Well-Being",
    page_icon="🌍",
    layout="wide"
)

# -----------------------------
# Core HDI calculation logic
# -----------------------------
# Standard UNDP-style Human Development Index bounds
LIFE_EXP_MIN, LIFE_EXP_MAX = 20, 85
SCHOOLING_MIN, SCHOOLING_MAX = 0, 18
GNI_MIN, GNI_MAX = 100, 75000


def health_index(life_expectancy):
    val = (life_expectancy - LIFE_EXP_MIN) / (LIFE_EXP_MAX - LIFE_EXP_MIN)
    return min(max(val, 0), 1)


def education_index(mean_years_schooling, expected_years_schooling):
    mys_index = mean_years_schooling / 15
    eys_index = expected_years_schooling / 18
    idx = (mys_index + eys_index) / 2
    return min(max(idx, 0), 1)


def income_index(gni_per_capita):
    gni = max(gni_per_capita, GNI_MIN)
    val = (math.log(gni) - math.log(GNI_MIN)) / (math.log(GNI_MAX) - math.log(GNI_MIN))
    return min(max(val, 0), 1)


def compute_hdi_score(life_expectancy, mean_years_schooling, expected_years_schooling, gni_per_capita):
    h = health_index(life_expectancy)
    e = education_index(mean_years_schooling, expected_years_schooling)
    i = income_index(gni_per_capita)
    hdi = (h * e * i) ** (1 / 3)
    return round(hdi, 4), round(h, 4), round(e, 4), round(i, 4)


def classify_tier(hdi_score):
    if hdi_score >= 0.80:
        return "Very High"
    elif hdi_score >= 0.70:
        return "High"
    elif hdi_score >= 0.55:
        return "Medium"
    else:
        return "Low"


# -----------------------------
# Sidebar navigation
# -----------------------------
st.sidebar.title("🌍 Well-Being Index")
page = st.sidebar.radio(
    "Navigate",
    ["Single Country Prediction", "Batch Upload & Comparison", "About This Project"]
)

st.sidebar.markdown("---")
st.sidebar.caption("A Comprehensive Measure of Well-Being")
st.sidebar.caption("HDI Score • Tier Classification • Sub-Index Breakdown")

# -----------------------------
# Page 1: Single Country Prediction
# -----------------------------
if page == "Single Country Prediction":
    st.title("🌍 A Comprehensive Measure of Well-Being")
    st.subheader("HDI Score Prediction & Tier Classification")

    col1, col2 = st.columns(2)

    with col1:
        country_name = st.text_input("Country / Region Name", value="Sample Country")
        life_expectancy = st.slider("Life Expectancy at Birth (years)", 20.0, 90.0, 70.0, 0.1)
        mean_years_schooling = st.slider("Mean Years of Schooling", 0.0, 18.0, 8.0, 0.1)

    with col2:
        expected_years_schooling = st.slider("Expected Years of Schooling", 0.0, 20.0, 12.0, 0.1)
        gni_per_capita = st.number_input(
            "GNI per Capita (PPP $)", min_value=100, max_value=150000, value=15000, step=100
        )

    if st.button("Predict HDI Score", type="primary"):
        hdi, h, e, i = compute_hdi_score(
            life_expectancy, mean_years_schooling, expected_years_schooling, gni_per_capita
        )
        tier = classify_tier(hdi)

        st.markdown("### Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("HDI Score", f"{hdi:.3f}")
        m2.metric("Development Tier", tier)
        m3.metric("Country", country_name)

        st.markdown("### Sub-Index Breakdown")
        breakdown_df = pd.DataFrame({
            "Sub-Index": ["Health Index", "Education Index", "Income Index"],
            "Score": [h, e, i]
        })
        st.bar_chart(breakdown_df.set_index("Sub-Index"))
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        # Downloadable single-row report
        report_df = pd.DataFrame([{
            "Country": country_name,
            "Life Expectancy": life_expectancy,
            "Mean Years Schooling": mean_years_schooling,
            "Expected Years Schooling": expected_years_schooling,
            "GNI per Capita": gni_per_capita,
            "Health Index": h,
            "Education Index": e,
            "Income Index": i,
            "HDI Score": hdi,
            "Tier": tier
        }])
        csv_buffer = io.StringIO()
        report_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "📥 Download Report (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"{country_name}_hdi_report.csv",
            mime="text/csv"
        )

# -----------------------------
# Page 2: Batch Upload & Comparison
# -----------------------------
elif page == "Batch Upload & Comparison":
    st.title("📊 Batch Upload & Multi-Country Comparison")
    st.write(
        "Upload a CSV with columns: **country, life_expectancy, mean_years_schooling, "
        "expected_years_schooling, gni_per_capita**"
    )

    sample = pd.DataFrame({
        "country": ["CountryA", "CountryB", "CountryC"],
        "life_expectancy": [75.2, 68.4, 82.1],
        "mean_years_schooling": [9.5, 6.2, 12.8],
        "expected_years_schooling": [13.0, 10.5, 16.2],
        "gni_per_capita": [18000, 6500, 42000]
    })

    with st.expander("📄 See sample CSV format"):
        st.dataframe(sample, use_container_width=True, hide_index=True)
        sample_buffer = io.StringIO()
        sample.to_csv(sample_buffer, index=False)
        st.download_button(
            "Download Sample CSV",
            data=sample_buffer.getvalue(),
            file_name="sample_countries.csv",
            mime="text/csv"
        )

    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {
                "country", "life_expectancy", "mean_years_schooling",
                "expected_years_schooling", "gni_per_capita"
            }
            if not required_cols.issubset(set(df.columns)):
                st.error(f"CSV must contain columns: {', '.join(required_cols)}")
            else:
                results = []
                for _, row in df.iterrows():
                    hdi, h, e, i = compute_hdi_score(
                        row["life_expectancy"],
                        row["mean_years_schooling"],
                        row["expected_years_schooling"],
                        row["gni_per_capita"]
                    )
                    tier = classify_tier(hdi)
                    results.append({
                        "Country": row["country"],
                        "Health Index": h,
                        "Education Index": e,
                        "Income Index": i,
                        "HDI Score": hdi,
                        "Tier": tier
                    })

                results_df = pd.DataFrame(results)
                st.markdown("### Results Table")
                st.dataframe(results_df, use_container_width=True, hide_index=True)

                st.markdown("### HDI Score Comparison")
                st.bar_chart(results_df.set_index("Country")["HDI Score"])

                st.markdown("### Sub-Index Comparison")
                st.line_chart(results_df.set_index("Country")[["Health Index", "Education Index", "Income Index"]])

                st.markdown("### Tier Distribution")
                tier_counts = results_df["Tier"].value_counts()
                st.bar_chart(tier_counts)

                out_buffer = io.StringIO()
                results_df.to_csv(out_buffer, index=False)
                st.download_button(
                    "📥 Download Full Results (CSV)",
                    data=out_buffer.getvalue(),
                    file_name="hdi_comparison_results.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Could not process file: {e}")

# -----------------------------
# Page 3: About
# -----------------------------
else:
    st.title("ℹ️ About This Project")
    st.markdown("""
**Project Name:** A Comprehensive Measure of Well-Being

**Purpose:** Predicts a Human Development Index (HDI)-style well-being score for a
country or region based on life expectancy, schooling, and income indicators, then
classifies it into a development tier.

**Core Features:**
- HDI Score Prediction from life expectancy, schooling, and GNI indicators
- Tier Classification: Very High / High / Medium / Low
- Sub-Index Breakdown (Health, Education, Income) with charts
- CSV Batch Upload for multi-country comparison
- Downloadable CSV reports

**How the score is calculated:**
1. **Health Index** — derived from life expectancy at birth
2. **Education Index** — average of mean years of schooling and expected years of schooling
3. **Income Index** — derived from GNI per capita (log-scaled)
4. **HDI Score** — geometric mean of the three sub-indices

**Tier Thresholds:**
| HDI Score | Tier |
|---|---|
| ≥ 0.80 | Very High |
| 0.70 – 0.799 | High |
| 0.55 – 0.699 | Medium |
| < 0.55 | Low |
    """)
