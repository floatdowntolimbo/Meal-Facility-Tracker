import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 설정값 불러오기
FOOD_API_KEY = os.environ['FOOD_API_KEY']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
CREDS_JSON = os.environ['GOOGLE_SHEETS_CREDENTIALS']

def fetch_meal_data():
    # 주소 오타 방지를 위해 f-string 사용
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/I1250/json/1/100"
    
    response = requests.get(url)
    
    # 에러 원인을 확인하기 위해 출력 추가
    print(f"응답 상태 코드: {response.status_code}")
    
    try:
        data = response.json()
        if 'I1250' in data:
            rows = data['I1250']['row']
            return pd.DataFrame(rows)
        else:
            # API에서 보내준 에러 메시지 출력 (인증키 오류 등)
            print("API 응답 오류:", data.get('result', data))
            return None
    except Exception as e:
        print("JSON 변환 실패! 받은 내용 맛보기:", response.text[:100])
        return None

# (나머지 update_google_sheet 함수는 동일)
