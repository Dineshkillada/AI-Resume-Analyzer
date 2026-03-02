import streamlit as st
import anthropic
import PyPDF2
import io
import json

# ── Page Config ──────────────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# ── Styling ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0f13, #1a1a2e); }

.hero h1 {
    background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem; font-weight: 700; text-align: center;
}
.card {
    background: #1e1e2e; border: 1px solid #2a2a3e;
    border-radius: 14px; padding: 1.5rem; margin: 0.8rem 0;
}
.score {
    font-size: 3.5rem; font-weight: 700; text-align: center;
}
.tag {
    display: inline-block; padding: 4px 12px;
    border-radius: 20px; font-size: 0.78rem; margin: 3px;
}
.green { background: #1a3a2a; color: #4ade80; border: 1px solid #2a5a3a; }
.red   { background: #3a1a1a; color: #f87171; border: 1px solid #5a2a2a; }
.good  {
    background: #1a3a2a; border-left: 3px solid #4ade80;
    border-radius: 8px; padding: 0.7rem 1rem; margin: 0.3rem 0; color: #ccc;
}
.bad   {
    background: #3a1a1a; border-left: 3px solid #f87171;
    border-radius: 8px; padding: 0.7rem 1rem; margin: 0.3rem 0; color: #ccc;
}
.tip   {
    background: #1a1a3a; border-left: 3px solid #667eea;
    border-radius: 8px; padding: 0.9rem 1.2rem; margin: 0.4rem 0; color: #ccc;
}
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 1rem !important; width: 100% !important;
}
.stTextArea textarea {
    background: #1e1e2e !important; color: #e0e0ff !important;
    border: 1px solid #333 !important; border-radius: 10px !important;
}
h1, h2, h3 { color: #e0e0ff; }
p { color: #ccc; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────
def extract_pdf_text(pdf_file):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def analyze_resume(resume_text, job_desc, api_key):
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
You are an expert ATS analyst and career coach.
Analyze this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_desc if job_desc.strip() else "General full-stack / software engineering role"}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "ats_score": <int 0-100>,
  "match_score": <int 0-100>,
  "summary": "<2 sentence overall assessment>",
  "strengths": ["<s1>", "<s2>", "<s3>"],
  "improvements": ["<i1>", "<i2>", "<i3>"],
  "matched_keywords": ["<k1>", "<k2>", "<k3>", "<k4>", "<k5>"],
  "missing_keywords": ["<k1>", "<k2>", "<k3>", "<k4>", "<k5>"],
  "tips": [
    {{"title": "<title>", "detail": "<actionable advice>"}},
    {{"title": "<title>", "detail": "<actionable advice>"}},
    {{"title": "<title>", "detail": "<actionable advice>"}}
  ]
}}
"""
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    return json.loads(raw)


def score_color(v):
    return "#4ade80" if v >= 80 else "#facc15" if v >= 60 else "#f87171"


# ── UI ────────────────────────────────────────────
st.markdown('<div class="hero"><h1>📄 AI Resume Analyzer</h1></div>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align:center;color:#888;font-size:1.05rem">'
    'Get your ATS score, keyword gaps & actionable tips — powered by Claude AI</p>',
    unsafe_allow_html=True
)

# API Key section
with st.expander("🔑 Enter your Anthropic API Key", expanded=not st.session_state.get("api_key")):
    key = st.text_input("API Key", type="password", placeholder="sk-ant-...", label_visibility="collapsed")
    if key:
        st.session_state["api_key"] = key
        st.success("✅ Key saved!")

if not st.session_state.get("api_key"):
    st.info("👆 Add your free Anthropic API key above. Get one at console.anthropic.com")
    st.stop()

# Inputs
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("### 📤 Upload Your Resume (PDF)")
    pdf = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")

with col2:
    st.markdown("### 💼 Job Description *(optional but recommended)*")
    jd = st.text_area(
        "JD", height=180,
        placeholder="Paste the job description here for a personalized match score...",
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)
analyze = st.button("🚀 Analyze My Resume", use_container_width=True)

# ── Analysis ──────────────────────────────────────
if analyze:
    if not pdf:
        st.warning("⚠️ Please upload a PDF resume first.")
        st.stop()

    with st.spinner("🤖 Claude is analyzing your resume..."):
        try:
            resume_text = extract_pdf_text(pdf)
            if len(resume_text.strip()) < 50:
                st.error("❌ Couldn't extract text. Make sure your PDF is text-based, not a scanned image.")
                st.stop()
            r = analyze_resume(resume_text, jd, st.session_state["api_key"])
        except json.JSONDecodeError:
            st.error("Unexpected AI response. Please try again.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    st.markdown("---")
    st.markdown("## 📊 Your Results")

    # Score cards
    ats   = r.get("ats_score", 0)
    match = r.get("match_score", 0)
    avg   = (ats + match) // 2

    c1, c2, c3 = st.columns(3)
    for col, label, val, emoji in [
        (c1, "ATS Score",  ats,   "🤖"),
        (c2, "Job Match",  match, "🎯"),
        (c3, "Overall",    avg,   "⭐"),
    ]:
        with col:
            st.markdown(
                f'<div class="card">'
                f'<div style="font-size:2rem;text-align:center">{emoji}</div>'
                f'<div class="score" style="color:{score_color(val)}">{val}</div>'
                f'<p style="text-align:center;color:#aaa;font-size:.85rem">{label} / 100</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Summary
    st.markdown(
        f'<div class="card"><b style="color:#a5b4fc">💬 Summary</b><br><br>'
        f'<span style="color:#ccc">{r.get("summary", "")}</span></div>',
        unsafe_allow_html=True
    )

    # Keywords
    kc1, kc2 = st.columns(2)
    with kc1:
        tags = " ".join(f'<span class="tag green">{k}</span>' for k in r.get("matched_keywords", []))
        st.markdown(f'<div class="card"><b style="color:#a5b4fc">✅ Matched Keywords</b><br><br>{tags}</div>', unsafe_allow_html=True)
    with kc2:
        tags = " ".join(f'<span class="tag red">{k}</span>' for k in r.get("missing_keywords", []))
        st.markdown(f'<div class="card"><b style="color:#a5b4fc">❌ Missing Keywords</b><br><br>{tags}</div>', unsafe_allow_html=True)

    # Strengths & Improvements
    rc1, rc2 = st.columns(2)
    with rc1:
        items = "".join(f'<div class="good">✓ {s}</div>' for s in r.get("strengths", []))
        st.markdown(f'<div class="card"><b style="color:#a5b4fc">💪 Strengths</b><br><br>{items}</div>', unsafe_allow_html=True)
    with rc2:
        items = "".join(f'<div class="bad">→ {s}</div>' for s in r.get("improvements", []))
        st.markdown(f'<div class="card"><b style="color:#a5b4fc">🔧 Improve These</b><br><br>{items}</div>', unsafe_allow_html=True)

    # Tips
    st.markdown("### 💡 Actionable Tips")
    for t in r.get("tips", []):
        st.markdown(
            f'<div class="tip"><b style="color:#a5b4fc">💡 {t.get("title","")}</b>'
            f'<br>{t.get("detail","")}</div>',
            unsafe_allow_html=True
        )

    st.success("✅ Analysis complete! Use these insights to sharpen your resume before applying.")
