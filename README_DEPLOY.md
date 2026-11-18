# RR Cricket Pressure Dashboard — Render deployment

This package deploys the existing Dash app. It reads the already-aggregated CSV and does not recalculate player metrics or pressure indices.

## Files to put in the same GitHub repository root

- `pressure_dashboard.py`
- `requirements.txt`
- `render.yaml`
- `agg_data_playerwise_dashboard.csv`  **(export this from your notebook; it is not included in this package)**

At the end of the notebook, after `agg_data_playerwise` includes player names and pressure-specific columns, run:

```python
agg_data_playerwise.to_csv("agg_data_playerwise_dashboard.csv", index=False)
```

The CSV must be in the same folder as `pressure_dashboard.py` in the deployed repository.

## Deploy on Render

1. Push these files and the aggregated CSV to a GitHub repository. A private repository is fine; give Render permission to access it.
2. Open https://dashboard.render.com/ and choose **New → Blueprint** (or **New → Web Service**).
3. For Blueprint deployment, connect the repository containing `render.yaml` and follow the prompts.
4. For manual Web Service deployment, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn pressure_dashboard:server`
5. Wait for the deployment to finish, open the generated `https://...onrender.com` URL, and test all dashboard selectors and tables.
6. Share that URL with the judges.

## Important

- Do not upload the original ball-by-ball data unless the competition rules explicitly allow it. The dashboard needs only the final aggregated player-wise CSV.
- Confirm that the competition permits sharing the derived player data with judges through a hosted dashboard.
- Render Free web services can sleep after 15 minutes without traffic; the first visit after sleep may take about a minute to wake up. Open the dashboard shortly before the judging session, or use a paid always-on instance if uninterrupted access is essential.
- When you change the player-wise CSV, commit and push the updated file to GitHub to trigger a redeploy (or manually trigger a deploy in Render).
