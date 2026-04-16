import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# 1. 설정값 (GitHub Secrets에서 가져오기)
API_KEY = os.environ.get('DATA_GO_KR_KEY', '').strip() # 공공데이터포털 Decoding 키
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_gov_data():
    # 행정안전부 집단급식소 API 주소
    base_url = "http://apis.data.go.kr/1741000/GroupMealServiceStatus2/getGroupMealServiceStatus2"
    
    all_rows = []
    page_no = 1
    num_of_rows = 1000 # 한 페이지당 최대 호출량
    
    print("📡 행정안전부 데이터 수집 시작...")
    
    try:
        while True:
            params = {
                'serviceKey': API_KEY,
                'type': 'json',
                'pageNo': page_no,
                'numOfRows': num_of_rows
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            
            # 응답 상태 확인
            if response.status_code != 200:
                print(f"❌ API 연결 실패: {response.status_code}")
                break
                
            data = response.json()
            
            # 행정안전부 API 특유의 응답 구조 처리
            # 보통 'getGroupMealServiceStatus2' -> 'item' 안에 데이터가 있음
            if 'getGroupMealServiceStatus2' in data:
                header = data['getGroupMealServiceStatus2'][0]['head']
                total_count = header[0]['totalCount']
                
                # 데이터 행 추출
                if len(data['getGroupMealServiceStatus2']) > 1:
                    items = data['getGroupMealServiceStatus2'][1]['row']
                    all_rows.extend(items)
                    
                    print(f"📦 수집 중: {len(all_rows)} / {total_count}")
                    
                    # 모든 데이터를 다 가져왔으면 종료
                    if len(all_rows) >= total_count:
                        break
                    
                    page_no += 1
                    time.sleep(0.2) # 서버 부하 방지
                else:
                    break
            else:
                print(f"⚠️ 예상치 못한 응답 구조: {data}")
                break
                
        print(f"✅ 수집 완료! 총 {len(all_rows)}개")
        return pd.DataFrame(all_rows)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def update_google_sheet(df):
    if df is None or df.empty:
        print("⏭️ 업데이트할 데이터가 없습니다.")
        return
    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # 새로운 시트(탭)를 만들거나 첫 번째 시트 선택
        # 기존 식품안전나라 데이터와 섞이지 않게 'GOV_DATA' 탭을 추천합니다.
        try:
            worksheet = sh.worksheet('GOV_DATA')
        except:
            worksheet = sh.add_worksheet(title="GOV_DATA", rows="100", cols="20")
            
        worksheet.clear()
        data_to_update = [df.columns.values.tolist()] + df.fillna('').values.tolist()
        worksheet.update(data_to_update)
        print(f"🎉 GOV_DATA 시트에 {len(df)}행 업데이트 완료!")
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 중 오류: {e}")

if __name__ == "__main__":
    df_gov = fetch_gov_data()
    update_google_sheet(df_gov)
