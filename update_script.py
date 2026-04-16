import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 설정값 (환경 변수)
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    service_id = "I1250"
    
    # 20자리 키를 위한 주소 테스트 (두 가지 방식 시도)
    urls = [
        # 방식 A: 표준 경로 방식
        f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/500",
        # 방식 B: 보안(https) 및 파라미터 방식 시도
        f"https://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/500"
    ]
    
    print(f"📡 데이터 요청 시작 (인증키 길이: {len(FOOD_API_KEY)}자)")
    
    for i, url in enumerate(urls):
        try:
            print(f"🔄 시도 {i+1}...")
            response = requests.get(url, timeout=30)
            
            # 인증키 거부 메시지가 포함되어 있는지 확인
            if "인증키가 유효하지 않습니다" in response.text or response.status_code != 200:
                continue

            data = response.json()
            if service_id in data:
                rows = data[service_id]['row']
                print(f"✅ 성공: {len(rows)}개의 데이터를 가져왔습니다!")
                return pd.DataFrame(rows)
                
        except Exception as e:
            print(f"⚠️ 시도 {i+1} 중 오류 발생: {e}")
            continue
            
    print("❌ 모든 접속 방식으로 실패했습니다. 인증키 승인 여부를 다시 확인해주세요.")
    return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 업데이트할 데이터가 없어 종료합니다.")
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
        print(f"❌ 시트 업데이트 오류: {e}")

if __name__ == "__main__":
    df_final = fetch_meal_data()
    update_google_sheet(df_final)
