import os
import uuid
import streamlit as st
import psycopg2
from datetime import datetime, date
import pandas as pd

# ---------------------------
# 1) 데이터베이스 초기화
# ---------------------------
def init_db():
    conn = psycopg2.connect(
        user=st.secrets["user"],
        password=st.secrets["password"],
        host=st.secrets["host"],
        port=st.secrets["port"],
        dbname=st.secrets["dbname"]
    )
    conn.autocommit = True
    # c = conn.cursor()

    # # users, kicked_users
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS users (
    #   id SERIAL PRIMARY KEY,
    #   username TEXT UNIQUE,
    #   password TEXT,
    #   role TEXT DEFAULT '학생'
    # );
    # """)
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS kicked_users (
    #   username TEXT PRIMARY KEY,
    #   reason TEXT NOT NULL,
    #   kicked_at TIMESTAMPTZ DEFAULT now()
    # );
    # """)

    # # chatting room
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS chat_messages (
    #   id SERIAL PRIMARY KEY,
    #   nickname TEXT,
    #   message TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # homeworks
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS homeworks (
    #   id SERIAL PRIMARY KEY,
    #   assignment TEXT,
    #   due_date DATE,
    #   posted_by TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # book & debate topic
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS book_topics (
    #   id SERIAL PRIMARY KEY,
    #   book_title TEXT,
    #   debate_topic TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # 추천 도구
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS recommendations (
    #   id SERIAL PRIMARY KEY,
    #   tool_name TEXT,
    #   description TEXT,
    #   url TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # word of the day
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS word_of_day (
    #   day DATE PRIMARY KEY,
    #   word TEXT,
    #   definition TEXT
    # );
    # """)

    # # class schedule
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS class_schedule (
    #   id SERIAL PRIMARY KEY,
    #   day_of_week TEXT,
    #   time_slot TEXT,
    #   subject TEXT
    # );
    # """)

    # # learning materials
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS materials (
    #   id SERIAL PRIMARY KEY,
    #   title TEXT,
    #   description TEXT,
    #   file_url TEXT,
    #   uploaded_by TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # essay uploads
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS essays (
    #   id SERIAL PRIMARY KEY,
    #   username TEXT,
    #   file_path TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)

    # # newbery books ratings
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS newbery_books (
    #   id SERIAL PRIMARY KEY,
    #   title TEXT,
    #   discussion_date DATE,
    #   rating INTEGER
    # );
    # """)

    # # debate articles
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS debate_articles (
    #   id SERIAL PRIMARY KEY,
    #   title TEXT,
    #   url TEXT,
    #   shared_by TEXT,
    #   timestamp TIMESTAMPTZ
    # );
    # """)
    
    return conn

conn = init_db()

# ---------------------------
# 2) 세션 상태 초기화
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username  = "게스트"
    st.session_state.role      = "학생"

# ---------------------------
# 3) 로그인 / 회원가입 사이드바
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
        choice = st.radio("옵션 선택", ["로그인","회원가입","게스트 로그인"], key="login_choice")
        if choice == "로그인":
            with st.form("login_form", clear_on_submit=True):
                user = st.text_input("아이디")
                pwd  = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    cur = conn.cursor()
                    # kicked?
                    cur.execute("SELECT reason FROM kicked_users WHERE username=%s", (user,))
                    if (row := cur.fetchone()):
                        st.error(f"🚫 강제 탈퇴됨: {row[0]}\n새 계정 생성이 필요합니다.")
                    else:
                        # special roles
                        if pwd == "teacherpw": role = "선생님"
                        elif pwd == "creatorpw": role = "제작자"
                        else: role = None
                        if role:
                            cur.execute("SELECT 1 FROM users WHERE username=%s", (user,))
                            if cur.fetchone():
                                st.session_state.logged_in = True
                                st.session_state.username  = user
                                st.session_state.role      = role
                                st.rerun()
                            else:
                                st.error("등록된 사용자가 아닙니다.")
                        else:
                            cur.execute(
                                "SELECT username,role FROM users WHERE username=%s AND password=%s",
                                (user, pwd)
                            )
                            if (row := cur.fetchone()):
                                st.session_state.logged_in = True
                                st.session_state.username  = row[0]
                                st.session_state.role      = row[1]
                                st.rerun()
                            else:
                                st.error("아이디 또는 비밀번호가 틀렸습니다.")
        elif choice == "회원가입":
            with st.form("reg_form", clear_on_submit=True):
                nu = st.text_input("아이디", key="reg_u")
                np = st.text_input("비밀번호", type="password", key="reg_p")
                if st.form_submit_button("회원가입"):
                    try:
                        cur = conn.cursor()
                        cur.execute(
                          "INSERT INTO users(username,password) VALUES(%s,%s)",
                          (nu, np)
                        )
                        st.success("회원가입 성공! 로그인해주세요.")
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
# 4) 사이드바 메뉴
# ---------------------------
st.sidebar.title("Honority 메뉴")
pages = [
    "홈","채팅 방","과제 공유","책/토론 주제","추천 도구",
    "오늘의 단어","수업 일정","학습 자료","에세이 업로드",
    "Newbery 북 평점","토론 기사","관리 페이지"
]
menu = st.sidebar.radio("페이지 선택", pages)

# ---------------------------
# 5) 헤더
# ---------------------------
st.image("assets/honority_logo.png", width=200)
st.title("🏅 Honority English Academy")

# ---------------------------
# 6) 각 페이지
# ---------------------------
# 홈
if menu=="홈":
    st.header("🏠 환영합니다, Honority에 오신 것을 환영해요!")
    st.write("여러분의 영어 학습을 돕기 위한 다양한 기능을 제공해요.")
    st.write("- 채팅 방에서 서로 소통하기")
    st.write("- 과제와 마감일 공유")
    st.write("- Newbery 토론 및 토론 기사 공유")
    if st.button("새로고침"):
        st.rerun()

# 채팅 방
elif menu=="채팅 방":
    st.header("💬 채팅 방")
    with st.form("chat_form", clear_on_submit=True):
        nick = st.text_input("닉네임")
        msg  = st.text_input("메시지")
        if st.form_submit_button("전송") and nick and msg:
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO chat_messages(nickname,message,timestamp) VALUES(%s,%s,%s)",
                (nick, msg, ts)
            )
            st.success("메시지 전송!")
            st.rerun()
    st.markdown("### 대화 내역")
    for nick, msg, ts in conn.cursor().execute(
        "SELECT nickname,message,timestamp FROM chat_messages ORDER BY id DESC"
    ).fetchall():
        st.write(f"[{ts:%H:%M}] **{nick}**: {msg}")

# 과제 공유
elif menu=="과제 공유":
    st.header("📚 과제 공유")
    with st.form("hw_form", clear_on_submit=True):
        assign = st.text_input("과제 내용")
        due    = st.date_input("마감일", date.today())
        if st.form_submit_button("등록") and assign:
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO homeworks(assignment,due_date,posted_by,timestamp) VALUES(%s,%s,%s,%s)",
                (assign, due, st.session_state.username, ts)
            )
            st.success("과제 등록 완료!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT assignment,due_date,posted_by FROM homeworks ORDER BY due_date"
    ).fetchall(), columns=["과제","마감일","등록자"])
    st.table(df)

# 책/토론 주제
elif menu=="책/토론 주제":
    st.header("📖 현재 책 & 토론 주제")
    with st.form("bt_form", clear_on_submit=True):
        book = st.text_input("책 제목")
        topic = st.text_input("토론 주제")
        if st.form_submit_button("등록") and book and topic:
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO book_topics(book_title,debate_topic,timestamp) VALUES(%s,%s,%s)",
                (book, topic, ts)
            )
            st.success("주제 등록 완료!")
            st.rerun()
    for b,t,ts in conn.cursor().execute(
        "SELECT book_title,debate_topic,timestamp FROM book_topics ORDER BY id DESC LIMIT 1"
    ).fetchall():
        st.markdown(f"**책:** {b}  \n**토론 주제:** {t}")

# 추천 도구
elif menu=="추천 도구":
    st.header("🔧 추천 도구")
    with st.form("rec_form", clear_on_submit=True):
        name = st.text_input("도구 이름")
        desc = st.text_area("설명")
        url  = st.text_input("URL")
        if st.form_submit_button("등록") and name:
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO recommendations(tool_name,description,url,timestamp) VALUES(%s,%s,%s,%s)",
                (name, desc, url, ts)
            )
            st.success("등록 완료!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT tool_name,description,url FROM recommendations ORDER BY id DESC"
    ).fetchall(), columns=["도구","설명","URL"])
    st.table(df)

# 오늘의 단어
elif menu=="오늘의 단어":
    st.header("📝 Word of the Day")
    today = date.today()
    with st.form("wotd_form", clear_on_submit=True):
        w = st.text_input("단어")
        d = st.text_area("정의")
        if st.form_submit_button("등록") and w:
            conn.cursor().execute(
                "INSERT INTO word_of_day(day,word,definition) VALUES(%s,%s,%s) ON CONFLICT(day) DO UPDATE SET word=EXCLUDED.word, definition=EXCLUDED.definition",
                (today, w, d)
            )
            st.success("오늘의 단어 설정 완료!")
            st.rerun()
    row = conn.cursor().execute(
        "SELECT word,definition FROM word_of_day WHERE day=%s", (today,)
    ).fetchone()
    if row:
        st.markdown(f"**{row[0]}**: {row[1]}")
    else:
        st.info("오늘의 단어가 없습니다.")

# 수업 일정
elif menu=="수업 일정":
    st.header("📆 수업 일정")
    days = ["월","화","수","목","금"]
    with st.form("sch_form", clear_on_submit=True):
        day  = st.selectbox("요일", days)
        time = st.text_input("시간대")
        subj = st.text_input("과목")
        if st.form_submit_button("추가") and time and subj:
            conn.cursor().execute(
                "INSERT INTO class_schedule(day_of_week,time_slot,subject) VALUES(%s,%s,%s)",
                (day, time, subj)
            )
            st.success("일정 추가!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT day_of_week,time_slot,subject FROM class_schedule ORDER BY id"
    ).fetchall(), columns=["요일","시간","과목"])
    st.table(df)

# 학습 자료
elif menu=="학습 자료":
    st.header("📂 학습 자료")
    with st.form("mat_form", clear_on_submit=True):
        title = st.text_input("제목")
        desc  = st.text_area("설명")
        file  = st.file_uploader("파일 업로드")
        if st.form_submit_button("등록") and title:
            fn = ""
            if file:
                os.makedirs("uploads_materials", exist_ok=True)
                fn = f"uploads_materials/{uuid.uuid4().hex}.{file.name.split('.')[-1]}"
                with open(fn,"wb") as f: f.write(file.getbuffer())
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO materials(title,description,file_url,uploaded_by,timestamp) VALUES(%s,%s,%s,%s,%s)",
                (title, desc, fn, st.session_state.username, ts)
            )
            st.success("등록 완료!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT title,description,file_url,uploaded_by FROM materials ORDER BY id DESC"
    ).fetchall(), columns=["제목","설명","파일","등록자"])
    st.table(df)

# 에세이 업로드
elif menu=="에세이 업로드":
    st.header("🖋️ 에세이 업로드")
    file = st.file_uploader("에세이를 파일로 업로드", type=["docx","pdf","txt"])
    if file:
        os.makedirs("uploads_essays", exist_ok=True)
        fn = f"uploads_essays/{uuid.uuid4().hex}.{file.name.split('.')[-1]}"
        with open(fn,"wb") as f: f.write(file.getbuffer())
        ts = datetime.now()
        conn.cursor().execute(
            "INSERT INTO essays(username,file_path,timestamp) VALUES(%s,%s,%s)",
            (st.session_state.username, fn, ts)
        )
        st.success("에세이 업로드 완료!")
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT username,file_path,timestamp FROM essays ORDER BY id DESC"
    ).fetchall(), columns=["작성자","파일","시간"])
    st.table(df)

# Newbery 북 평점
elif menu=="Newbery 북 평점":
    st.header("⭐ Newbery 북 평점")
    with st.form("nb_form", clear_on_submit=True):
        title = st.text_input("책 제목")
        date_ = st.date_input("논의일")
        rating = st.slider("평점", 1, 5, 3)
        if st.form_submit_button("등록") and title:
            conn.cursor().execute(
                "INSERT INTO newbery_books(title,discussion_date,rating) VALUES(%s,%s,%s)",
                (title, date_, rating)
            )
            st.success("평점 등록 완료!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT title,discussion_date,rating FROM newbery_books ORDER BY rating DESC"
    ).fetchall(), columns=["제목","논의일","평점"])
    st.table(df)

