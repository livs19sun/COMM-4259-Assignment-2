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

Steps run in the order you add them, so order matters (for example, add a missing flag *before* filling that column).

## How to run
```
cd assignment_02/dashboard
pip install -r requirements.txt   # only if streamlit and pandas are not installed yet
streamlit run app.py
```
