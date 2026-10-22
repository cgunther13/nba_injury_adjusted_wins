# NBA Injury Adjusted Wins Dashboard

A Streamlit dashboard for exploring team-level NBA Injury Adjusted Wins from a CSV.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

The dashboard reads `running_injury_adjusted_wins.csv` from the same folder as `app.py`.

## Publish for free with Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, and `running_injury_adjusted_wins.csv`.
3. Visit https://share.streamlit.io/ and connect GitHub.
4. Create an app from your repository, selecting `app.py` as the main file.
5. Deploy and share the public URL.

## Daily updates

This starter version reads the CSV included in the deployed repository. A new CSV generated only on your own computer will **not** automatically appear on the public site. For automatic updates, connect the existing script to a scheduled GitHub Actions workflow (or another hosted job) that writes and commits the refreshed CSV. The right setup depends on where your Python script currently runs and where its inputs come from.

## Metric definition

The leaderboard currently sums `ADJUSTED_WIN` for each team across the selected date range. Confirm this aggregation is the intended season-long metric before treating the rankings as final.
