import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# ⚠️ 테스트를 위해 본인의 20자리 인증키를 아래 따옴표 안에 직접 넣으세요.
# 성공하면 나중에 다시 Secrets 방식으로 돌려놓으면 됩니다.
FOOD_API_KEY = "7e04fbb5ff4148c6b427" 

# 나머지 설정은 그대로 Secrets에서 가져옵니다.
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    service_id = "I1210"
    # 주소창에서 성공했던 그 형식을 100% 재현합니다.
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/100"
    
    print(f"📡 데이터 요청 시작 (인증키 직접 입력 방식)")
    
    try:
        response = requests.get(url, timeout=30)
        
        # 서버에서 보낸 응답이 HTML(스크립트 에러)인지 확인
        if "<script" in response.text:
            print("❌ 오류: 서버가 인증키를 거절했습니다. (IP 차단 또는 키 오류)")
            # 어떤 에러 메시지가 뜨는지 확인하기 위해 출력
            print(f"서버 응답 내용: {response.text}")
            return None

        data = response.json()
        if service_id in data:
            rows = data[service_id]['row']
            print(f"✅ 성공: {len(rows)}개의 데이터를 수집했습니다.")
            return pd.DataFrame(rows)
        else:
            print(f"❌ API 응답 실패: {data}")
            return None
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty: return
    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.fillna('').values.tolist())
        print("🎉 구글 시트 업데이트 완료!")
    except Exception as e:
        print(f"❌ 시트 업데이트 오류: {e}")

if __name__ == "__main__":
    df_data = fetch_meal_data()
    update_google_sheet(df_data)
