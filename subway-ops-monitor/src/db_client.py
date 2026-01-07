from supabase import create_client, Client
from .config import Config
from datetime import datetime

class DbClient:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def insert_positions(self, positions: list):
        """
        API에서 수집한 열차 위치 리스트를 DB에 일괄 삽입합니다.
        :param positions: API 원본 데이터 리스트
        :return: 삽입 성공 여부/개수
        """
        if not positions:
            return 0
        
        transformed_data = [self._transform_data(pos) for pos in positions]
        
        try:
            # Supabase insert
            response = self.supabase.table("realtime_subway_positions").insert(transformed_data).execute()
            # response.data 확인 (버전에 따라 다를 수 있음)
            return len(transformed_data)
        except Exception as e:
            print(f"[DB Error] 데이터 삽입 실패: {e}")
            return 0

    def _transform_data(self, raw: dict) -> dict:
        """
        API 원본 데이터를 DB 스키마에 맞게 변환 (Snake case 매핑)
        """
        # Boolean 변환 처리 (lstcarAt 등)
        # API에서 "0", "1" string으로 올 수 있음
        is_last = raw.get('lstcarAt') == '1'
        
        # AGENT.md 정의 된 매핑 따름
        return {
            "line_id": raw.get('subwayId'),
            "line_name": raw.get('subwayNm'),
            "station_id": raw.get('statnId'),
            "station_name": raw.get('statnNm'),
            "train_number": raw.get('trainNo'),
            "last_rec_date": raw.get('lastRecptnDt'),
            "last_rec_time": raw.get('recptnDt'),
            "direction_type": raw.get('updnLine'),
            "dest_station_id": raw.get('statnTid'),
            "dest_station_name": raw.get('statnTnm'),
            "train_status": raw.get('trainSttus'),
            "is_express": raw.get('directAt'),
            "is_last_train": str(is_last), # DB 스키마가 VARCHAR일 경우. Boolean이면 True/False
            # created_at은 DB Default 값 사용
        }
