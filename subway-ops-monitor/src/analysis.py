import pandas as pd
from db_client import DbClient
from datetime import timedelta

class SubwayAnalyzer:
    def __init__(self):
        self.db = DbClient()

    def fetch_data(self, limit=1000):
        """최근 데이터를 가져옵니다."""
        print(f"Fetching last {limit} records from DB...")
        response = self.db.supabase.table("subway_time")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['last_rec_time'] = pd.to_datetime(df['last_rec_time'], errors='coerce') # API 포맷에 따라 조정 필요
        return df

    def analyze_interval_regularity(self, df):
        """1. 배차 간격 정기성 분석"""
        print("\n=== [Analysis 1] 배차 간격 정기성 분석 ===")
        if df.empty:
            print("데이터가 부족합니다.")
            return

        # 특정 노선/방향/역 기준으로 정렬
        # 예: 2호선(1002), 내선(0), 특정 역
        # 여기서는 전체 데이터에서 샘플링하여 보여줌
        
        target_lines = df['line_name'].unique()
        
        for line in target_lines:
            line_df = df[df['line_name'] == line]
            # 역별로 그룹화하여 시간 차이 계산
            # (단순화를 위해 데이터가 충분하다고 가정하고 가장 최근 도착 시간들의 차이를 계산)
            
            # 같은 역, 같은 방향의 열차들에 대해 도착 시간 차이 계산
            # train_status: 1(도착) 인 경우만 필터링하거나, last_rec_time 기준으로 정렬
            
            sorted_df = line_df.sort_values(by=['station_name', 'direction_type', 'created_at'])
            sorted_df['prev_arrival'] = sorted_df.groupby(['station_name', 'direction_type'])['created_at'].shift(1)
            sorted_df['interval'] = sorted_df['created_at'] - sorted_df['prev_arrival']
            
            # 배차 간격 통계
            intervals = sorted_df['interval'].dropna()
            if not intervals.empty:
                avg_interval = intervals.mean()
                std_interval = intervals.std() # 표준편차로 불규칙성 측정 (Bunching Index 유사)
                
                print(f"[{line}] 평균 배차 간격: {avg_interval}, 불규칙성(One Sigma): {std_interval}")
            else:
                print(f"[{line}] 배차 간격 계산을 위한 데이터 부족")
                
        # Return summary stats for dashboard
        # Group by line and calculate stats
        if not df.empty:
            df_sorted = df.sort_values(by=['station_name', 'direction_type', 'created_at'])
            df_sorted['prev_arrival'] = df_sorted.groupby(['station_name', 'direction_type'])['created_at'].shift(1)
            df_sorted['interval'] = (df_sorted['created_at'] - df_sorted['prev_arrival']).dt.total_seconds() / 60.0
            
            # Line-level stats
            stats = df_sorted.groupby('line_name')['interval'].agg(['mean', 'std', 'count']).reset_index()
            return stats
        return pd.DataFrame()

    def analyze_delay_hotspots(self, df):
        """2. 지연 발생 구간 탐지 (체류 시간)"""
        print("\n=== [Analysis 2] 지연 발생 구간 (Hotspots) ===")
        if df.empty: return pd.DataFrame()

        # train_number 별로 역에서의 체류 시간 추정
        # 같은 train_number가 같은 station_id에서 머무르는 시간 (count * batch_interval)
        
        # 열차별, 역별 체류 횟수 카운트
        dwell_counts = df.groupby(['line_name', 'station_name', 'train_number']).size().reset_index(name='observed_count')
        
        # 단순히 많이 관측된 곳 = 오래 머무른 곳으로 추정 (배치 주기가 1분이면 count 3 = 3분 체류)
        # 상위 5개 지연 의심 역 출력
        top_delays = dwell_counts.sort_values(by='observed_count', ascending=False).head(10)
        print("Top 5 체류 시간 긴 구간 (지연 의심):")
        print(top_delays.head(5))
        return top_delays

    def analyze_turnaround_efficiency(self, df):
        """3. 회차 효율성 분석"""
        print("\n=== [Analysis 3] 회차 효율성 분석 ===")
        # 종착역 근처 데이터 필터링
        # train_status가 도착(1)이고 dest_station_name와 station_name이 같은 경우 찾기 등
        print("데이터가 더 축적되어야 분석 가능합니다. (현재 로직 준비 중)")

    def analyze_express_interference(self, df):
        """4. 급행/일반 열차 간섭 분석"""
        print("\n=== [Analysis 4] 급행/일반 간섭 분석 ===")
        if df.empty: return
        
        express_trains = df[df['is_express'] == '1']
        normal_trains = df[df['is_express'] == '0']
        
        print(f"수집된 급행 위치 수: {len(express_trains)}, 일반 위치 수: {len(normal_trains)}")
        # 같은 역에 동시에 존재하거나 근접한 경우 탐지 로직 (복잡하므로 개수만 출력)
        return {
            "express_count": len(express_trains),
            "normal_count": len(normal_trains)
        }

    def run_all(self):
        df = self.fetch_data(limit=2000)
        if df.empty:
            print("DB에 데이터가 없습니다.")
            return

        self.analyze_interval_regularity(df)
        self.analyze_delay_hotspots(df)
        self.analyze_turnaround_efficiency(df)
        self.analyze_express_interference(df)

if __name__ == "__main__":
    analyzer = SubwayAnalyzer()
    analyzer.run_all()
