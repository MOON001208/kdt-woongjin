# 데이터 분석 상세 계획 (모니터링 관점)

본 문서는 `AGENT.md`의 4. 데이터 분석 프로젝트 목표를 구체화한 계획입니다.

## 1. 배차 간격 정기성 분석 (Interval Regularity)
- **목표**: 특정 역에 도착하는 열차들 사이의 시간 간격이 일정하게 유지되는지 모니터링
- **분석 지표**:
    - `Time Headway`: $t_{arrival}(n) - t_{arrival}(n-1)$
    - **Bunching Index**: 배차 간격의 변동성 측정 (변동 계수 등 활용)
- **활용 데이터**:
    - `station_id`, `line_id`, `direction_type` 별 `last_rec_time` 변화량
- **기대 효과**: 배차 몰림 현상 조기 탐지 및 승객 분산 유도

## 2. 지연 발생구간 탐지 (Delay Hotspots)
- **목표**: 역별 체류 시간 및 구간 주행 시간을 측정하여 상습 지연 구간 파악
- **분석 지표**:
    - `Dwell Time`: `train_status`가 `1:도착`에서 `2:출발`로 바뀌는 시간 차이
    - `Travel Time`: A역 출발 -> B역 도착 시간
- **활용 데이터**:
    - `train_number` 기준 역별 timestamp 추적
- **기대 효과**: 지연 원인 파악 및 운영 효율화

## 3. 회차 효율성 분석 (Turnaround Efficiency)
- **목표**: 종착역 도착 후 반대 방향으로 병행(Turnaround)하는 데 걸리는 시간 분석
- **분석 지표**:
    - `Turnaround Time`: 종착역 도착(`train_status=1`) ~ 반대편 노선 첫 식별 시간
- **활용 데이터**:
    - 종착역(`dest_station_id`) 부근에서의 `train_number` 추적 (열차 번호가 바뀌는지 확인 필요)
- **기대 효과**: 회차 병목 구간 식별 및 차량 운용 최적화

## 4. 급행/일반 열차 간섭 분석 (Congestion/Overtake)
- **목표**: 급행 열차가 일반 열차로 인해 서행하거나, 대피선 활용이 적절한지 분석
- **분석 지표**:
    - `Overtake Count`: 급행이 일반을 추월한 횟수
    - `Interference Duration`: 급행이 일반 열차 뒤에서 감속 운행한 시간
- **활용 데이터**:
    - `is_express` 필드 활용, 동일 구간 내 급행/일반 열차 위치 비교
- **기대 효과**: 급행 운행 스케줄 조정 및 대피선 활용 최적화
