import os
import uuid
import streamlit as st
import psycopg2
from datetime import datetime, date
import pandas as pd

# ---------------------------
# 1) DB 연결 및 테이블 초기화
# ---------------------------
@st.cache_resource
def get_conn():
    conn = psycopg2.connect(
        user=st.secrets["user"],
        password=st.secrets["password"],
        host=st.secrets["host"],
        port=st.secrets["port"],
        dbname=st.secrets["dbname"],
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=5
    )
    conn.autocommit = True
    return conn

def init_tables():
    tmp = psycopg2.connect(
        user=st.secrets["user"],
        password=st.secrets["password"],
        host=st.secrets["host"],
        port=st.secrets["port"],
        dbname=st.secrets["dbname"]
    )
    cur = tmp.cursor()
    # 사용자
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT '학생'
        );
    """)
    # ... (기타 테이블 생성 생략)
    # Add created_at to users table if it doesn't exist
    cur.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
    """)
    tmp.commit()
    tmp.close()

# 최초 1회 실행 후 주석 처리하세요
# init_tables()

conn = get_conn()
cur = conn.cursor()

# ---------------------------
# 2) 세션 초기화
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = "게스트"
    st.session_state.role     = "학생"

# ---------------------------
# 3) 사이드바: 로그인/회원가입
# ---------------------------
with st.sidebar.expander("로그인 / 회원가입"):
    # ... (로그인/회원가입 로직 생략)

# ---------------------------
# 4) 메뉴 선택
# ---------------------------
st.sidebar.title("메뉴")
# label이 빈 문자열이 되지 않도록 "메뉴"로 설정하고 화면에는 보이지 않게 숨깁니다.
menu = st.sidebar.radio(
    "메뉴",
    [
        "🏠 홈",
        "💬 채팅방",
        "📚 과제 공유",
        "📖 도서·토론 주제",
        "🛠 추천 도구",
        "📓 Word of the Day",
        "🗓 수업 일정",
        "📂 학습 자료",
        "✍️ 에세이 업로드",
        "⭐️ Newbery 도서 평점",
        "🔗 토론 기사 공유",
        "👩‍🏫 선생님 페이지"
    ],
    label_visibility="collapsed"
)

# ---------------------------
# 5) 공통 헤더
# ---------------------------
# ... (공통 헤더 생략)

# ---------------------------
# 페이지 구현
# ---------------------------
# ... (다른 메뉴들 생략)

# 선생님 페이지 (제작자 전용)
elif menu == "👩‍🏫 선생님 페이지":
    st.header("👩‍🏫 제작자 전용 관리 페이지")
    if st.session_state.role not in ["제작자", "선생님"]:
        st.error("접근 권한이 없습니다.")
        st.stop()

    admin_tabs = st.tabs(["사용자 관리", "콘텐츠 관리", "시스템 설정"])

    # 1. User Management Tab
    with admin_tabs[0]:
        st.subheader("사용자 관리")

        # View all users (created_at 컬럼이 없을 경우 에러 방지를 위해 제외)
        cur.execute("SELECT username, role FROM users ORDER BY username")
        users = cur.fetchall()
        if users:
            # created_at 컬럼을 빼고 두 개 항목만 표시
            df_users = pd.DataFrame(users, columns=["아이디", "현재 역할"])
            st.dataframe(df_users, use_container_width=True)

            # User actions
            col1, col2 = st.columns(2)
            with col1:
                selected_user = st.selectbox(
                    "사용자 선택",
                    [u[0] for u in users],
                    index=0
                )
                new_role = st.selectbox(
                    "새로운 역할 선택",
                    ["학생", "선생님", "제작자"],
                    index=0
                )
                if st.button("역할 업데이트"):
                    cur.execute(
                        "UPDATE users SET role = %s WHERE username = %s",
                        (new_role, selected_user)
                    )
                    st.success(f"✅ {selected_user}님의 역할이 '{new_role}' 로 변경되었습니다.")
                    st.rerun()

            with col2:
                if st.button("사용자 삭제", type="secondary"):
                    if st.session_state.username == selected_user:
                        st.error("자신의 계정은 삭제할 수 없습니다.")
                    else:
                        if st.checkbox("정말로 삭제하시겠습니까?"):
                            cur.execute("DELETE FROM users WHERE username = %s", (selected_user,))
                            st.success(f"✅ {selected_user}님의 계정이 삭제되었습니다.")
                            st.rerun()

        # User activity logs
        st.subheader("사용자 활동 로그")
        cur.execute("""
            SELECT username, action, timestamp 
            FROM user_logs 
            ORDER BY timestamp DESC 
            LIMIT 100
        """)
        logs = cur.fetchall()
        if logs:
            df_logs = pd.DataFrame(logs, columns=["사용자", "활동", "시간"])
            st.dataframe(df_logs, use_container_width=True)

    # 2. Content Management Tab
    # ... (콘텐츠 관리 생략)

    # 3. System Settings Tab
    # ... (시스템 설정 생략)
