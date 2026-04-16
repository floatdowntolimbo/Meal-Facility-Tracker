import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 설정값 불러오기 (공백 자동 제거)
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    # 서비스 ID: I1250 (대문자 아이 + 1250)
    service_id = "I1250"
    # 요청 주소 형식 준수
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/500"
    
    print(f"📡 데이터 요청 시작: {service_id}")
    
    try:
        response = requests.get(url, timeout=30)
        
        # 만약 '인증키 유효하지 않음' 팝업 내용이 들어있다면?
        if "<script" in response.text:
            print("❌ 오류: 식품안전나라에서 인증키를 거부했습니다.")
            print("💡 해결책: GitHub Secrets에 넣은 인증키가 32자리 글자만 정확히 들어있는지 재확인하세요.")
            return None

        data = response.json()
        
        # 데이터가 정상적으로 들어온 경우
        if service_id in data:
            rows = data[service_id]['row']
            print(f"✅ 성공: {len(rows)}개의 데이터를 수집했습니다.")
            return pd.DataFrame(rows)
        else:
            msg = data.get('RESULT', {}).get('MSG', '알 수 없는 응답 구조')
            print(f"❌ API 응답 오류: {msg}")
            return None
            
    except Exception as e:
        print(f"❌ 시스템 오류 발생: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 데이터가 없어 시트 업데이트를 진행하지 않습니다.")
        return
    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        
        worksheet.clear()
        # 전체 데이터를 문자열로 변환하여 에러 방지
        worksheet.update([df.columns.values.tolist()] + df.fillna('').values.tolist())
        print("🎉 모든 데이터가 구글 시트에 업데이트되었습니다!")
    except Exception as e:
        print(f"❌ 구글 시트 오류: {e}")

if __name__ == "__main__":
    final_df = fetch_meal_data()
    update_google_sheet(final_df)
