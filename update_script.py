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
    # 데이터 양을 100개로 줄여서 안정성 확보
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/I1250/json/1/100"
    
    print("데이터를 불러오는 중입니다...")
    try:
        response = requests.get(url, timeout=30)
        # 응답 내용 확인용 로그
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            print("서버 연결에 실패했습니다.")
            return None

        # 혹시 결과가 비어있는지 확인
        if not response.text.strip():
            print("서버에서 빈 내용을 보냈습니다. 인증키를 다시 확인해주세요.")
            return None

        data = response.json()
        if 'I1250' in data:
            rows = data['I1250']['row']
            print(f"성공! {len(rows)}개의 데이터를 찾았습니다.")
            return pd.DataFrame(rows)
        else:
            print("데이터 형식이 올바르지 않습니다.")
            return None
    except Exception as e:
        print(f"에러 발생: {e}")
        return None

# (이하 update_google_sheet 함수는 동일)
