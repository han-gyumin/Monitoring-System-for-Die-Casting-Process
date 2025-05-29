# ================================
# shared.py
# ✅ 실시간 스트리밍 기반 공정 모니터링 대시보드용 공통 모듈
# - 데이터 로딩
# - 센서 이름 정의
# - 실시간 시뮬레이션 클래스 정의
# ================================

import pandas as pd
from pathlib import Path
import joblib

# ================================
# 📁 데이터 로딩
# ================================
app_dir = Path(__file__).parent

# ✅ 정적 데이터 (누적 데이터 분석용)
try:
    static_df = pd.read_csv(app_dir / "./data/df_final.csv", encoding="utf-8")
except UnicodeDecodeError:
    static_df = pd.read_csv(app_dir / "./data/df_final.csv",  encoding="ISO-8859-1")

# ✅ 스트리밍 데이터 (실시간 시각화용)
try:
    streaming_df = pd.read_csv(app_dir / "./data/streaming_df.csv",  encoding="utf-8")
except UnicodeDecodeError:
    streaming_df = pd.read_csv(app_dir / "./data/streaming_df.csv",  encoding="cp949")



# ✅ 센서 데이터의 사람이 읽기 쉬운 한글 이름과 단위 정의
# UI 카드나 그래프 라벨링 시 활용
sensor_labels = {
    "molten_temp": ("용탕온도", "°C"),
    "cast_pressure": ("주조압력", "bar"),
    "high_section_speed": ("고속구간속도", "mm/s"),
    "low_section_speed": ("저속구간속도", "mm/s"),
    # 필요 시 더 추가
}
# 사용할 센서 컬럼 선택
selected_cols = [
    'registration_time',
    'molten_temp',           # 용탕 온도
    'cast_pressure',         # 주조 압력
    'high_section_speed',    # 고속 구간 속도
    'low_section_speed',     # 저속 구간 속도
    'biscuit_thickness',      # 비스킷 두께
    'passorfail'
]
df_selected = streaming_df[selected_cols].reset_index(drop=True)

# ================================
# 🔧 실시간 스트리밍 클래스 정의
# ================================
class RealTimeStreamer:
    def __init__(self):
        self.full_data = df_selected.copy()
        self.current_index = 0

    def get_next_batch(self, batch_size=1):
        if self.current_index >= len(self.full_data):
            return None
        end_index = min(self.current_index + batch_size, len(self.full_data))
        batch = self.full_data.iloc[self.current_index:end_index].copy()
        self.current_index = end_index
        return batch

    def get_current_data(self):
        if self.current_index == 0:
            return pd.DataFrame()
        return self.full_data.iloc[:self.current_index].copy()

    def reset_stream(self):
        self.current_index = 0

    def get_stream_info(self):
        return {
            'total_rows': len(self.full_data),
            'current_index': self.current_index,
            'progress': (self.current_index / len(self.full_data)) * 100 if len(self.full_data) > 0 else 0
        }


class StreamAccumulator:
    def __init__(self, base_df: pd.DataFrame):
        # 누적에 사용할 기준 컬럼 (최초 static_df 기반)
        self.columns = list(base_df.columns)
        self.total_df = base_df.copy()

    def accumulate(self, new_data: pd.DataFrame):
        if not new_data.empty:
            try:
                available_cols = [col for col in self.columns if col in new_data.columns]
                new_data = new_data[available_cols].copy()
                self.total_df = pd.concat([self.total_df, new_data], ignore_index=True)
            except Exception as e:
                print(f"[⛔ accumulate 중 오류] {e}")

    def get_data(self):
        return self.total_df.copy()

    def reset(self):
        # 누적 데이터프레임을 초기 상태(static_df 기반)로 리셋
        self.total_df = static_df[self._common_columns()].copy()

    def _common_columns(self):
        # static_df와 streaming_df 간의 공통 컬럼을 리스트로 반환
        return sorted(set(static_df.columns).intersection(set(streaming_df.columns)))

