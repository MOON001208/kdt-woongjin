import schedule
import time
from config import Config
from api_client import SeoulSubwayAPI
from db_client import DbClient

def job():
    print(f"\n[Batch Start] {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    api = SeoulSubwayAPI()
    db = DbClient()
    
    # 모니터링 대상 호선 (예시: 1~9호선, 경의중앙선 등 필요에 따라 추가)
    # API 호선명 파라미터 확인 필요. 보통 "1호선", "2호선" 등으로 사용
    target_lines = ["1호선", "2호선", "3호선", "4호선", "5호선", "6호선", "7호선", "8호선", "9호선"]
    
    total_inserted = 0
    
    for line in target_lines:
        print(f"Fetching {line}...", end=" ")
        data = api.get_realtime_positions(line)
        data = api.get_realtime_positions(line)
        if data:
            count = db.insert_positions(data)
            print(f"Inserted {count} records.")
            total_inserted += count
        else:
            print("No data.")
            
    print(f"[Batch End] Total {total_inserted} records processed.")

def main():
    print("=== Seoul Subway Monitoring System Started ===")
    
    try:
        Config.check_config()
    except ValueError as e:
        print(f"[System Error] 설정 오류: {e}")
        return

    # 테이블 초기화 (테이블이 없으면 생성)
    try:
        tmp_db = DbClient()
        tmp_db.initialize_table()
    except Exception as e:
        print(f"[System Warning] 테이블 초기화 중 오류: {e}")

    # 초기 실행

    job()
    
    # 주기적 실행 설정
    schedule.every(Config.BATCH_INTERVAL).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
