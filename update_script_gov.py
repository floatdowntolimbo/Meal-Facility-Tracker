import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# 1. 설정값
API_KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_gov_data():
    # 행안부 집단급식소 API 기본 주소
    base_url = "http://apis.data.go.kr/1741000/GroupMealServiceStatus2/getGroupMealServiceStatus2"
    
    all_rows = []
    page_no = 1
    num_of_rows = 1000
    
    print(f"📡 행정안전부 데이터 수집 시작 (Key 확인: {API_KEY[:5]}...)")
    
    try:
        while True:
            # 💡 핵심: 인증키가 꼬이지 않도록 params 대신 URL에 직접 박아넣습니다.
            # requests가 키를 멋대로 인코딩하는 것을 방지합니다.
            request_url = (
                f"{base_url}?serviceKey={API_KEY}"
                f"&type=json&pageNo={page_no}&numOfRows={num_of_rows}"
            )
            
            response = requests.get(request_url, timeout=30)
            
            # 서버 응답이 200이 아닐 경우 상세 내용 출력
            if response.status_code != 200:
                print(f"❌ API 연결 실패: {response.status_code}")
                print(f"내용: {response.text}")
                break
                
            data = response.json()
            
            # 행안부 API의 데이터 계층 구조 접근
            if 'getGroupMealServiceStatus2' in data:
                header = data['getGroupMealServiceStatus2'][0]['head']
                total_count = int(header[0]['totalCount'])
                
                if len(data['getGroupMealServiceStatus2']) > 1:
                    items = data['getGroupMealServiceStatus2'][1]['row']
                    all_rows.extend(items)
                    print(f"📦 수집 중: {len(all_rows)} / {total_count}")
                    
                    if len(all_rows) >= total_count:
                        break
                    page_no += 1
                    time.sleep(0.3)
                else:
                    break
            else:
                # 가끔 에러 메시지가 RESULT에 담겨 오는 경우
                if 'RESULT' in data:
                    print(f"⚠️ 서버 에러 메시지: {data['RESULT'].get('MESSAGE', '알 수 없는 에러')}")
                break
                
        return pd.DataFrame(all_rows)
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        return
    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # 'GOV_DATA' 탭 확인 및 생성
        try:
            worksheet = sh.worksheet('GOV_DATA')
        except:
            worksheet = sh.add_worksheet(title="GOV_DATA", rows="100", cols="20")
            
        worksheet.clear()
        data_to_update = [df.columns.values.tolist()] + df.fillna('').values.tolist()
        worksheet.update(data_to_update)
        print(f"🎉 GOV_DATA 시트에 {len(df)}행 업데이트 완료!")
    except Exception as e:
        print(f"❌ 시트 업데이트 오류: {e}")

if __name__ == "__main__":
    df_gov = fetch_gov_data()
    update_google_sheet(df_gov)
