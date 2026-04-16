import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. 환경 변수 설정 (GitHub Secrets에서 불러오기)
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_meal_data():
    # I1250: 집단급식소 설치 현황 (안정성을 위해 우선 500개만 가져옵니다)
    service_id = "I1250"
    url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/1/500"
    
    print(f"📡 데이터 요청 중: {service_id}...")
    
    try:
        response = requests.get(url, timeout=30)
        
        # HTTP 상태 코드가 200이 아니면 오류
        if response.status_code != 200:
            print(f"❌ 서버 연결 실패 (코드: {response.status_code})")
            return None

        # 결과가 비어있는지 확인
        if not response.text.strip():
            print("❌ 서버에서 빈 응답을 보냈습니다. 인증키를 다시 확인하세요.")
            return None

        data = response.json()
        
        # 정상 데이터 구조 확인
        if service_id in data:
            rows = data[service_id]['row']
            print(f"✅ 수집 성공: {len(rows)}개의 데이터를 가져왔습니다.")
            return pd.DataFrame(rows)
        
        # API 수준 에러 메시지 출력
        elif 'RESULT' in data:
            print(f"❌ API 오류: {data['RESULT'].get('MSG', '알 수 없는 에러')}")
            return None
        else:
            print(f"❓ 예상치 못한 응답: {data}")
            return None
            
    except Exception as e:
        print(f"❌ 처리 중 예외 발생: {e}")
        # 에러 원인을 파악하기 위해 응답 앞부분 출력
        if 'response' in locals():
            print(f"서버 응답 내용(일부): {response.text[:200]}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 업데이트할 데이터가 없어 작업을 종료합니다.")
        return

    try:
        # 구글 인증 및 클라이언트 실행
        creds_dict = json.loads(CREDS_JSON)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 스프레드시트 열기
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0) # 첫 번째 탭
        
        # 기존 내용 삭제 및 새 데이터 업로드
        worksheet.clear()
        # 모든 데이터를 문자열로 변환하여 에러 방지, 빈 값 처리
        df = df.fillna('')
        data_to_write = [df.columns.values.tolist()] + df.values.tolist()
        
        worksheet.update(data_to_write)
        print("🎉 구글 스프레드시트 업데이트가 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 중 오류: {e}")

if __name__ == "__main__":
    result_df = fetch_meal_data()
    update_google_sheet(result_df)
