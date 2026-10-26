# Lab 7: Customer Dashboard

A Streamlit dashboard for `data/Customer.csv` (1,000 customers, 17 columns).

## Data Preparation tab

Shows:
- rows and columns before and after preparation
- missing values in each column before and after preparation
- a bar chart of the average AgeAtJoin for churned (`Churn = 1`) and returning (`Churn = 0`) customers

## Data-preparation decisions

| Column | Decision |
|---|---|
| Reviews (83.2% missing), Feedback_Call (83.8% missing) | Add `HasReview` (1 if the customer left a review, else 0), then drop both columns (keep only columns with less than 80% missing). |
| ZipCode (476 five-digit, 524 nine-digit) | Keep the first five digits. Read as text so leading zeros are kept. |
| BirthYear (21.5% missing) | Leave missing values as missing. No rows dropped, nothing filled in. |
| New: AgeAtJoin | Year of JoinDate minus BirthYear (missing when BirthYear is missing). |

## How to run

From this folder (`lab_07/agent_demo/`):

```
pip install -r requirements.txt
streamlit run app.py
```

If `streamlit` or `python` is "not found", Python isn't on your PATH. Call it by its full path instead (on this computer):

```
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m streamlit run app.py
```

The app finds `data/Customer.csv` relative to `app.py`, so you can also run it from another folder, for example `streamlit run lab_07/agent_demo/app.py`.

## Files

- `app.py`: the dashboard
- `data/Customer.csv`: the raw data
- `ai_sessions/`: saved AI sessions
- `AI_USE_LOG.md`: AI use log (written by the student)
