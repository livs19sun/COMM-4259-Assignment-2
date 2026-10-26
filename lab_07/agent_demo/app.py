from pathlib import Path

import pandas as pd
import streamlit as st

# Locate the data file relative to this script, so the app runs from any folder
DATA_PATH = Path(__file__).parent / "data" / "Customer.csv"


# Load the raw data; ZipCode is read as text so leading zeros (e.g. 02134) are kept
@st.cache_data
def load_raw():
    return pd.read_csv(DATA_PATH, dtype={"ZipCode": str})


# Apply the data-preparation decisions and return the cleaned table
def prepare(raw):
    df = raw.copy()

    # Reviews / Feedback_Call: add HasReview first, then drop both columns
    df["HasReview"] = df["Reviews"].notna().astype(int)
    df = df.drop(columns=["Reviews", "Feedback_Call"])

    # ZipCode: keep only the first five digits
    df["ZipCode"] = df["ZipCode"].str[:5]

    # BirthYear: leave missing values as missing (no rows dropped, nothing filled in)
    # so AgeAtJoin is only averaged over customers whose birth year is known

    # New feature: AgeAtJoin = year of JoinDate minus BirthYear
    join_year = pd.to_datetime(df["JoinDate"]).dt.year
    df["AgeAtJoin"] = join_year - df["BirthYear"]

    return df


# Build one table comparing missing values per column before and after preparation
def missing_table(before, after):
    table = pd.DataFrame({
        "Missing before": before.isna().sum(),
        "Missing after": after.isna().sum(),
    }).astype("Int64")
    table["% before"] = (table["Missing before"] / len(before) * 100).round(1)
    table["% after"] = (table["Missing after"] / len(after) * 100).round(1)

    # Label columns that were dropped or newly created
    table["Status"] = ""
    table.loc[~table.index.isin(after.columns), "Status"] = "dropped"
    table.loc[~table.index.isin(before.columns), "Status"] = "new"

    # Keep the original column order, with new columns at the end
    order = list(before.columns) + [c for c in after.columns if c not in before.columns]
    return table.loc[order, ["Missing before", "% before", "Missing after", "% after", "Status"]]


# Page setup and data
st.set_page_config(page_title="Customer Dashboard", layout="wide")
st.title("Customer Dashboard")

raw = load_raw()
clean = prepare(raw)

(prep_tab,) = st.tabs(["Data Preparation"])

with prep_tab:
    # List the decisions that were applied
    st.header("Data preparation")
    st.markdown(
        """
- **Reviews** and **Feedback_Call** (over 80% missing): added **HasReview**
  (1 if the customer left a review, else 0), then dropped both columns.
- **ZipCode**: kept the first five digits.
- **BirthYear**: missing values left as missing; no rows dropped and no values filled in.
- **New feature**: **AgeAtJoin** = year of JoinDate minus BirthYear.
"""
    )

    # Rows and columns before and after
    st.subheader("Rows and columns")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows before", raw.shape[0])
    c2.metric("Rows after", clean.shape[0], delta=clean.shape[0] - raw.shape[0])
    c3.metric("Columns before", raw.shape[1])
    c4.metric("Columns after", clean.shape[1], delta=clean.shape[1] - raw.shape[1])

    # Missing values per column before and after
    st.subheader("Missing values per column")
    st.dataframe(missing_table(raw, clean))

    # Average AgeAtJoin for churned vs. returning customers (Churn = 1 means churned)
    st.subheader("Average age at join: churned vs. returning")
    groups = clean["Churn"].map({1: "Churned", 0: "Returning"})
    age_by_group = clean.groupby(groups)["AgeAtJoin"].agg(["mean", "count"])
    age_by_group.index.name = "Customer group"
    st.bar_chart(age_by_group["mean"].rename("Average AgeAtJoin"))
    st.caption(
        "Averages use only customers with a known BirthYear: "
        + ", ".join(f"{g}: {n} customers" for g, n in age_by_group["count"].items())
        + "."
    )
