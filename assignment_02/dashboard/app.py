from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# scikit-learn is only needed for information gain and chi-squared in the EDA tab.
# If it is not installed yet, the rest of the app still works.
try:
    from sklearn.feature_selection import chi2, mutual_info_classif
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

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


# True if a column has more than 10 different values and holds numbers (for example Age or Fare).
# The EDA tab cuts these columns into 5 equal-size groups before comparing groups.
def needs_bins(series):
    return pd.api.types.is_numeric_dtype(series) and series.nunique() > 10


# Page settings and the two tabs
st.set_page_config(page_title="Data Preparation Workbench", layout="wide")
tab, eda_tab = st.tabs(["Data Preparation Workbench", "EDA"])

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

# The EDA tab: it looks at the prepared data (df), the result of the workbench steps
with eda_tab:
    st.title("EDA")
    st.write(f"This tab shows the **prepared data**: {source} after the {len(results)} workbench step(s). "
             f"{df.shape[0]} rows, {df.shape[1]} columns.")

    # Section 1: summary statistics of the number columns
    st.header("1. Summary statistics")
    st.code("df.describe()", language="python")
    st.dataframe(df.describe())

    # Section 1 (continued): how often each value appears in a chosen column
    st.subheader("Frequency table")
    vc_col = st.selectbox("Column to count", list(df.columns), index=None,
                          placeholder="Choose a column...", key="eda_vc_col")
    if vc_col is not None:
        st.code(f'df["{vc_col}"].value_counts()', language="python")
        st.dataframe(df[vc_col].value_counts())

    # Section 2: histogram of a chosen number column
    st.header("2. Histogram")
    number_cols = list(df.select_dtypes("number").columns)
    hist_col = st.selectbox("Number column", number_cols, index=None,
                            placeholder="Choose a column...", key="eda_hist_col")
    if hist_col is not None:
        st.code(f'df["{hist_col}"].plot.hist(bins=20)', language="python")
        fig, ax = plt.subplots(figsize=(7, 3))
        df[hist_col].plot.hist(bins=20, ax=ax, color="#4C78A8", edgecolor="white")
        ax.set_xlabel(hist_col)
        ax.set_ylabel("count")
        ax.spines[["top", "right"]].set_visible(False)
        st.pyplot(fig)

    # Section 3: correlation table of the number columns
    st.header("3. Correlation table")
    st.code("df.corr(numeric_only=True).round(2)", language="python")
    st.dataframe(df.corr(numeric_only=True).round(2))

    # Choose the target: any column that holds only 0 and 1 and has no missing values
    st.header("4. Target")
    target_cols = [c for c in df.columns
                   if df[c].notnull().all() and set(df[c].unique()) <= {0, 1} and df[c].nunique() == 2]
    if not target_cols:
        st.info("This data has no 0/1 column without missing values, so sections 5 and 6 cannot be shown.")
        st.stop()
    target = st.selectbox("Target column (0/1)", target_cols,
                          index=target_cols.index("Survived") if "Survived" in target_cols else 0,
                          key="eda_target")

    # Section 5: the rate of the target (for example Survived) in each group of a chosen column.
    # Number columns with many values are cut into 5 equal-size groups first.
    st.header(f"5. Rate of {target} for each group")
    group_options = [c for c in df.columns if c != target and (df[c].nunique() <= 10 or needs_bins(df[c]))]
    group_col = st.selectbox("Group column", group_options, index=None,
                             placeholder="Choose a column...", key="eda_group_col")
    if group_col is not None:
        if needs_bins(df[group_col]):
            groups = pd.qcut(df[group_col], 5, duplicates="drop")
            code = (f'df.groupby(pd.qcut(df["{group_col}"], 5, duplicates="drop"), observed=True)'
                    f'["{target}"].agg(["mean", "count"]).round(3)')
        else:
            groups = df[group_col]
            code = f'df.groupby("{group_col}")["{target}"].agg(["mean", "count"]).round(3)'
        st.code(code, language="python")
        rates = df.groupby(groups, observed=True)[target].agg(["mean", "count"]).round(3)
        # Show group names as text so ranges like (19.0, 25.0] display correctly
        rates.index = rates.index.astype(str)
        st.dataframe(rates)

    # Section 6: feature weighting by information gain and chi-squared
    st.header("6. Feature weighting: information gain and chi-squared")
    if not HAS_SKLEARN:
        st.warning("scikit-learn is not installed. Run `pip install scikit-learn` in a terminal, then click Rerun.")
    else:
        # Turn each column into group numbers (0, 1, 2, ...):
        # number columns with many values -> 5 equal-size groups; columns with at most 10 values -> one number per value.
        # Columns with missing values, and text columns with many values (like Name), are skipped.
        X = pd.DataFrame(index=df.index)
        skipped = []
        for c in df.columns:
            if c == target:
                continue
            if df[c].isnull().any():
                skipped.append(f"{c} (has missing values)")
            elif needs_bins(df[c]):
                X[c] = pd.qcut(df[c], 5, labels=False, duplicates="drop")
            elif df[c].nunique() <= 10:
                X[c] = df[c].astype("category").cat.codes
            else:
                skipped.append(f"{c} (text with more than 10 values)")

        st.code(
            "# for each number column with many values (e.g. Age): 5 equal-size groups\n"
            'X[col] = pd.qcut(df[col], 5, labels=False, duplicates="drop")\n'
            "# for each column with at most 10 values (e.g. Sex): one number per value\n"
            'X[col] = df[col].astype("category").cat.codes\n'
            f'info_gain = mutual_info_classif(X, df["{target}"], discrete_features=True)\n'
            f'chi2_scores, p_values = chi2(X, df["{target}"])',
            language="python",
        )

        if X.shape[1] == 0:
            st.info("No columns can be scored.")
        else:
            # Compute both scores and show them in one table, highest information gain first
            info_gain = mutual_info_classif(X, df[target], discrete_features=True)
            chi2_scores, p_values = chi2(X, df[target])
            weights = pd.DataFrame(
                {"information gain": info_gain, "chi-squared": chi2_scores, "chi-squared p-value": p_values},
                index=X.columns,
            ).sort_values("information gain", ascending=False)
            st.dataframe(weights.round(4))
        if skipped:
            st.write("Skipped: " + ", ".join(skipped))
