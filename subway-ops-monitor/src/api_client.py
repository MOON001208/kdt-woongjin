import requests
import datetime
from config import Config

class SeoulSubwayAPI:
    def __init__(self):
        self.api_key = Config.SEOUL_API_KEY
        self.base_url = Config.SEOUL_API_URL

    def get_realtime_positions(self, subway_line: str):
        """
        특정 호선의 실시간 열차 위치 정보를 가져옵니다.
        :param subway_line: 호선명 (예: '1호선', '2호선')
        :return: API 응답 JSON 데이터 (리스트)
        """
        # API URL 구성: http://swopenapi.seoul.go.kr/api/subway/(key)/json/realtimePosition/0/50/(line)
        # 0/50은 요청 시작/종료 인덱스
        url = f"{self.base_url}/{self.api_key}/json/realtimePosition/0/50/{subway_line}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'realtimePositionList' in data:
                return data['realtimePositionList']
            else:
                print(f"[API Error] {subway_line} 데이터 없음 또는 에러: {data.get('RESULT', {}).get('MESSAGE')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"[API Error] 요청 실패: {e}")
            return []
