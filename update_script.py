name: Daily Meal Data Update

on:
  schedule:
    - cron: '0 22 * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11' # 3.9에서 3.11로 변경
      - name: Install dependencies
        run: pip install pandas requests gspread google-auth
      - name: Run Script
        env:
          FOOD_API_KEY: ${{ secrets.FOOD_API_KEY }}
          GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
          SPREADSHEET_ID: ${{ secrets.SPREADSHEET_ID }}
        run: python update_script.py
