import streamlit as st
import sqlite3
import random
from datetime import datetime
import pandas as pd

# ---------------------------
# 데이터베이스 초기화 함수 (추가 테이블 포함)
# ---------------------------
def init_db():
    conn = sqlite3.connect('honority.db', check_same_thread=False)
    c = conn.cursor()
    # 사용자 테이블: role 컬럼 추가 (제작자, 관리자, 헌재, 일반학생)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT '일반학생'
        )
    ''')
    # 미니 블로그 게시판
    c.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            timestamp TEXT,
            username TEXT
        )
    ''')
    # 숙제 공유함 게시판
    c.execute('''
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            due_date TEXT,
            timestamp TEXT,
            username TEXT
        )
    ''')
    # 채팅 메시지 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT,
            message TEXT,
            timestamp TEXT
        )
    ''')
    # Word of the Day 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS word_of_the_day (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            definition TEXT,
            example TEXT
        )
    ''')
    # 수업 일정 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_range TEXT,
            monday TEXT,
            tuesday TEXT,
            wednesday TEXT,
            thursday TEXT,
            friday TEXT
        )
    ''')
    # 학습 자료 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    
    # 기본 데이터 삽입 (없을 경우)
    c.execute("SELECT COUNT(*) FROM word_of_the_day")
    if c.fetchone()[0] == 0:
        default_words = [
            ("Eloquent", "Fluent or persuasive in speaking or writing.", "She delivered an eloquent speech."),
            ("Meticulous", "Showing great attention to detail; very careful and precise.", "He was meticulous in his work."),
            ("Innovative", "Featuring new methods; advanced and original.", "They developed an innovative solution."),
            ("Versatile", "Able to adapt or be adapted to many different functions or activities.", "A versatile musician plays multiple instruments."),
            ("Resilient", "Able to withstand or recover quickly from difficult conditions.", "The resilient community bounced back after the storm.")
        ]
        c.executemany("INSERT INTO word_of_the_day (word, definition, example) VALUES (?,?,?)", default_words)
    
    c.execute("SELECT COUNT(*) FROM class_schedule")
    if c.fetchone()[0] == 0:
        default_schedule = [
            ("09:00-10:00", "Grammar", "Vocabulary", "Speaking", "Listening", "Writing"),
            ("10:00-11:00", "Reading", "Debate", "Grammar", "Vocabulary", "Speaking"),
            ("11:00-12:00", "Writing", "Reading", "Listening", "Debate", "Grammar"),
            ("12:00-13:00", "Break", "Break", "Break", "Break", "Break"),
            ("13:00-14:00", "Speaking", "Writing", "Reading", "Listening", "Vocabulary")
        ]
        c.executemany("INSERT INTO class_schedule (time_range, monday, tuesday, wednesday, thursday, friday) VALUES (?,?,?,?,?,?)", default_schedule)
    
    c.execute("SELECT COUNT(*) FROM learning_resources")
    if c.fetchone()[0] == 0:
        default_resources = [
            ("BBC Learning English", "https://www.bbc.co.uk/learningenglish", "News, videos, and articles for learning English."),
            ("VOA Learning English", "https://learningenglish.voanews.com", "News stories and videos in slow-speed English."),
            ("ESL Gold", "https://www.eslgold.com", "Resources for speaking, writing, vocabulary, and grammar."),
            ("TED Talks", "https://www.ted.com/topics/learning+english", "Inspiring talks with subtitles to support learning.")
        ]
        c.executemany("INSERT INTO learning_resources (title, url, description) VALUES (?,?,?)", default_resources)
    conn.commit()
    return conn

conn = init_db()

# ---------------------------
# 세션 상태 초기화 (로그인/기타)
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = "게스트"
    st.session_state.role = "일반학생"  # 제작자, 관리자, 헌재, 일반학생

# ---------------------------
# 로그인 / 회원가입
# ---------------------------
with st.sidebar.expander("로그인 / 회원가입"):
    if st.session_state.logged_in:
        st.write(f"현재 **{st.session_state.username}** ({st.session_state.role})님 로그인 상태입니다.")
        st.info(f"안녕하세요, {st.session_state.username}님! 반가워요.")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.username = "게스트"
            st.session_state.role = "일반학생"
            st.success("로그아웃 되었습니다.")
    else:
        login_choice = st.radio("옵션 선택", ["로그인", "회원가입", "게스트 로그인"], key="login_choice")
        if login_choice == "로그인":
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("아이디")
                password = st.text_input("비밀번호", type="password")
                submitted = st.form_submit_button("로그인")
                if submitted:
                    c = conn.cursor()
                    # 특수 비밀번호에 따른 역할 인증
                    if password == "sqrtof4":  # 제작자 비번
                        c.execute("SELECT * FROM users WHERE username=?", (username,))
                        user = c.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = "제작자"
                            st.success(f"{username}님, 제작자 인증 완료!")
                        else:
                            st.error("등록된 사용자가 아닙니다.")
                    elif password == "3.141592":  # 관리자 비번
                        c.execute("SELECT * FROM users WHERE username=?", (username,))
                        user = c.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = "관리자"
                            st.success(f"{username}님, 관리자 인증 완료!")
                        else:
                            st.error("등록된 사용자가 아닙니다.")
                    elif password == "1.414":  # 헌재 비번
                        c.execute("SELECT * FROM users WHERE username=?", (username,))
                        user = c.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = "헌재"
                            st.success(f"{username}님, 헌재 인증 완료!")
                        else:
                            st.error("등록된 사용자가 아닙니다.")
                    else:
                        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                        user = c.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = user[3] if len(user) >= 4 else "일반학생"
                            st.success(f"{username}님, 환영합니다! (역할: {st.session_state.role})")
                        else:
                            st.error("아이디 또는 비밀번호가 틀렸습니다.")
        elif login_choice == "회원가입":
            with st.form("register_form", clear_on_submit=True):
                new_username = st.text_input("아이디 (회원가입)", key="reg_username")
                new_password = st.text_input("비밀번호 (회원가입)", type="password", key="reg_password")
                submitted = st.form_submit_button("회원가입")
                if submitted:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", 
                                  (new_username, new_password, "일반학생"))
                        conn.commit()
                        st.success("회원가입 성공! 이제 로그인 해주세요.")
                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 아이디입니다.")
        elif login_choice == "게스트 로그인":
            if st.button("게스트 모드로 로그인"):
                st.session_state.logged_in = True
                st.session_state.username = "게스트"
                st.session_state.role = "일반학생"
                st.success("게스트 모드로 로그인 되었습니다.")

# ---------------------------
# 사이드바 메뉴 선택
# ---------------------------
st.sidebar.title("메뉴 선택")
# 추가 기능: Word of the Day, 수업 일정, 학습 자료 등
menu = st.sidebar.radio("페이지 이동", 
                         ["홈", "채팅방", "미니 블로그", "우리 반 명단", "숙제 공유함", 
                          "추천 도구", "Word of the Day", "수업 일정", "학습 자료"])

# ---------------------------
# 공통 헤더
# ---------------------------
with st.container():
    st.image('assets/logo.jpg', width=250)
    st.title("H 아너리티 영어학원")
    st.markdown("""#### 안녕하세요? 아너리티 학원입니다.
왼쪽 탭에서 원하는 메뉴를 선택하세요.
(하단의 '새로고침' 버튼을 누르면 최신 내용이 반영됩니다.)""")

# ---------------------------
# 홈 페이지
# ---------------------------
if menu == "홈":
    st.header("🏠 홈")
    st.markdown("""
    **아너리티 영어학원** 웹사이트입니다.  
    이 웹사이트는 채팅, 소식(미니 블로그), 반 명단 등의 기능과 함께,
    숙제 공유, 추천 도구 및 영어 학습에 도움이 되는 다양한 기능들을 제공합니다.
    """)
    mood = st.selectbox("📆 오늘의 기분은?", ["😄 행복해!", "😎 멋져!", "😴 피곤해...", "🥳 신나!"])
    st.write(f"오늘의 기분: {mood}")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 채팅방 페이지 (데이터베이스 저장 방식)
# ---------------------------
elif menu == "채팅방":
    st.header("💬 채팅방")
    st.markdown("일반 채팅방입니다. 자유롭게 대화하세요.")
    with st.form("chat_form", clear_on_submit=True):
        nickname = st.text_input("닉네임", placeholder="닉네임")
        message = st.text_input("메시지", placeholder="내용")
        submitted = st.form_submit_button("전송")
        if submitted and nickname and message:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c = conn.cursor()
            c.execute("INSERT INTO chat_messages (nickname, message, timestamp) VALUES (?,?,?)", 
                      (nickname, message, now))
            conn.commit()
            st.success("전송 완료")
    st.markdown("### 대화 내역")
    c = conn.cursor()
    c.execute("SELECT nickname, message, timestamp FROM chat_messages ORDER BY id DESC")
    chat_rows = c.fetchall()
    if chat_rows:
        for nick, msg, timestamp in reversed(chat_rows):
            st.markdown(f"**[{timestamp}] {nick}**: {msg}")
    else:
        st.info("아직 대화 내용이 없습니다.")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 미니 블로그 페이지
# ---------------------------
elif menu == "미니 블로그":
    st.header("📘 미니 블로그")
    st.markdown("소식 및 공지사항을 등록할 수 있는 게시판입니다.")
    with st.form("blog_form", clear_on_submit=True):
        title = st.text_input("글 제목", placeholder="제목 입력")
        content = st.text_area("글 내용", placeholder="내용 입력")
        submitted = st.form_submit_button("게시하기")
        if submitted and title and content:
            now = datetime.now().strftime("%Y-%m-%d")
            c = conn.cursor()
            c.execute("INSERT INTO blog_posts (title, content, timestamp, username) VALUES (?,?,?,?)", 
                      (title, content, now, st.session_state.username))
            conn.commit()
            st.success("게시글 등록 완료")
    st.markdown("### 최신 게시글")
    c = conn.cursor()
    c.execute("SELECT id, title, content, timestamp, username FROM blog_posts ORDER BY id DESC")
    blog_data = c.fetchall()
    if blog_data:
        for row in blog_data:
            post_id, title, content, timestamp, author = row
            st.markdown(f"**[{post_id}] {title}** _(작성일: {timestamp}, 작성자: {author})_")
            st.write(content)
            if st.session_state.logged_in and st.session_state.role in ["제작자", "관리자", "헌재"]:
                if st.button(f"삭제 (ID {post_id})", key=f"delete_{post_id}"):
                    c.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
                    conn.commit()
                    st.success("게시글 삭제 완료")
            st.markdown("---")
    else:
        st.info("등록된 게시글이 없습니다.")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 우리 반 명단 페이지
# ---------------------------
elif menu == "우리 반 명단":
    st.header("👥 우리 반 명단")
    data = {
        "번호": [1, 2, 3, 4, 5, 6, 7, 8],
        "이름": ["Yani", "Lily", "Jia", "Sofia", "Violet", "Jayce", "Dylan", "Jiho"]
    }
    roster_df = pd.DataFrame(data)
    st.table(roster_df)
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 숙제 공유함 페이지
# ---------------------------
elif menu == "숙제 공유함":
    st.header("📝 숙제 공유함")
    st.markdown("오늘의 숙제 및 공지사항을 공유합니다.")
    c = conn.cursor()
    with st.form("homework_form", clear_on_submit=True):
        hw_title = st.text_input("숙제 제목", placeholder="숙제 제목 입력")
        hw_desc = st.text_area("설명", placeholder="숙제 내용 및 주의사항 입력")
        hw_due = st.text_input("마감일 (YYYY-MM-DD)", placeholder="예: 2025-05-01")
        submitted_hw = st.form_submit_button("숙제 등록")
        if submitted_hw and hw_title and hw_desc and hw_due:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO homework (title, description, due_date, timestamp, username) VALUES (?,?,?,?,?)",
                      (hw_title, hw_desc, hw_due, now, st.session_state.username))
            conn.commit()
            st.success("숙제 등록 완료")
    st.markdown("### 최신 숙제")
    c.execute("SELECT id, title, description, due_date, timestamp, username FROM homework ORDER BY id DESC")
    hw_data = c.fetchall()
    if hw_data:
        for hw in hw_data:
            hw_id, hw_title, hw_desc, due_date, ts, author = hw
            st.markdown(f"**[{hw_id}] {hw_title}** _(마감일: {due_date}, 등록일: {ts}, 등록자: {author})_")
            st.write(hw_desc)
            st.markdown("---")
    else:
        st.info("등록된 숙제가 없습니다.")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 추천 도구 페이지
# ---------------------------
elif menu == "추천 도구":
    st.header("🔧 추천 도구")
    st.markdown("학원 수업이나 개인 학습에 유용한 도구들을 소개합니다.")
    c = conn.cursor()
    c.execute("SELECT title, url, description FROM learning_resources")
    resources = c.fetchall()
    # 관리자 편집 모드
    if st.session_state.logged_in and st.session_state.role in ["제작자", "관리자"]:
        with st.expander("편집 모드: 학습 자료 관리"):
            with st.form("add_resource", clear_on_submit=True):
                res_title = st.text_input("도구 이름", placeholder="도구 이름 입력")
                res_url = st.text_input("도구 URL", placeholder="URL 입력")
                res_desc = st.text_area("도구 설명", placeholder="설명 입력")
                submitted_res = st.form_submit_button("추가")
                if submitted_res and res_title and res_url and res_desc:
                    c.execute("INSERT INTO learning_resources (title, url, description) VALUES (?,?,?)",
                              (res_title, res_url, res_desc))
                    conn.commit()
                    st.success("학습 자료 추가됨")
            st.markdown("### 현재 학습 자료")
            c.execute("SELECT id, title FROM learning_resources")
            for res in c.fetchall():
                res_id, res_title = res
                if st.button(f"삭제 (ID {res_id})", key=f"del_res_{res_id}"):
                    c.execute("DELETE FROM learning_resources WHERE id=?", (res_id,))
                    conn.commit()
                    st.success("삭제됨")
                    st.rerun()
    # Display resources
    if resources:
        for title, url, desc in resources:
            st.markdown(f"### [{title}]({url})")
            st.write(desc)
            st.markdown("---")
    else:
        st.info("등록된 학습 자료가 없습니다.")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# Word of the Day 페이지
# ---------------------------
elif menu == "Word of the Day":
    st.header("📚 Word of the Day")
    c = conn.cursor()
    # 관리자 편집 모드
    if st.session_state.logged_in and st.session_state.role in ["제작자", "관리자"]:
        with st.expander("편집 모드: 단어 추가/삭제"):
            with st.form("add_word", clear_on_submit=True):
                new_word = st.text_input("단어")
                new_def = st.text_input("정의")
                new_ex = st.text_input("예문")
                submitted_word = st.form_submit_button("추가")
                if submitted_word and new_word and new_def and new_ex:
                    c.execute("INSERT INTO word_of_the_day (word, definition, example) VALUES (?,?,?)",
                              (new_word, new_def, new_ex))
                    conn.commit()
                    st.success("단어 추가됨")
                    st.rerun()
            st.markdown("### 현재 단어 목록")
            c.execute("SELECT id, word FROM word_of_the_day")
            for row in c.fetchall():
                word_id, word = row
                if st.button(f"삭제 (ID {word_id}: {word})", key=f"del_word_{word_id}"):
                    c.execute("DELETE FROM word_of_the_day WHERE id=?", (word_id,))
                    conn.commit()
                    st.success("삭제됨")
                    st.rerun()
    # 일반 사용자: display a random word
    c.execute("SELECT word, definition, example FROM word_of_the_day")
    all_words = c.fetchall()
    if all_words:
        selected = random.choice(all_words)
        st.markdown(f"### **{selected[0]}**")
        st.write(f"**Definition:** {selected[1]}")
        st.write(f"**Example:** {selected[2]}")
    else:
        st.info("단어가 등록되어 있지 않습니다.")
    if st.button("새로운 단어 보기"):
        st.rerun()

# ---------------------------
# 수업 일정 페이지
# ---------------------------
elif menu == "수업 일정":
    st.header("📅 Class Schedule")
    c = conn.cursor()
    # 관리자 편집 모드
    if st.session_state.logged_in and st.session_state.role in ["제작자", "관리자"]:
        with st.expander("편집 모드: 수업 일정 추가/삭제"):
            with st.form("add_schedule", clear_on_submit=True):
                time_range = st.text_input("시간대", placeholder="예: 14:00-15:00")
                mon = st.text_input("월요일 과목")
                tue = st.text_input("화요일 과목")
                wed = st.text_input("수요일 과목")
                thu = st.text_input("목요일 과목")
                fri = st.text_input("금요일 과목")
                submitted_sched = st.form_submit_button("추가")
                if submitted_sched and time_range and mon and tue and wed and thu and fri:
                    c.execute("INSERT INTO class_schedule (time_range, monday, tuesday, wednesday, thursday, friday) VALUES (?,?,?,?,?,?)",
                              (time_range, mon, tue, wed, thu, fri))
                    conn.commit()
                    st.success("수업 일정 추가됨")
                    st.rerun()
            st.markdown("### 현재 수업 일정")
            c.execute("SELECT id, time_range FROM class_schedule")
            for row in c.fetchall():
                sched_id, time_range = row
                if st.button(f"삭제 (ID {sched_id}: {time_range})", key=f"del_sched_{sched_id}"):
                    c.execute("DELETE FROM class_schedule WHERE id=?", (sched_id,))
                    conn.commit()
                    st.success("삭제됨")
                    st.rerun()
    # Display schedule as table
    c.execute("SELECT time_range, monday, tuesday, wednesday, thursday, friday FROM class_schedule ORDER BY id ASC")
    schedule_rows = c.fetchall()
    if schedule_rows:
        schedule_df = pd.DataFrame(schedule_rows, columns=["시간", "월요일", "화요일", "수요일", "목요일", "금요일"])
        st.dataframe(schedule_df)
    else:
        st.info("수업 일정이 등록되어 있지 않습니다.")

# ---------------------------
# 학습 자료 페이지
# ---------------------------
elif menu == "학습 자료":
    st.header("📚 학습 자료")
    c = conn.cursor()
    # 관리자 편집 모드 is integrated in 추천 도구 page above,
    # but you can add additional editing here if desired.
    c.execute("SELECT title, url, description FROM learning_resources")
    resources = c.fetchall()
    if resources:
        for title, url, desc in resources:
            st.markdown(f"### [{title}]({url})")
            st.write(desc)
            st.markdown("---")
    else:
        st.info("등록된 학습 자료가 없습니다.")
    if st.button("새로고침"):
        st.rerun()

# ---------------------------
# 하단 제작자 표시
# ---------------------------
st.markdown("***-Made By 양지호-***")
