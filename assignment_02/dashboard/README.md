# Data Preparation Workbench

A Streamlit app (one tab, **Data Preparation Workbench**) for Assignment 2, Part 2B.
You choose every step; the app makes no decisions on its own and uses no AI model.

## What it does
1. **Profile:** loads an uploaded CSV, or `data/titanic_features.csv` when nothing is uploaded, and shows the rows,
   columns, and each column's type, missing count and missing share.
2. **Add steps** from a fixed menu:
   - drop a column
   - fill missing values (mean, median, most frequent, or a value you type)
   - fill missing values with the median of each group (for example Age by Pclass)
   - add a 0/1 missing-value flag (1 if missing, or 1 if present)
   - extract the title from a name column (for example "Mr", "Mrs")
   - dummy-code a column (0/1 columns)
   - drop rows that are missing a value
3. **Steps so far:** for each step, the pandas line it equals and the rows, columns and missing values before and after.
   **Undo last step** removes the last step; **Clear all steps** removes them all.
4. **Download** the prepared data as `prepared_data.csv`.

`data/titanic_train.csv` is kept only as a backup; the app does not use it.

## EDA tab
Looks at the **prepared data** (the result of the workbench steps; with no steps it is the loaded file).
Each part shows the pandas line it uses.
1. Summary statistics (`df.describe()`) and a frequency table of a chosen column (`value_counts()`).
2. A histogram of a chosen number column (`df["Age"].plot.hist(bins=20)`).
3. The correlation table (`df.corr(numeric_only=True)`).
4. A target column you choose (any 0/1 column with no missing values; Survived when it is there).
5. The rate of the target for each group of a chosen column (`groupby(...).agg(["mean", "count"])`).
   Number columns with more than 10 values are cut into 5 equal-size groups with `pd.qcut`.
6. Feature weighting by information gain (`mutual_info_classif`) and chi-squared (`chi2`) from scikit-learn,
   on the same groups. Columns with missing values, and text columns with more than 10 values, are skipped.
   Information gain is in nats (natural log), as scikit-learn reports it.

Steps run in the order you add them, so order matters (for example, add a missing flag *before* filling that column).

## How to run
```
cd assignment_02/dashboard
pip install -r requirements.txt   # only if a package is not installed yet (the EDA tab needs scikit-learn)
streamlit run app.py
```
