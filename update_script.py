import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 설정값 불러오기 (GitHub Secrets에서 가져옴)
FOOD_API_KEY = os.environ['FOOD_API_KEY']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
CREDS_JSON = os.environ['GOOGLE_SHEETS_CREDENTIALS']

def fetch_meal_data():
    # 식품안전나라 API 주소 (집단급식소 설치 현황)
    # 시작행 1, 종료행 1000 (한 번에 최대 1000개)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/I1250/json/1/1000"
    
    response = requests.get(url)
    data = response.json()
    
    if 'I1250' in data:
        rows = data['I1250']['row']
        return pd.DataFrame(rows)
    else:
        print("데이터를 가져오는 데 실패했습니다.")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        return

    # 구글 인증
    creds_dict = json.loads(CREDS_JSON)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 시트 열기
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0) # 첫 번째 탭
    
    # 기존 내용 지우고 새 데이터 넣기
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("구글 시트 업데이트 완료!")

if __name__ == "__main__":
    df_data = fetch_meal_data()
    update_google_sheet(df_data)
