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
    # API 호출 제한 500개에 맞춰 설정
    service_id = "I1250"
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/500"
    
    print(f"📡 데이터 요청 시작: {service_id} (최대 500건)")
    
    try:
        response = requests.get(url, timeout=30)
        
        # HTML 에러 메시지가 오는지 확인 (인증키 오류 시 발생)
        if "<script" in response.text:
            print("❌ 오류: 인증키가 유효하지 않습니다. GitHub Secrets를 다시 확인하세요.")
            return None

        data = response.json()
        if service_id in data:
            rows = data[service_id]['row']
            print(f"✅ 성공: {len(rows)}개의 데이터를 수집했습니다.")
            return pd.DataFrame(rows)
        else:
            print(f"❌ API 응답 실패: {data.get('RESULT', {}).get('MSG', '알 수 없는 에러')}")
            return None
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 데이터가 없어 시트 업데이트를 건너뜁니다.")
        return
    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.fillna('').values.tolist())
        print("🎉 구글 스프레드시트 업데이트 완료!")
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 중 오류: {e}")

if __name__ == "__main__":
    df_result = fetch_meal_data()
    update_google_sheet(df_result)
