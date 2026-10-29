import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from io import StringIO

# ============================================================
# HR Insight | 데이터 기반 스마트 인사 관리 시스템
# GitHub + Streamlit Cloud용 단일 파일: main.py
# ============================================================

st.set_page_config(
    page_title="HR Insight | 스마트 인사 관리",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- 스타일 ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #101d36; }
    [data-testid="stSidebar"] * { color: #f4f7ff !important; }
    .hero {
        background: linear-gradient(120deg, #142747 0%, #2458a6 100%);
        padding: 28px 30px; border-radius: 18px; color: white;
        margin-bottom: 22px; box-shadow: 0 8px 24px rgba(25,55,100,.13);
    }
    .hero h1 { color: white; margin: 0 0 8px 0; font-size: 2.05rem; }
    .hero p { color: #e2ebff; margin: 0; font-size: 1rem; }
    .section-title { font-size: 1.2rem; font-weight: 800; color: #152744; margin: 8px 0 12px; }
    .small-note { color: #64748b; font-size: .88rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e6ebf3; padding: 15px 17px;
        border-radius: 14px; box-shadow: 0 3px 10px rgba(25,45,80,.035);
    }
    div[data-testid="stMetricLabel"] { color: #64748b; }
    div[data-testid="stMetricValue"] { color: #18365f; }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 10px; font-weight: 700; min-height: 2.6rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: white; border-radius: 9px 9px 0 0; padding: 10px 16px; }
    .footer { text-align:center; color:#8490a4; padding:24px 0 8px; font-size:.82rem; }
</style>
""", unsafe_allow_html=True)

DEPARTMENTS = ["경영지원", "개발", "마케팅", "영업", "인사", "디자인", "고객지원"]
POSITIONS = ["사원", "주임", "대리", "과장", "차장", "부장"]
EMPLOYEE_COLUMNS = ["사번", "이름", "부서", "직급", "입사일", "고용형태", "이메일", "상태"]
ATTENDANCE_COLUMNS = ["날짜", "사번", "이름", "부서", "상태", "근무시간"]

def sample_employees():
    names = [
        "김민준","이서연","박지호","최하은","정도윤","강유진","조현우","윤서아","장우진","임지우",
        "한도현","오지민","서준호","신예린","권민재","황수빈","안시우","송채원","전지훈","홍다은",
        "문태윤","양서윤","배준서","백예원","허지안","남도현","심하린","노유찬","유나연","차은우"
    ]
    departments = ["개발","개발","마케팅","영업","경영지원","인사","디자인","고객지원","영업","개발",
                   "마케팅","고객지원","개발","디자인","영업","경영지원","인사","마케팅","개발","고객지원",
                   "영업","디자인","개발","마케팅","인사","경영지원","고객지원","개발","영업","디자인"]
    rows = []
    today = date.today()
    for i, name in enumerate(names, start=1):
        hire = today - timedelta(days=180 + ((i * 137) % 2200))
        rows.append({
            "사번": f"HR{i:03d}", "이름": name, "부서": departments[i-1],
            "직급": POSITIONS[(i * 3 + i // 4) % len(POSITIONS)],
            "입사일": hire.isoformat(),
            "고용형태": "정규직" if i % 7 else "계약직",
            "이메일": f"employee{i:02d}@example.com",
            "상태": "재직" if i not in (8, 21) else "퇴사",
        })
    return pd.DataFrame(rows, columns=EMPLOYEE_COLUMNS)

def sample_attendance(employees):
    rng_rows = []
    today = date.today()
    active = employees[employees["상태"] == "재직"]
    for back in range(29, -1, -1):
        d = today - timedelta(days=back)
        if d.weekday() >= 5:
            continue
        for idx, emp in active.reset_index(drop=True).iterrows():
            # Deterministic sample variation, not real employee information.
            n = idx + back
            status = "출근"
            if n % 23 == 0:
                status = "지각"
            elif n % 61 == 0:
                status = "결근"
            hours = 0.0 if status == "결근" else (7.5 if status == "지각" else 8.0)
            rng_rows.append({
                "날짜": d.isoformat(), "사번": emp["사번"], "이름": emp["이름"],
                "부서": emp["부서"], "상태": status, "근무시간": hours
            })
    return pd.DataFrame(rng_rows, columns=ATTENDANCE_COLUMNS)

def normalize_employees(df):
    df = df.copy()
    for col in EMPLOYEE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[EMPLOYEE_COLUMNS]
    df["사번"] = df["사번"].astype(str).str.strip()
    df["이름"] = df["이름"].astype(str).str.strip()
    df["부서"] = df["부서"].astype(str).str.strip()
    df["직급"] = df["직급"].astype(str).str.strip()
    df["입사일"] = pd.to_datetime(df["입사일"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df["고용형태"] = df["고용형태"].astype(str).str.strip()
    df["이메일"] = df["이메일"].astype(str).str.strip()
    df["상태"] = df["상태"].astype(str).str.strip()
    return df

def normalize_attendance(df, employees):
    df = df.copy()
    for col in ATTENDANCE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[ATTENDANCE_COLUMNS]
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df["사번"] = df["사번"].astype(str).str.strip()
    emp_map = employees.set_index("사번").to_dict("index") if not employees.empty else {}
    for i, row in df.iterrows():
        emp = emp_map.get(row["사번"])
        if emp:
            df.at[i, "이름"] = emp["이름"]
            df.at[i, "부서"] = emp["부서"]
    df["근무시간"] = pd.to_numeric(df["근무시간"], errors="coerce").fillna(0).clip(0, 24)
    return df

if "employees" not in st.session_state:
    st.session_state.employees = sample_employees()
if "attendance" not in st.session_state:
    st.session_state.attendance = sample_attendance(st.session_state.employees)
if "notice" not in st.session_state:
    st.session_state.notice = ""

employees = st.session_state.employees
attendance = st.session_state.attendance

# ---------- 사이드바 ----------
with st.sidebar:
    st.markdown("## 🏢 HR Insight")
    st.caption("DATA-DRIVEN HR MANAGEMENT")
    st.markdown("---")
    page = st.radio(
        "메뉴",
        ["대시보드", "직원 관리", "근태 관리", "인사 분석", "인력 배치 시뮬레이션", "데이터 관리"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("### 📌 안내")
    st.caption("현재 표시되는 초기 직원 및 근태 기록은 프로그램 시연을 위한 가상 데이터입니다.")
    st.caption("실제 개인정보를 입력하지 마세요.")
    st.markdown("---")
    st.caption("HR Insight · Python + Streamlit")

# ---------- 헤더 ----------
st.markdown("""
<div class="hero">
  <h1>HR Insight</h1>
  <p>데이터로 이해하고, 근거를 바탕으로 더 나은 인력 운영을 설계하세요.</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.notice:
    st.info(st.session_state.notice)
    st.session_state.notice = ""

employees = st.session_state.employees
attendance = st.session_state.attendance
active_employees = employees[employees["상태"] == "재직"] if not employees.empty else employees

def show_kpis():
    total = len(employees)
    active = int((employees["상태"] == "재직").sum()) if total else 0
    dept_count = int(employees.loc[employees["상태"] == "재직", "부서"].nunique()) if total else 0
    month_start = date.today().replace(day=1).isoformat()
    month_att = attendance[attendance["날짜"] >= month_start] if not attendance.empty else attendance
    present = int(month_att["상태"].isin(["출근", "지각"]).sum()) if not month_att.empty else 0
    absent = int((month_att["상태"] == "결근").sum()) if not month_att.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 직원", f"{total:,}명")
    c2.metric("현재 재직", f"{active:,}명", delta=f"{(active/total*100):.1f}% 재직 비율" if total else None)
    c3.metric("운영 부서", f"{dept_count:,}개")
    c4.metric("이번 달 결근 기록", f"{absent:,}건", delta=f"출근·지각 {present}건")

# ---------- 대시보드 ----------
if page == "대시보드":
    show_kpis()
    st.markdown('<div class="section-title">📊 조직 현황 한눈에 보기</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("부서별 재직 인원")
        dept = active_employees.groupby("부서").size().reset_index(name="인원") if not active_employees.empty else pd.DataFrame(columns=["부서","인원"])
        if not dept.empty:
            fig = px.bar(dept.sort_values("인원", ascending=True), x="인원", y="부서", orientation="h",
                         text="인원", color="인원", color_continuous_scale=["#b8d5ff", "#2458a6"])
            fig.update_layout(height=330, margin=dict(l=5,r=5,t=10,b=5), coloraxis_showscale=False,
                              plot_bgcolor="white", paper_bgcolor="white", xaxis_title="직원 수", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("표시할 재직 직원 데이터가 없습니다.")
    with right:
        st.subheader("직급 구성")
        ranks = active_employees["직급"].value_counts().reindex(POSITIONS, fill_value=0).reset_index()
        ranks.columns = ["직급", "인원"]
        ranks = ranks[ranks["인원"] > 0]
        if not ranks.empty:
            fig = px.pie(ranks, names="직급", values="인원", hole=.55,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(height=330, margin=dict(l=5,r=5,t=10,b=5), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("표시할 데이터가 없습니다.")
    st.markdown('<div class="section-title">🕒 최근 근태 기록</div>', unsafe_allow_html=True)
    if not attendance.empty:
        recent = attendance.sort_values("날짜", ascending=False).head(10)
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("근태 기록이 없습니다.")
    st.caption("※ 초기 데이터는 기능 시연용 가상 데이터이며 실제 기업 통계가 아닙니다.")

# ---------- 직원 관리 ----------
elif page == "직원 관리":
    st.markdown('<div class="section-title">👥 직원 정보 관리</div>', unsafe_allow_html=True)
    st.write("직원 정보를 등록하고 검색하거나, 기존 정보를 수정·삭제할 수 있습니다.")
    with st.expander("➕ 새 직원 등록", expanded=False):
        with st.form("add_employee_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            emp_id = c1.text_input("사번", placeholder="예: HR031")
            emp_name = c2.text_input("이름")
            emp_dept = c3.selectbox("부서", DEPARTMENTS)
            c4, c5, c6 = st.columns(3)
            emp_pos = c4.selectbox("직급", POSITIONS)
            emp_hire = c5.date_input("입사일", value=date.today())
            emp_type = c6.selectbox("고용형태", ["정규직", "계약직", "인턴", "시간제"])
            emp_email = st.text_input("이메일 (선택)", placeholder="example@company.com")
            submitted = st.form_submit_button("직원 등록", type="primary", use_container_width=True)
            if submitted:
                current = st.session_state.employees
                emp_id = emp_id.strip().upper()
                if not emp_id or not emp_name.strip():
                    st.error("사번과 이름은 필수 입력 항목입니다.")
                elif emp_id in current["사번"].astype(str).values:
                    st.error("이미 존재하는 사번입니다. 사번을 확인해 주세요.")
                elif "@" in emp_email and "." not in emp_email.split("@")[-1]:
                    st.error("이메일 형식을 확인해 주세요.")
                else:
                    new = pd.DataFrame([{
                        "사번": emp_id, "이름": emp_name.strip(), "부서": emp_dept, "직급": emp_pos,
                        "입사일": emp_hire.isoformat(), "고용형태": emp_type, "이메일": emp_email.strip(), "상태": "재직"
                    }])
                    st.session_state.employees = pd.concat([current, new], ignore_index=True)
                    st.session_state.notice = f"{emp_name.strip()} 직원이 등록되었습니다."
                    st.rerun()

    employees = st.session_state.employees
    f1, f2, f3 = st.columns([1.5, 1, 1])
    search = f1.text_input("🔎 직원 검색", placeholder="이름 또는 사번 입력")
    dept_filter = f2.selectbox("부서 필터", ["전체"] + DEPARTMENTS)
    status_filter = f3.selectbox("상태 필터", ["전체", "재직", "퇴사"])
    filtered = employees.copy()
    if search:
        filtered = filtered[filtered["이름"].str.contains(search, case=False, na=False) | filtered["사번"].str.contains(search, case=False, na=False)]
    if dept_filter != "전체":
        filtered = filtered[filtered["부서"] == dept_filter]
    if status_filter != "전체":
        filtered = filtered[filtered["상태"] == status_filter]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(f"검색 결과: {len(filtered)}명")
    st.markdown("#### 선택 직원 정보 수정 또는 삭제")
    if not employees.empty:
        selected_id = st.selectbox("직원 선택", employees["사번"].tolist(), format_func=lambda x: f"{x} · {employees.loc[employees['사번']==x, '이름'].iloc[0]}")
        selected = employees[employees["사번"] == selected_id].iloc[0]
        with st.form("edit_employee_form"):
            c1, c2, c3 = st.columns(3)
            edit_name = c1.text_input("이름 수정", value=str(selected["이름"]))
            edit_dept = c2.selectbox("부서 수정", DEPARTMENTS, index=DEPARTMENTS.index(selected["부서"]) if selected["부서"] in DEPARTMENTS else 0)
            edit_pos = c3.selectbox("직급 수정", POSITIONS, index=POSITIONS.index(selected["직급"]) if selected["직급"] in POSITIONS else 0)
            c4, c5, c6 = st.columns(3)
            parsed_hire = pd.to_datetime(selected["입사일"], errors="coerce")
            default_hire = parsed_hire.date() if pd.notna(parsed_hire) else date.today()
            edit_hire = c4.date_input("입사일 수정", value=default_hire)
            type_options = ["정규직", "계약직", "인턴", "시간제"]
            current_type = selected["고용형태"] if selected["고용형태"] in type_options else type_options[0]
            edit_type = c5.selectbox("고용형태 수정", type_options, index=type_options.index(current_type))
            status_options = ["재직", "퇴사"]
            current_status = selected["상태"] if selected["상태"] in status_options else "재직"
            edit_status = c6.selectbox("상태 수정", status_options, index=status_options.index(current_status))
            edit_email = st.text_input("이메일 수정", value=str(selected["이메일"]))
            save_edit = st.form_submit_button("변경 사항 저장", type="primary")
            if save_edit:
                if not edit_name.strip():
                    st.error("이름은 비워둘 수 없습니다.")
                else:
                    idx = st.session_state.employees.index[st.session_state.employees["사번"] == selected_id][0]
                    st.session_state.employees.loc[idx, ["이름","부서","직급","입사일","고용형태","이메일","상태"]] = [
                        edit_name.strip(), edit_dept, edit_pos, edit_hire.isoformat(), edit_type, edit_email.strip(), edit_status
                    ]
                    st.session_state.attendance = normalize_attendance(st.session_state.attendance, st.session_state.employees)
                    st.session_state.notice = f"{selected_id} 직원 정보가 수정되었습니다."
                    st.rerun()
        confirm_delete = st.checkbox(f"{selected_id} 직원 삭제 확인")
        if st.button("🗑️ 선택 직원 삭제", type="secondary"):
            if confirm_delete:
                st.session_state.employees = st.session_state.employees[st.session_state.employees["사번"] != selected_id].reset_index(drop=True)
                st.session_state.attendance = st.session_state.attendance[st.session_state.attendance["사번"] != selected_id].reset_index(drop=True)
                st.session_state.notice = f"{selected_id} 직원과 관련 근태 기록이 삭제되었습니다."
                st.rerun()
            else:
                st.warning("삭제하려면 먼저 확인란을 선택해 주세요.")

# ---------- 근태 관리 ----------
elif page == "근태 관리":
    st.markdown('<div class="section-title">🗓️ 출퇴근 및 근태 관리</div>', unsafe_allow_html=True)
    employees = st.session_state.employees
    attendance = st.session_state.attendance
    active = employees[employees["상태"] == "재직"]
    if active.empty:
        st.warning("재직 중인 직원이 없습니다. 먼저 직원 관리에서 직원을 등록해 주세요.")
    else:
        with st.expander("➕ 근태 기록 추가", expanded=True):
            with st.form("attendance_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                work_date = c1.date_input("근무 날짜", value=date.today())
                emp_choice = c2.selectbox("직원", active["사번"].tolist(),
                    format_func=lambda x: f"{x} · {active.loc[active['사번']==x, '이름'].iloc[0]}")
                status = c3.selectbox("근태 상태", ["출근", "지각", "결근", "휴가"])
                hours = st.number_input("근무 시간", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
                add_att = st.form_submit_button("근태 기록 저장", type="primary", use_container_width=True)
                if add_att:
                    existing = st.session_state.attendance
                    same = existing[(existing["날짜"] == work_date.isoformat()) & (existing["사번"] == emp_choice)]
                    if not same.empty:
                        st.error("해당 직원의 날짜별 근태 기록이 이미 있습니다. 기존 기록을 확인해 주세요.")
                    else:
                        emp = active[active["사번"] == emp_choice].iloc[0]
                        new = pd.DataFrame([{
                            "날짜": work_date.isoformat(), "사번": emp_choice, "이름": emp["이름"],
                            "부서": emp["부서"], "상태": status,
                            "근무시간": 0.0 if status in ["결근", "휴가"] else hours
                        }])
                        st.session_state.attendance = pd.concat([existing, new], ignore_index=True)
                        st.session_state.notice = f"{emp['이름']} 직원의 근태 기록이 저장되었습니다."
                        st.rerun()
    attendance = st.session_state.attendance
    if not attendance.empty:
        c1, c2 = st.columns(2)
        date_from = c1.date_input("조회 시작일", value=date.today().replace(day=1), key="att_from")
        date_to = c2.date_input("조회 종료일", value=date.today(), key="att_to")
        if date_from > date_to:
            st.warning("조회 시작일은 종료일보다 늦을 수 없습니다.")
        else:
            view = attendance[(attendance["날짜"] >= date_from.isoformat()) & (attendance["날짜"] <= date_to.isoformat())].copy()
            st.markdown("#### 조회 기간 요약")
            a, b, c, d = st.columns(4)
            a.metric("전체 기록", f"{len(view):,}건")
            b.metric("출근", f"{int((view['상태']=='출근').sum()):,}건")
            c.metric("지각", f"{int((view['상태']=='지각').sum()):,}건")
            d.metric("결근", f"{int((view['상태']=='결근').sum()):,}건")
            st.dataframe(view.sort_values("날짜", ascending=False), use_container_width=True, hide_index=True)
            st.markdown("#### 근태 기록 삭제")
            if not view.empty:
                record_index = st.selectbox("삭제할 기록 선택", view.index.tolist(),
                    format_func=lambda i: f"{view.loc[i, '날짜']} · {view.loc[i, '이름']} · {view.loc[i, '상태']}")
                if st.button("선택한 근태 기록 삭제"):
                    st.session_state.attendance = st.session_state.attendance.drop(index=record_index).reset_index(drop=True)
                    st.session_state.notice = "근태 기록이 삭제되었습니다."
                    st.rerun()
    else:
        st.info("근태 기록이 없습니다.")

# ---------- 인사 분석 ----------
elif page == "인사 분석":
    st.markdown('<div class="section-title">📈 인사 데이터 분석</div>', unsafe_allow_html=True)
    employees = st.session_state.employees
    attendance = st.session_state.attendance
    active = employees[employees["상태"] == "재직"].copy()
    if employees.empty:
        st.info("분석할 직원 데이터가 없습니다.")
    else:
        hire_dates = pd.to_datetime(active["입사일"], errors="coerce")
        today_ts = pd.Timestamp(date.today())
        tenure = ((today_ts - hire_dates).dt.days / 365.25).dropna()
        avg_tenure = tenure.mean() if not tenure.empty else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("재직 인원", f"{len(active)}명")
        c2.metric("평균 근속 기간", f"{avg_tenure:.1f}년")
        c3.metric("부서 수", f"{active['부서'].nunique()}개")
        c4.metric("퇴사 인원", f"{int((employees['상태']=='퇴사').sum())}명")
        left, right = st.columns(2)
        with left:
            st.subheader("부서별 인원 및 직급 구성")
            dept_rank = active.groupby(["부서","직급"]).size().reset_index(name="인원")
            if not dept_rank.empty:
                fig = px.bar(dept_rank, x="부서", y="인원", color="직급", barmode="stack",
                             category_orders={"직급": POSITIONS})
                fig.update_layout(height=380, margin=dict(l=5,r=5,t=15,b=5), plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
        with right:
            st.subheader("입사 월별 추세")
            hire = pd.to_datetime(employees["입사일"], errors="coerce").dropna()
            if not hire.empty:
                hire_counts = hire.dt.to_period("M").astype(str).value_counts().sort_index().tail(12).reset_index()
                hire_counts.columns = ["월", "입사 인원"]
                fig = px.line(hire_counts, x="월", y="입사 인원", markers=True)
                fig.update_layout(height=380, margin=dict(l=5,r=5,t=15,b=5), plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
        st.subheader("부서별 근태 지표")
        if not attendance.empty:
            att = attendance.copy()
            att["날짜_dt"] = pd.to_datetime(att["날짜"], errors="coerce")
            cutoff = pd.Timestamp(date.today() - timedelta(days=89))
            att = att[att["날짜_dt"] >= cutoff]
            if not att.empty:
                summary = att.groupby("부서").agg(
                    기록수=("상태","size"),
                    출근=("상태", lambda x: int((x=="출근").sum())),
                    지각=("상태", lambda x: int((x=="지각").sum())),
                    결근=("상태", lambda x: int((x=="결근").sum())),
                    평균근무시간=("근무시간","mean")
                ).reset_index()
                summary["출근·지각 비율(%)"] = ((summary["출근"] + summary["지각"]) / summary["기록수"] * 100).round(1)
                summary["지각 비율(%)"] = (summary["지각"] / summary["기록수"] * 100).round(1)
                st.dataframe(summary, use_container_width=True, hide_index=True)
                fig = px.bar(summary, x="부서", y="지각 비율(%)", color="지각 비율(%)",
                             color_continuous_scale=["#c7e5d7", "#e8a09b"])
                fig.update_layout(height=300, margin=dict(l=5,r=5,t=10,b=5), coloraxis_showscale=False, plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("최근 90일 이내 근태 기록이 없습니다.")
        else:
            st.info("근태 기록을 추가하면 부서별 근태 분석을 볼 수 있습니다.")
        st.caption("해석 시 유의: 근태 지표만으로 직원의 성과나 성실성을 단정하지 마세요. 부서별 업무 특성과 기록량을 함께 고려해야 합니다.")

# ---------- 인력 배치 시뮬레이션 ----------
elif page == "인력 배치 시뮬레이션":
    st.markdown('<div class="section-title">🧭 인력 배치 시뮬레이션</div>', unsafe_allow_html=True)
    st.write("부서별 업무량과 인원수를 가정해 현재 배치와 변경 시나리오를 비교합니다. 실제 인사 결정이 아닌 의사결정 보조용 분석입니다.")
    active = st.session_state.employees[st.session_state.employees["상태"] == "재직"]
    base = active.groupby("부서").size().reindex(DEPARTMENTS, fill_value=0).reset_index()
    base.columns = ["부서", "현재 인원"]
    if "workload" not in st.session_state:
        st.session_state.workload = {d: max(10, int(base.loc[base["부서"]==d, "현재 인원"].iloc[0] * 24)) for d in DEPARTMENTS}
    with st.form("simulation_form"):
        st.markdown("#### 부서별 업무량 및 배치 인원 설정")
        st.caption("업무량은 시뮬레이션용 상대 지수(단위 없음)입니다. 실제 측정값이 아니라면 결과도 가정에 기반합니다.")
        cols = st.columns(2)
        workload_new = {}
        staff_new = {}
        for i, d in enumerate(DEPARTMENTS):
            with cols[i % 2]:
                st.markdown(f"**{d}**")
                workload_new[d] = st.number_input(f"{d} 업무량 지수", min_value=0, max_value=10000,
                    value=int(st.session_state.workload.get(d, 20)), step=5, key=f"work_{d}")
                default_staff = int(base.loc[base["부서"]==d, "현재 인원"].iloc[0])
                staff_new[d] = st.number_input(f"{d} 시뮬레이션 인원", min_value=0, max_value=500,
                    value=default_staff, step=1, key=f"staff_{d}")
        submitted_sim = st.form_submit_button("시뮬레이션 실행", type="primary", use_container_width=True)
        if submitted_sim:
            st.session_state.workload = workload_new
            st.session_state.staff_scenario = staff_new
            st.session_state.sim_ran = True
    if "sim_ran" not in st.session_state:
        st.session_state.sim_ran = False
    if st.session_state.sim_ran:
        rows = []
        for d in DEPARTMENTS:
            current_n = int(base.loc[base["부서"]==d, "현재 인원"].iloc[0])
            new_n = int(st.session_state.staff_scenario[d])
            work = int(st.session_state.workload[d])
            rows.append({
                "부서": d, "현재 인원": current_n, "시나리오 인원": new_n, "업무량 지수": work,
                "현재 1인당 업무량": round(work/current_n, 2) if current_n else None,
                "시나리오 1인당 업무량": round(work/new_n, 2) if new_n else None,
                "인원 변화": new_n-current_n
            })
        sim = pd.DataFrame(rows)
        st.markdown("#### 시나리오 결과")
        a,b,c = st.columns(3)
        a.metric("현재 총 인원", f"{int(sim['현재 인원'].sum())}명")
        b.metric("시나리오 총 인원", f"{int(sim['시나리오 인원'].sum())}명",
                 delta=f"{int(sim['시나리오 인원'].sum()-sim['현재 인원'].sum()):+d}명")
        zero_staff = sim[(sim["시나리오 인원"] == 0) & (sim["업무량 지수"] > 0)]
        c.metric("인력 공백 위험 부서", f"{len(zero_staff)}개")
        st.dataframe(sim, use_container_width=True, hide_index=True)
        chart_data = sim.melt(id_vars="부서", value_vars=["현재 1인당 업무량","시나리오 1인당 업무량"],
                              var_name="구분", value_name="업무량")
        fig = px.bar(chart_data, x="부서", y="업무량", color="구분", barmode="group",
                     color_discrete_sequence=["#9bb8e8","#2458a6"], title="부서별 1인당 업무량 비교")
        fig.update_layout(height=400, plot_bgcolor="white", margin=dict(l=5,r=5,t=45,b=5))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### 자동 분석 요약")
        positive = sim[(sim["인원 변화"] > 0) & (sim["시나리오 인원"] > 0)].sort_values("인원 변화", ascending=False)
        negative = sim[sim["인원 변화"] < 0].sort_values("인원 변화")
        if not zero_staff.empty:
            st.warning("업무량은 0보다 크지만 시나리오 인원이 0명인 부서가 있습니다: " + ", ".join(zero_staff["부서"].tolist()))
        if not positive.empty:
            st.write("• 인원이 증가한 부서: " + ", ".join([f"{r['부서']} (+{r['인원 변화']}명)" for _,r in positive.iterrows()]))
        if not negative.empty:
            st.write("• 인원이 감소한 부서: " + ", ".join([f"{r['부서']} ({r['인원 변화']}명)" for _,r in negative.iterrows()]))
        valid = sim[sim["시나리오 1인당 업무량"].notna()]
        if not valid.empty:
            max_row = valid.loc[valid["시나리오 1인당 업무량"].idxmax()]
            st.write(f"• 시나리오에서 1인당 업무량 지수가 가장 높은 부서는 **{max_row['부서']}**입니다 ({max_row['시나리오 1인당 업무량']:.2f}).")
        st.info("해석 기준: 1인당 업무량 지수는 입력한 가정에 따라 달라집니다. 업무 난이도, 숙련도, 근무 형태 등은 반영하지 않으므로 이 결과만으로 실제 인사 배치를 결정하면 안 됩니다.")
        csv = sim.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 시뮬레이션 결과 CSV 다운로드", data=csv, file_name="hr_staffing_simulation.csv", mime="text/csv")
    else:
        st.info("업무량과 시나리오 인원을 입력한 뒤 ‘시뮬레이션 실행’을 눌러 결과를 확인하세요.")

# ---------- 데이터 관리 ----------
elif page == "데이터 관리":
    st.markdown('<div class="section-title">💾 데이터 가져오기 및 내보내기</div>', unsafe_allow_html=True)
    st.warning("Streamlit Cloud의 로컬 파일은 재배포·환경 변경 시 유지되지 않을 수 있습니다. 중요한 데이터는 정기적으로 CSV로 내려받아 보관하세요. 실제 개인정보 대신 가상 데이터를 사용하세요.")
    employees = st.session_state.employees
    attendance = st.session_state.attendance
    st.subheader("데이터 내보내기")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**직원 데이터**")
        st.download_button("직원 데이터 CSV 다운로드", data=employees.to_csv(index=False).encode("utf-8-sig"),
                           file_name="hr_employees.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.write("**근태 데이터**")
        st.download_button("근태 데이터 CSV 다운로드", data=attendance.to_csv(index=False).encode("utf-8-sig"),
                           file_name="hr_attendance.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    st.subheader("직원 데이터 가져오기")
    st.caption("UTF-8 CSV를 업로드하세요. 필수 열: 사번, 이름, 부서, 직급, 입사일, 고용형태, 이메일, 상태. 업로드하면 현재 직원 데이터가 교체됩니다.")
    upload = st.file_uploader("직원 CSV 파일 선택", type=["csv"], key="employee_upload")
    if upload is not None:
        try:
            incoming = pd.read_csv(upload, dtype=str).fillna("")
            incoming = normalize_employees(incoming)
            errors = []
            if incoming["사번"].eq("").any(): errors.append("사번이 비어 있는 행이 있습니다.")
            if incoming["이름"].eq("").any(): errors.append("이름이 비어 있는 행이 있습니다.")
            if incoming["사번"].duplicated().any(): errors.append("중복된 사번이 있습니다.")
            if not set(incoming["상태"].unique()).issubset({"재직","퇴사"}): errors.append("상태는 재직 또는 퇴사여야 합니다.")
            if errors:
                for e in errors: st.error(e)
            else:
                st.dataframe(incoming.head(10), use_container_width=True, hide_index=True)
                if st.button("업로드한 직원 데이터로 교체", type="primary"):
                    st.session_state.employees = incoming
                    st.session_state.attendance = normalize_attendance(st.session_state.attendance, incoming)
                    st.session_state.notice = f"직원 데이터 {len(incoming)}명을 불러왔습니다."
                    st.rerun()
        except Exception as e:
            st.error(f"CSV 파일을 읽을 수 없습니다. 열 이름과 인코딩을 확인해 주세요. ({e})")
    st.markdown("---")
    st.subheader("초기 가상 데이터로 복원")
    st.caption("현재 세션의 직원 및 근태 데이터 변경 사항을 초기 시연 데이터로 되돌립니다.")
    confirm_reset = st.checkbox("초기화 내용을 확인했습니다.")
    if st.button("초기 가상 데이터 복원", type="secondary"):
        if confirm_reset:
            st.session_state.employees = sample_employees()
            st.session_state.attendance = sample_attendance(st.session_state.employees)
            st.session_state.workload = {}
            st.session_state.sim_ran = False
            st.session_state.notice = "초기 가상 데이터로 복원했습니다."
            st.rerun()
        else:
            st.warning("복원하려면 먼저 확인란을 선택해 주세요.")

st.markdown('<div class="footer">HR Insight · 데이터 기반 인사 관리 시스템 · 시연용 가상 데이터 사용</div>', unsafe_allow_html=True)
