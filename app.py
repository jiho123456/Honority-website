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
    # 강제탈퇴 기록
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kicked_users (
            username TEXT PRIMARY KEY,
            reason   TEXT NOT NULL,
            kicked_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    # 채팅방
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            username TEXT,
            message  TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 과제 공유
    cur.execute("""
        CREATE TABLE IF NOT EXISTS homeworks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            due_date DATE,
            posted_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 현재 도서 & 토론 주제
    cur.execute("""
        CREATE TABLE IF NOT EXISTS current_book (
            id SERIAL PRIMARY KEY,
            book_title TEXT,
            week_of DATE,
            debate_topic TEXT,
            posted_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 추천 도구
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id SERIAL PRIMARY KEY,
            name TEXT,
            url TEXT,
            description TEXT,
            added_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 오늘의 단어
    cur.execute("""
        CREATE TABLE IF NOT EXISTS word_of_day (
            id SERIAL PRIMARY KEY,
            word TEXT,
            definition TEXT,
            date DATE UNIQUE
        );
    """)
    # 수업 일정
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id SERIAL PRIMARY KEY,
            class_date DATE,
            content TEXT
        );
    """)
    # 학습 자료
    cur.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            file_url TEXT,
            uploaded_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 에세이 업로드
    cur.execute("""
        CREATE TABLE IF NOT EXISTS essays (
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_path TEXT,
            uploaded_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # Newbery 도서 평점
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newbery_books (
            id SERIAL PRIMARY KEY,
            title TEXT,
            rating INTEGER,
            rated_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # 토론 기사
    cur.execute("""
        CREATE TABLE IF NOT EXISTS debate_articles (
            id SERIAL PRIMARY KEY,
            url TEXT,
            description TEXT,
            shared_by TEXT,
            timestamp TIMESTAMPTZ
        );
    """)
    # User logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (
            id SERIAL PRIMARY KEY,
            username TEXT,
            action TEXT,
            timestamp TIMESTAMPTZ DEFAULT now()
        );
    """)
    # System logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            level TEXT,
            message TEXT,
            timestamp TIMESTAMPTZ DEFAULT now()
        );
    """)
    # Announcements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id SERIAL PRIMARY KEY,
            content TEXT,
            posted_by TEXT,
            timestamp TIMESTAMPTZ DEFAULT now()
        );
    """)
    # Site settings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            id SERIAL PRIMARY KEY,
            setting_key TEXT UNIQUE,
            setting_value TEXT,
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """)
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
    if st.session_state.logged_in:
        st.write(f"현재 **{st.session_state.username}** ({st.session_state.role})님 로그인 상태입니다.")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.username  = "게스트"
            st.session_state.role      = "학생"
            st.rerun()
    else:
        choice = st.radio("옵션 선택", ["로그인","회원가입","게스트 로그인"])
        if choice == "로그인":
            with st.form("login", clear_on_submit=True):
                user = st.text_input("아이디")
                pwd  = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    # 강제탈퇴 체크
                    cur.execute("SELECT reason FROM kicked_users WHERE username=%s", (user,))
                    kicked_row = cur.fetchone()
                    if kicked_row:
                        reason = kicked_row[0]
                        st.error(f"🚫 강제탈퇴: {reason}\n새 계정을 만들어주세요.")
                    else:
                        # 특수 PW: 선생님/제작자
                        if pwd == "sqrtof4":
                            cur.execute("SELECT 1 FROM users WHERE username=%s", (user,))
                            if cur.fetchone():
                                st.session_state.logged_in = True
                                st.session_state.username  = user
                                st.session_state.role      = "제작자"
                                st.rerun()
                            else:
                                st.error("등록된 사용자가 아닙니다.")
                        else:
                            cur.execute(
                                "SELECT username,role FROM users WHERE username=%s AND password=%s",
                                (user,pwd)
                            )
                            row = cur.fetchone()
                            if row:
                                st.session_state.logged_in = True
                                st.session_state.username  = row[0]
                                st.session_state.role      = row[1]
                                st.rerun()
                            else:
                                st.error("아이디 또는 비밀번호가 틀렸습니다.")
        elif choice == "회원가입":
            with st.form("signup", clear_on_submit=True):
                nu = st.text_input("아이디")
                np = st.text_input("비밀번호", type="password")
                if st.form_submit_button("회원가입"):
                    try:
                        cur.execute(
                            "INSERT INTO users(username,password) VALUES(%s,%s)",
                            (nu,np)
                        )
                        st.success("회원가입 성공! 로그인 해주세요.")
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("이미 존재하는 아이디입니다.")
        else:
            if st.button("게스트 로그인"):
                st.session_state.logged_in = True
                st.session_state.username  = "게스트"
                st.session_state.role      = "학생"
                st.rerun()