# 토론 기사
elif menu=="토론 기사":
    st.header("📰 토론 관련 유용 기사")
    with st.form("da_form", clear_on_submit=True):
        title = st.text_input("기사 제목")
        url   = st.text_input("URL")
        if st.form_submit_button("공유") and title and url:
            ts = datetime.now()
            conn.cursor().execute(
                "INSERT INTO debate_articles(title,url,shared_by,timestamp) VALUES(%s,%s,%s,%s)",
                (title, url, st.session_state.username, ts)
            )
            st.success("기사 공유 완료!")
            st.rerun()
    df = pd.DataFrame(conn.cursor().execute(
        "SELECT title,url,shared_by FROM debate_articles ORDER BY id DESC"
    ).fetchall(), columns=["제목","URL","공유자"])
    st.table(df)

# 관리 페이지
elif menu=="관리 페이지":
    st.header("🔧 선생님/제작자 전용 관리 페이지")
    if st.session_state.role not in ["선생님","제작자"]:
        st.error("권한이 없습니다.")
        st.stop()

    cur = conn.cursor()
    # 사용자 강제 탈퇴
    st.subheader("👤 사용자 관리")
    cur.execute("SELECT id,username,role FROM users ORDER BY id")
    for uid, un, ur in cur.fetchall():
        col1, col2, col3 = st.columns([0.5,0.2,0.3])
        col1.write(f"**{un}** (역할: {ur})")
        # 역할 변경
        roles = ["제작자","선생님","학생"]
        idx = roles.index(ur) if ur in roles else 2
        newr = col2.selectbox("", roles, index=idx, key=f"r_{uid}")
        if col2.button("변경", key=f"chg_{uid}"):
            conn.cursor().execute("UPDATE users SET role=%s WHERE id=%s",(newr,uid))
            st.success("역할 변경 완료!"); st.rerun()
        # 강제 탈퇴
        with col3.expander("킥하기"):
            reason = st.text_input("사유", key=f"k_{uid}")
            if st.button("강제 탈퇴", key=f"kick_{uid}"):
                conn.cursor().execute(
                    "INSERT INTO kicked_users(username,reason) VALUES(%s,%s) ON CONFLICT(username) DO UPDATE SET reason=EXCLUDED.reason,kicked_at=now()",
                    (un, reason)
                )
                conn.cursor().execute("DELETE FROM users WHERE id=%s",(uid,))
                st.success(f"{un} 강제 탈퇴: {reason}"); st.rerun()

    st.markdown("---")
    st.write("기타 관리 기능은 추후 추가 가능합니다.")
