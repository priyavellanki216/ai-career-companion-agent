import os
import requests
import streamlit as st

API = os.getenv("CAREER_API_URL", "http://localhost:8000")
st.set_page_config(page_title="AI Career Companion", page_icon="✦", layout="wide")

st.markdown("""<style>
:root { --ink:#14213d; --muted:#64748b; --accent:#e76f51; --paper:#f7f5f0; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width: 1320px; padding-top: 2rem; }
[data-testid="stSidebar"] { background:#14213d; }
[data-testid="stSidebar"] * { color:#f7f5f0 !important; }
.metric-card { background:white; padding:1rem 1.2rem; border-radius:16px; box-shadow:0 8px 24px rgba(20,33,61,.07); border:1px solid #e8e4dc; }
.small-label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
</style>""", unsafe_allow_html=True)


def api(method, path, **kwargs):
    try:
        response = requests.request(method, API + path, timeout=20, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Backend unavailable: {exc}")
        return None


def refresh():
    st.session_state.profile = api("GET", "/api/profile") or st.session_state.get("profile", {})
    st.session_state.jobs = api("GET", "/api/jobs") or []
    st.session_state.apps = api("GET", "/api/applications") or []
    st.session_state.dashboard = api("GET", "/api/dashboard") or {}

if "profile" not in st.session_state:
    refresh()

with st.sidebar:
    st.markdown("# AI Career\n## Companion")
    st.caption("Explainable internship matching for students")
    page = st.radio("Workspace", ["Dashboard", "Student Profile", "Resume Upload", "Internship Matching", "Skill Gap Analysis", "Resume / Cover Letter", "Interview Preparation", "Application Tracker", "Career Assistant"])
    st.divider()
    st.caption("Demo mode is deterministic when no LLM key is configured.")

st.title(page)

if page == "Dashboard":
    st.markdown("Build a focused job-search loop: understand your evidence, compare roles, close gaps, and keep applications moving.")
    d = st.session_state.dashboard
    cols = st.columns(4)
    for col, label, value in zip(cols, ["Profile completeness", "Matched jobs", "Applications in progress", "Resumes uploaded"], [f"{d.get('profile_completeness',0)}%", d.get('matched_jobs_count',0), d.get('applications_in_progress',0), d.get('resume_count',0)]):
        col.markdown(f'<div class="metric-card"><div class="small-label">{label}</div><h2>{value}</h2></div>', unsafe_allow_html=True)
    st.subheader("Current skill-gap signal")
    st.write(", ".join(d.get("top_skill_gaps", [])) or "Upload a resume or update your profile to see recommendations.")
    st.subheader("Recommended next step")
    st.info("Start with Student Profile, then upload a resume. Matching and generation use only evidence you provide.")

elif page == "Student Profile":
    p = st.session_state.profile
    with st.form("profile"):
        name = st.text_input("Name", p.get("name", ""))
        education = st.text_area("Education (one item per line)", "\n".join(p.get("education", [])))
        skills = st.text_area("Skills (comma separated)", ", ".join(p.get("skills", [])))
        experience = st.text_area("Experience (one item per line)", "\n".join(p.get("experience", [])))
        certifications = st.text_area("Certifications (one item per line)", "\n".join(p.get("certifications", [])))
        projects = st.text_area("Projects (one item per line)", "\n".join(p.get("projects", [])))
        if st.form_submit_button("Save profile"):
            result = api("PUT", "/api/profile", json={"name":name, "education":[x for x in education.splitlines() if x.strip()], "skills":[x.strip() for x in skills.split(",") if x.strip()], "experience":[x for x in experience.splitlines() if x.strip()], "certifications":[x for x in certifications.splitlines() if x.strip()], "projects":[x for x in projects.splitlines() if x.strip()]})
            if result: st.success("Profile saved."); refresh()

elif page == "Resume Upload":
    st.write("Upload a text-readable PDF or DOCX. The parser extracts conservative evidence; review it before relying on it.")
    file = st.file_uploader("Resume", type=["pdf", "docx"])
    if file and st.button("Parse resume"):
        result = api("POST", "/api/resumes/upload", files={"file": (file.name, file.getvalue(), file.type)})
        if result:
            st.success(f"Parsed {result['filename']}")
            st.json(result["parsed"]); refresh()

elif page == "Internship Matching":
    if st.button("Refresh matches"): refresh()
    st.caption(f"Showing {len(st.session_state.jobs)} seeded listings. Scores are explainable keyword-overlap fallbacks in demo mode.")
    for job in st.session_state.jobs:
        with st.container(border=True):
            c1, c2 = st.columns([4,1])
            c1.subheader(job["title"]); c1.write(f"{job['company']} · {job['location']} · {job['employment_type']}")
            c2.metric("Compatibility", f"{job['compatibility_score']:.0f}%")
            st.write(job["description"])
            st.write("**Matched:** " + (", ".join(job["matched_skills"]) or "None yet") + "  |  **Missing:** " + (", ".join(job["missing_skills"]) or "None") )
            if st.button("Save job", key=f"save-{job['id']}"):
                api("POST", f"/api/saved-jobs/{job['id']}"); st.toast("Saved")

elif page == "Skill Gap Analysis":
    gaps = api("GET", "/api/skill-gaps") or {}
    st.subheader("Missing skills across the job set")
    st.write(", ".join(gaps.get("missing_skills", [])) or "No gaps detected")
    for rec in gaps.get("recommendations", []):
        st.markdown(f"**{rec['skill']}** · Priority {rec['priority']} — {rec['recommendation']}")

elif page == "Resume / Cover Letter":
    jobs = st.session_state.jobs
    if jobs:
        job = st.selectbox("Target job", jobs, format_func=lambda x: f"{x['title']} — {x['company']}")
        if st.button("Generate tailored content"):
            resume = api("POST", "/api/generate/resume", json={"job_id":job["id"]})
            cover = api("POST", "/api/generate/cover-letter", json={"job_id":job["id"]})
            if resume:
                st.subheader("Resume bullets"); [st.write(f"• {b}") for b in resume["bullets"]]; st.caption(resume["note"])
            if cover: st.subheader("Cover letter"); st.text_area("Draft", cover["cover_letter"], height=260)

elif page == "Interview Preparation":
    jobs = st.session_state.jobs
    if jobs:
        job = st.selectbox("Interview target", jobs, format_func=lambda x: f"{x['title']} — {x['company']}")
        if st.button("Prepare interview"):
            prep = api("POST", "/api/generate/interview", json={"job_id":job["id"]})
            if prep:
                st.subheader("Questions"); [st.write(f"{i+1}. {q}") for i,q in enumerate(prep["questions"])]
                st.subheader("Preparation strategy"); [st.write(f"• {s}") for s in prep["strategy"]]

elif page == "Application Tracker":
    jobs = st.session_state.jobs
    if jobs:
        job = st.selectbox("Job", jobs, format_func=lambda x: f"{x['title']} — {x['company']}")
        status = st.selectbox("Status", ["Saved", "Applied", "Interview", "Offer", "Rejected"])
        notes = st.text_area("Notes")
        deadline = st.date_input("Deadline", value=None)
        if st.button("Save application"):
            api("POST", "/api/applications", json={"job_id":job["id"], "status":status, "notes":notes, "deadline":str(deadline) if deadline else None}); st.success("Application updated."); refresh()
    st.subheader("Tracked applications")
    for app in st.session_state.apps: st.write(f"**{app['job_title']}** · {app['company']} · `{app['status']}` · {app['notes']}")

elif page == "Career Assistant":
    st.write("Ask about roles, resumes, skills, interviews, or organizing your search. Messages are retained for this session.")
    if "chat" not in st.session_state: st.session_state.chat = []
    for message in st.session_state.chat: st.chat_message(message["role"]).write(message["content"])
    prompt = st.chat_input("What should I work on next?")
    if prompt:
        st.session_state.chat.append({"role":"user", "content":prompt})
        result = api("POST", "/api/chat", json={"message":prompt, "history":st.session_state.chat}) or {"reply":"The assistant is temporarily unavailable."}
        st.session_state.chat.append({"role":"assistant", "content":result["reply"]})
        st.rerun()
