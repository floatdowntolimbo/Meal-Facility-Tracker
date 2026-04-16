import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 환경 변수 안전하게 불러오기
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    # 주소 체계: 인증키/서비스명/확장자/시작/종료
    # I1250: 집단급식소 설치 현황
    service_id = "I1250"
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/1000"
    
    print(f"[{service_id}] 데이터 수집 시도 중...")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 서버 응답 에러: {response.status_code}")
            return None

        data = response.json()
        
        # 정상적으로 데이터가 들어온 경우
        if service_id in data:
            rows = data[service_id]['row']
            print(f"✅ 성공! {len(rows)}개의 데이터를 가져왔습니다.")
            return pd.DataFrame(rows)
        
        # 인증키 오류 등 API 자체 에러 메시지가 있는 경우
        elif 'RESULT' in data:
            print(f"❌ API 오류 메시지: {data['RESULT'].get('MSG', '알 수 없는 에러')}")
            return None
        else:
            print(f"❓ 예상치 못한 응답 구조: {data}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 처리할 데이터가 없어 시트 업데이트를 건너뜁니다.")
        return

    try:
        # 구글 인증 정보 로드
        creds_dict = json.loads(CREDS_JSON)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 시트 열기 및 데이터 쓰기
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0) # 첫 번째 탭
        
        # 기존 데이터 삭제 후 헤더와 함께 업데이트
        worksheet.clear()
        df = df.fillna('') # 결측치 처리
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print("🎉 구글 스프레드시트 업데이트 완료!")
        
    except Exception as e:
        print(f"❌ 구글 시트 오류: {e}")

if __name__ == "__main__":
    df_result = fetch_meal_data()
    update_google_sheet(df_result)
