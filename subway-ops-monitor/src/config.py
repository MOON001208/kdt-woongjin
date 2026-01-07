import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    SEOUL_API_KEY = os.getenv("SEOUL_API_KEY")
    SEOUL_API_URL = "http://swopenAPI.seoul.go.kr/api/subway"
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # 배치 실행 주기 (초) - 기본값 60초
    BATCH_INTERVAL = int(os.getenv("BATCH_INTERVAL", 60))

    @staticmethod
    def check_config():
        """필수 환경변수가 설정되었는지 확인"""
        if not Config.SEOUL_API_KEY:
            raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError("SUPABASE 접속 정보가 설정되지 않았습니다.")
