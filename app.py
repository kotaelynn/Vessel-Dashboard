import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 (Page Configuration)
# -----------------------------------------------------------------------------
# 모바일 환경(방선 중)에서도 잘 보이도록 layout을 'wide'로 설정하고, 탭 제목을 지정합니다.
st.set_page_config(
    page_title="Provision Dashboard",
    page_icon="🚢",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (구글 시트 연결)
@st.cache_data(ttl=60) # 60초마다 새로고침
def load_data():
    # secrets.toml에 정의된 'gsheets' 연결 정보를 사용
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 구글 시트 데이터 읽기 (1번째 워크시트)
    df = conn.read()
    return df

try:
    df = load_data()
    st.success("✅ 구글 시트 연결 성공!")
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.stop() # 에러나면 여기서 멈춤
    
# -----------------------------------------------------------------------------
# 3. 사이드바 (Sidebar) - 필터 기능 구현
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Options")

# 벤더 선택 필터 (Multiselect를 사용하여 여러 벤더 동시 선택 가능)
# 기본적으로 모든 벤더를 선택한 상태로 시작할 수도 있고, 비워둘 수도 있습니다.
unique_vendors = df['Vendor'].unique()
selected_vendors = st.sidebar.multiselect(
    "Select Vendor",
    options=unique_vendors,
    default=unique_vendors  # 기본값: 전체 선택
)

# -----------------------------------------------------------------------------
# 4. 메인 화면 구성 (Main Dashboard)
# -----------------------------------------------------------------------------

# (1) 헤더 및 제목
st.title("🚢 Provision Dashboard")
st.markdown("Last Update: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
st.markdown("---")

# (2) 데이터 필터링 로직
# 사용자가 사이드바에서 선택한 벤더에 해당하는 데이터만 추출합니다.
if selected_vendors:
    filtered_df = df[df['Vendor'].isin(selected_vendors)]
else:
    filtered_df = df  # 선택된 것이 없으면 전체 표시 (또는 빈 데이터)

# (3) 핵심 지표 (KPI) 표시 - 시니어 개발자의 팁!
# 단순히 표만 보여주는 것보다, '오늘 처리해야 할 건수'를 상단에 보여주면 업무 효율이 올라갑니다.
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Vessels", value=len(filtered_df))
with col2:
    # 'Pending' 상태인 건수 계산
    pending_count = len(filtered_df[filtered_df['Order_Status'] == 'Pending'])
    st.metric(label="Pending Orders", value=pending_count, delta_color="inverse")
with col3:
    # 가장 급한 배의 ETA 표시
    if not filtered_df.empty:
        earliest_eta = filtered_df['ETA'].min().strftime("%m-%d %H:%M")
        st.metric(label="Earliest ETA", value=earliest_eta)

# (4) 메인 데이터 테이블 표시
st.subheader("📋 Vessel List")

# 데이터프레임 스타일링: 'Order_Status'가 'Pending'인 행을 강조하고 싶다면
# styled_df 기능을 사용할 수 있으나, 여기서는 가독성을 위해 깔끔한 dataframe을 사용합니다.
# use_container_width=True를 쓰면 모바일 화면 너비에 맞게 표가 꽉 찹니다.

st.dataframe(
    filtered_df.style.applymap(
        lambda x: 'background-color: #ffcccc; color: red;' if x == 'Pending' else '',
        subset=['Order_Status']
    ),
    use_container_width=True,
    column_config={
        "ETA": st.column_config.DatetimeColumn(
            "ETA (Arrival)",
            format="D MMM YYYY, HH:mm",
            step=60,
        ),
    }
)

# -----------------------------------------------------------------------------
# 5. 하단 푸터 (Footer)
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("Developed by Provision Team | Powered by Vibe Coding Strategy")