# ---------------------------
# 4) 메뉴 선택
# ---------------------------
st.sidebar.title("메뉴")
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
st.image("assets/logo.jpg", width=200)
st.title("Honority English Academy")
st.write("영어 독서·토론을 통한 학습 커뮤니티입니다.")

# ---------------------------
# 페이지 구현
# ---------------------------

# 홈
if menu == "🏠 홈":
    st.header("Welcome to Honority!")
    st.write("""
    - 📖 Newbery 도서 토론 & 🗣 Debate  
    - 💬 실시간 채팅  
    - ✍️ 에세이 업로드  
    ...  
    """)

# 채팅방
elif menu == "💬 채팅방":
    st.header("실시간 채팅")
    # 메시지 입력
    with st.form("chat"):
        name = st.text_input("이름", value=st.session_state.get("username",""))
        msg  = st.text_input("메시지")
        if st.form_submit_button("전송") and msg:
            cur.execute(
                "INSERT INTO chat_messages(username,message,timestamp) VALUES(%s,%s,%s)",
                (name, msg, datetime.utcnow())
            )
            st.success("전송됨")
    # 메시지 표시
    cur.execute("SELECT username,message,timestamp FROM chat_messages ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    for u,m,ts in rows[::-1]:
        st.markdown(f"**[{ts:%H:%M:%S}] {u}**: {m}")

# 과제 공유
elif menu == "📚 과제 공유":
    st.header("과제 공유")
    with st.form("hw"):
        title = st.text_input("과제명")
        desc  = st.text_area("설명")
        due   = st.date_input("마감일")
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO homeworks(title,description,due_date,posted_by,timestamp) VALUES(%s,%s,%s,%s,%s)",
                (title,desc,due,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("""
        SELECT title,description,due_date,posted_by FROM homeworks ORDER BY id DESC
    """)
    hw_rows = cur.fetchall()
    df = pd.DataFrame(hw_rows, columns=["과제","설명","마감일","등록자"])
    st.table(df)

# 도서·토론 주제
elif menu == "📖 도서·토론 주제":
    st.header("현재 주 차 도서 & 토론 주제")
    with st.form("book"):
        book  = st.text_input("도서 제목")
        topic = st.text_area("토론 주제")
        week  = st.date_input("주차 시작일", value=date.today())
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO current_book(book_title,week_of,debate_topic,posted_by,timestamp) VALUES(%s,%s,%s,%s,%s)",
                (book,week,topic,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("SELECT week_of,book_title,debate_topic,posted_by FROM current_book ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        st.write(f"**{row[0]} 주간**: {row[1]}  \n토론 주제: {row[2]}  \n등록자: {row[3]}")

# 추천 도구
elif menu == "🛠 추천 도구":
    st.header("추천 도구")
    with st.form("tool"):
        name = st.text_input("도구명")
        url  = st.text_input("URL")
        desc = st.text_area("설명")
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO tools(name,url,description,added_by,timestamp) VALUES(%s,%s,%s,%s,%s)",
                (name,url,desc,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("SELECT name,url,description,added_by FROM tools")
    tool_rows = cur.fetchall()
    df = pd.DataFrame(tool_rows, columns=["도구","URL","설명","등록자"])
    st.table(df)

# Word of the Day
elif menu == "📓 Word of the Day":
    st.header("Word of the Day")
    with st.form("wod"):
        wd  = st.text_input("단어")
        defi= st.text_area("뜻")
        dt  = st.date_input("날짜", value=date.today())
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO word_of_day(word,definition,date) VALUES(%s,%s,%s) ON CONFLICT(date) DO NOTHING",
                (wd,defi,dt)
            )
            st.success("등록됨")
    cur.execute("SELECT date,word,definition FROM word_of_day ORDER BY date DESC")
    wod_rows = cur.fetchall()
    df = pd.DataFrame(wod_rows, columns=["날짜","단어","뜻"])
    st.table(df)

# 수업 일정
elif menu == "🗓 수업 일정":
    st.header("수업 일정")
    with st.form("sched"):
        cd  = st.date_input("수업일")
        cont= st.text_area("내용")
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO schedule(class_date,content) VALUES(%s,%s)",
                (cd,cont)
            )
            st.success("등록됨")
    cur.execute("SELECT class_date,content FROM schedule ORDER BY class_date")
    sched_rows = cur.fetchall()
    df = pd.DataFrame(sched_rows, columns=["일자","내용"])
    st.table(df)

# 학습 자료
elif menu == "📂 학습 자료":
    st.header("학습 자료")
    with st.form("mat"):
        title = st.text_input("제목")
        desc  = st.text_area("설명")
        file  = st.file_uploader("파일 업로드")
        if st.form_submit_button("등록"):
            url = ""
            if file:
                os.makedirs("uploads_mat",exist_ok=True)
                fn = f"uploads_mat/{uuid.uuid4().hex}.{file.name.split('.')[-1]}"
                with open(fn,"wb") as f: f.write(file.getbuffer())
                url = fn
            cur.execute(
                "INSERT INTO materials(title,description,file_url,uploaded_by,timestamp) VALUES(%s,%s,%s,%s,%s)",
                (title,desc,url,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("SELECT title,description,file_url,uploaded_by FROM materials ORDER BY id DESC")
    mat_rows = cur.fetchall()
    df = pd.DataFrame(mat_rows, columns=["제목","설명","파일","등록자"])
    st.table(df)

# 에세이 업로드
elif menu == "✍️ 에세이 업로드":
    st.header("에세이 업로드")
    with st.form("essay"):
        title = st.text_input("제목")
        file  = st.file_uploader("에세이 파일")
        if st.form_submit_button("업로드") and file:
            os.makedirs("uploads_essay",exist_ok=True)
            fn = f"uploads_essay/{uuid.uuid4().hex}.{file.name.split('.')[-1]}"
            with open(fn,"wb") as f: f.write(file.getbuffer())
            cur.execute(
                "INSERT INTO essays(title,file_path,uploaded_by,timestamp) VALUES(%s,%s,%s,%s)",
                (title,fn,st.session_state.username,datetime.utcnow())
            )
            st.success("업로드됨")
    cur.execute("SELECT title,file_path,uploaded_by FROM essays ORDER BY id DESC")
    essay_rows = cur.fetchall()
    df = pd.DataFrame(essay_rows, columns=["제목","파일","등록자"])
    st.table(df)

# Newbery 도서 평점
elif menu == "⭐️ Newbery 도서 평점":
    st.header("Newbery 도서 평점")
    with st.form("nb"):
        book   = st.text_input("도서명")
        rating = st.slider("평점", 1, 5, 3)
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO newbery_books(title,rating,rated_by,timestamp) VALUES(%s,%s,%s,%s)",
                (book,rating,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("SELECT title,rating,rated_by FROM newbery_books ORDER BY rating DESC")
    nb_rows = cur.fetchall()
    df = pd.DataFrame(nb_rows, columns=["도서","평점","등록자"])
    st.table(df)

# 토론 기사 공유
elif menu == "🔗 토론 기사 공유":
    st.header("토론 기사 공유")
    with st.form("da"):
        link = st.text_input("URL")
        desc = st.text_area("설명")
        if st.form_submit_button("등록"):
            cur.execute(
                "INSERT INTO debate_articles(url,description,shared_by,timestamp) VALUES(%s,%s,%s,%s)",
                (link,desc,st.session_state.username,datetime.utcnow())
            )
            st.success("등록됨")
    cur.execute("SELECT url,description,shared_by FROM debate_articles ORDER BY id DESC")
    da_rows = cur.fetchall()
    df = pd.DataFrame(da_rows, columns=["URL","설명","등록자"])
    st.table(df)

# 선생님 페이지 (제작자 전용)
elif menu == "👩‍🏫 선생님 페이지":
    st.header("👩‍🏫 제작자 전용 관리 페이지")
    if st.session_state.role not in ["제작자", "선생님"]:
        st.error("접근 권한이 없습니다.")
        st.stop()

    # Admin tabs
    admin_tabs = st.tabs(["사용자 관리", "콘텐츠 관리", "시스템 설정"])
    
    # 1. User Management Tab
    with admin_tabs[0]:
        st.subheader("사용자 관리")
        
        # View all users
        cur.execute("SELECT username, role FROM users ORDER BY username")
        users = cur.fetchall()
        if users:
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
    with admin_tabs[1]:
        st.subheader("콘텐츠 관리")
        
        # Content type selection
        content_type = st.selectbox(
            "콘텐츠 유형 선택",
            ["과제", "학습 자료", "에세이", "토론 기사"]
        )
        
        if content_type == "과제":
            cur.execute("SELECT id, title, description, posted_by, timestamp FROM homeworks ORDER BY id DESC")
            content = cur.fetchall()
            columns = ["ID", "제목", "설명", "작성자", "작성일"]
        elif content_type == "학습 자료":
            cur.execute("SELECT id, title, description, uploaded_by, timestamp FROM materials ORDER BY id DESC")
            content = cur.fetchall()
            columns = ["ID", "제목", "설명", "작성자", "작성일"]
        elif content_type == "에세이":
            cur.execute("SELECT id, title, uploaded_by, timestamp FROM essays ORDER BY id DESC")
            content = cur.fetchall()
            columns = ["ID", "제목", "작성자", "작성일"]
        else:  # 토론 기사
            cur.execute("SELECT id, url, description, shared_by, timestamp FROM debate_articles ORDER BY id DESC")
            content = cur.fetchall()
            columns = ["ID", "URL", "설명", "작성자", "작성일"]
        
        if content:
            df_content = pd.DataFrame(content, columns=columns)
            st.dataframe(df_content, use_container_width=True)
            
            # Content deletion
            content_id = st.number_input("삭제할 콘텐츠 ID 입력", min_value=1)
            if st.button("콘텐츠 삭제", type="secondary"):
                if content_type == "과제":
                    cur.execute("DELETE FROM homeworks WHERE id = %s", (content_id,))
                elif content_type == "학습 자료":
                    cur.execute("DELETE FROM materials WHERE id = %s", (content_id,))
                elif content_type == "에세이":
                    cur.execute("DELETE FROM essays WHERE id = %s", (content_id,))
                else:
                    cur.execute("DELETE FROM debate_articles WHERE id = %s", (content_id,))
                st.success(f"✅ ID {content_id}의 콘텐츠가 삭제되었습니다.")
                st.rerun()
    
    # 3. System Settings Tab
    with admin_tabs[2]:
        st.subheader("시스템 설정")
        
        # Site settings
        st.write("### 사이트 설정")
        site_title = st.text_input("사이트 제목", value="Honority English Academy")
        site_description = st.text_area("사이트 설명", value="영어 독서·토론을 통한 학습 커뮤니티입니다.")
        
        if st.button("설정 저장"):
            # Here you would typically save these settings to a configuration table
            st.success("✅ 설정이 저장되었습니다.")
        
        # System announcements
        st.write("### 공지사항 관리")
        announcement = st.text_area("새 공지사항")
        if st.button("공지사항 게시"):
            cur.execute(
                "INSERT INTO announcements (content, posted_by, timestamp) VALUES (%s, %s, %s)",
                (announcement, st.session_state.username, datetime.utcnow())
            )
            st.success("✅ 공지사항이 게시되었습니다.")
        
        # View recent announcements
        cur.execute("SELECT content, posted_by, timestamp FROM announcements ORDER BY timestamp DESC LIMIT 5")
        announcements = cur.fetchall()
        if announcements:
            st.write("#### 최근 공지사항")
            for ann in announcements:
                st.write(f"**{ann[1]}** ({ann[2]:%Y-%m-%d %H:%M}): {ann[0]}")
        
        # System logs
        st.write("### 시스템 로그")
        cur.execute("""
            SELECT timestamp, level, message 
            FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT 100
        """)
        system_logs = cur.fetchall()
        if system_logs:
            df_system_logs = pd.DataFrame(system_logs, columns=["시간", "레벨", "메시지"])
            st.dataframe(df_system_logs, use_container_width=True)
