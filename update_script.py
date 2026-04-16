import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 설정값 불러오기
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    service_id = "I1250"
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/1000"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
        if service_id in data:
            rows = data[service_id]['row']
            return pd.DataFrame(rows)
        return None
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        return
    try:
        creds_dict = json.loads(CREDS_JSON)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        worksheet.clear()
        df = df.fillna('')
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print("구글 시트 업데이트 성공!")
    except Exception as e:
        print(f"시트 업데이트 오류: {e}")

if __name__ == "__main__":
    df_result = fetch_meal_data()
    update_google_sheet(df_result)
