from pathlib import Path

import pandas as pd
import streamlit as st

# The default data file, in the data/ folder next to this app
DATA_FILE = Path(__file__).parent / "data" / "titanic_features.csv"

# The fixed menu of steps a user can choose from
ACTIONS = [
    "Drop a column",
    "Fill missing values",
    "Fill missing values with the median of each group",
    "Add a 0/1 missing-value flag",
    "Extract the title from a name column",
    "Dummy-code a column",
    "Drop rows that are missing a value",
]

# The ways to fill missing values
FILL_METHODS = ["mean", "median", "most frequent", "a value I type"]


# Profile table: the type, missing count and missing share of each column
def profile(df):
    return pd.DataFrame({
        "type": df.dtypes.astype(str),
        "missing": df.isnull().sum(),
        "missing share": df.isnull().mean().round(3),
    })


# Rows, columns and total missing values (used in the before/after tables)
def summary(df):
    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "missing values": int(df.isnull().sum().sum()),
    }


# Carry out one step on a copy of df.
# Returns the new df and the pandas line that the step equals.
def apply_step(df, step):
    df = df.copy()
    action = step["action"]
    col = step["column"]

    # Drop a column
    if action == "Drop a column":
        df = df.drop(columns=[col])
        code = f'df = df.drop(columns=["{col}"])'

    # Fill missing values with the mean, median, most frequent value, or a typed value
    elif action == "Fill missing values":
        method = step["method"]
        if method == "mean":
            df[col] = df[col].fillna(df[col].mean())
            code = f'df["{col}"] = df["{col}"].fillna(df["{col}"].mean())'
        elif method == "median":
            df[col] = df[col].fillna(df[col].median())
            code = f'df["{col}"] = df["{col}"].fillna(df["{col}"].median())'
        elif method == "most frequent":
            df[col] = df[col].fillna(df[col].mode()[0])
            code = f'df["{col}"] = df["{col}"].fillna(df["{col}"].mode()[0])'
        else:
            value = step["value"]
            # If the column holds numbers, turn the typed text into a number
            if pd.api.types.is_numeric_dtype(df[col]):
                value = float(value)
            df[col] = df[col].fillna(value)
            code = f'df["{col}"] = df["{col}"].fillna({value!r})'

    # Fill missing values with the median of each group (for example Age by Pclass)
    elif action == "Fill missing values with the median of each group":
        group = step["group"]
        df[col] = df[col].fillna(df.groupby(group)[col].transform("median"))
        code = f'df["{col}"] = df["{col}"].fillna(df.groupby("{group}")["{col}"].transform("median"))'

    # Add a 0/1 flag column: 1 if the value is missing, or 1 if it is present
    elif action == "Add a 0/1 missing-value flag":
        new = step["new_name"]
        if step["flag_type"] == "1 if missing":
            df[new] = df[col].isnull().astype(int)
            code = f'df["{new}"] = df["{col}"].isnull().astype(int)'
        else:
            df[new] = df[col].notnull().astype(int)
            code = f'df["{new}"] = df["{col}"].notnull().astype(int)'

    # Take the title out of a name like "Braund, Mr. Owen Harris":
    # split at ", " and keep the part after it, then split at "." and keep the part before it
    elif action == "Extract the title from a name column":
        new = step["new_name"]
        df[new] = df[col].str.split(", ").str[1].str.split(".").str[0]
        code = f'df["{new}"] = df["{col}"].str.split(", ").str[1].str.split(".").str[0]'

    # Dummy-code (one-hot encode) a column into 0/1 columns
    elif action == "Dummy-code a column":
        df = pd.get_dummies(df, columns=[col], dtype=int)
        code = f'df = pd.get_dummies(df, columns=["{col}"], dtype=int)'

    # Drop the rows that are missing a value in this column
    else:
        df = df.dropna(subset=[col])
        code = f'df = df.dropna(subset=["{col}"])'

    return df, code


# Page settings and the one tab
st.set_page_config(page_title="Data Preparation Workbench", layout="wide")
(tab,) = st.tabs(["Data Preparation Workbench"])

