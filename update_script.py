import os
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# 설정값
FOOD_API_KEY = os.environ.get('FOOD_API_KEY', '').strip()
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '').strip()
CREDS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')

def fetch_all_data():
    service_id = "I1210"
    all_rows = []
    start_idx = 1
    end_idx = 1000  # API 1회 최대 호출량
    
    print(f"📡 {service_id} 전체 데이터 수집 시작...")
    
    try:
        while True:
            url = f"http://openapi.foodsafetykorea.go.kr/api/{FOOD_API_KEY}/{service_id}/json/{start_idx}/{end_idx}"
            response = requests.get(url, timeout=30)
            data = response.json()
            
            # 데이터 존재 확인
            if service_id in data:
                total_count = int(data[service_id]['total_count'])
                rows = data[service_id]['row']
                all_rows.extend(rows)
                
                print(f"📦 수집 중: {start_idx} ~ {len(all_rows)} / {total_count}")
                
                # 모든 데이터를 다 가져왔으면 반복 중단
                if len(all_rows) >= total_count:
                    break
                
                # 다음 구간 설정
                start_idx += 1000
                end_idx += 1000
                time.sleep(0.1) # 서버 부하 방지용 짧은 대기
            else:
                print("❌ 더 이상 데이터를 가져올 수 없거나 오류가 발생했습니다.")
                break
                
        print(f"✅ 수집 완료! 총 {len(all_rows)}개의 데이터를 확인했습니다.")
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
        worksheet = sh.get_worksheet(0)
        
        worksheet.clear()
        # 데이터가 많을 경우를 대비해 리스트 변환 후 한 번에 업데이트
        data_to_update = [df.columns.values.tolist()] + df.fillna('').values.tolist()
        worksheet.update(data_to_update)
        print(f"🎉 구글 시트에 {len(df)}행 업데이트 완료!")
    except Exception as e:
        print(f"❌ 시트 업데이트 오류: {e}")

if __name__ == "__main__":
    df_all = fetch_all_data()
    update_google_sheet(df_all)