# The first time the app runs, start with an empty list of steps
if "steps" not in st.session_state:
    st.session_state["steps"] = []
    st.session_state["data_source"] = None

with tab:
    st.title("Data Preparation Workbench")
    st.write("You choose every step. The app makes no decisions on its own and uses no AI model.")

    # Load the data: the uploaded CSV, or the default Titanic file when nothing is uploaded
    uploaded = st.file_uploader("Upload a CSV (optional)", type="csv")
    if uploaded is not None:
        original = pd.read_csv(uploaded)
        source = uploaded.name
    else:
        original = pd.read_csv(DATA_FILE)
        source = DATA_FILE.name

    # When the data file changes, clear the steps (they were made for the old file)
    if st.session_state["data_source"] != source:
        st.session_state["steps"] = []
        st.session_state["data_source"] = source

    # Section 1: profile of the original data
    st.header("1. Profile of the data")
    st.write(f"File: **{source}**")
    c1, c2 = st.columns(2)
    c1.metric("Rows", original.shape[0])
    c2.metric("Columns", original.shape[1])
    st.dataframe(profile(original))

    # Replay every saved step, in order, starting from the original data
    df = original
    results = []
    for i, step in enumerate(st.session_state["steps"]):
        try:
            new_df, code = apply_step(df, step)
        except Exception as error:
            st.error(f"Step {i + 1} could not run: {error}. Use Undo last step to remove it.")
            break
        results.append((code, summary(df), summary(new_df)))
        df = new_df

    # Section 2: choose a new step from the menu
    st.header("2. Add a step")
    action = st.selectbox("Step", ACTIONS, index=None, placeholder="Choose a step...")
    columns = list(df.columns)
    step = None

    if action is not None:
        col = st.selectbox("Column", columns, index=None, placeholder="Choose a column...")
        step = {"action": action, "column": col}

        # Extra options that only some steps need
        if action == "Fill missing values":
            step["method"] = st.selectbox("Fill with", FILL_METHODS, index=None, placeholder="Choose a method...")
            if step["method"] == "a value I type":
                step["value"] = st.text_input("Value to fill in")
        elif action == "Fill missing values with the median of each group":
            step["group"] = st.selectbox("Group by", columns, index=None, placeholder="Choose a group column...")
        elif action == "Add a 0/1 missing-value flag":
            step["flag_type"] = st.radio("Flag", ["1 if missing", "1 if present"], index=None)
            step["new_name"] = st.text_input("Name of the new flag column")
        elif action == "Extract the title from a name column":
            step["new_name"] = st.text_input("Name of the new column")

    # Add the step only when every option has been filled in
    if st.button("Add step"):
        if step is None or any(v in (None, "") for v in step.values()):
            st.warning("Please fill in every option for this step first.")
        else:
            st.session_state["steps"].append(step)
            st.rerun()

    # Section 3: each step's pandas line and its before/after numbers
    st.header("3. Steps so far")
    if not results:
        st.write("No steps yet.")
    for i, (code, before, after) in enumerate(results):
        st.subheader(f"Step {i + 1}")
        st.code(code, language="python")
        st.table(pd.DataFrame([before, after], index=["before", "after"]))

    # Undo the last step, or clear all steps
    b1, b2 = st.columns(2)
    if b1.button("Undo last step", disabled=not st.session_state["steps"]):
        st.session_state["steps"].pop()
        st.rerun()
    if b2.button("Clear all steps", disabled=not st.session_state["steps"]):
        st.session_state["steps"] = []
        st.rerun()

    # Section 4: the prepared data, its profile, and the download button
    st.header("4. Prepared data")
    st.write(f"{df.shape[0]} rows, {df.shape[1]} columns")
    st.dataframe(df.head(20))
    st.dataframe(profile(df))
    st.download_button(
        "Download prepared data (CSV)",
        data=df.to_csv(index=False),
        file_name="prepared_data.csv",
        mime="text/csv",
    )
