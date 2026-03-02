import streamlit as st
import anthropic
import PyPDF2
import io, json

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0f13, #1a1a2e); }
.hero { text-align:center; }
.hero h1 { background: linear-gradient(135deg,#667eea,#f093fb);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-size:2.8rem; font-weight:700; }
.card { background:#1e1e2e; border:1px solid #2a2a3e; border-radius:14px; padding:1.5rem; margin:0.8rem 0; }
.score { font-size:3.5rem; font-weight:700; text-align:center; }
.tag { display:inline-block; padding:4px 12px; border-radius:20px; font-size:0.78rem; margin:3px; }
.green { background:#1a3a2a; color:#4ade80; border:1px solid #2a5a3a; }
.red   { background:#3a1a1a; color:#f87171; border:1px solid #5a2a2a; }
.good  { background:#1a3a2a; border-left:3px solid #4ade80; border-radius:8px; padding:0.7rem 1rem; margin:0.3rem 0; color:#ccc; }
.bad   { background:#3a1a1a; border-left:3px solid #f87171; border-radius:8px; padding:0.7rem 1rem; margin:0.3rem 0; color:#ccc; }
.tip   { background:#1a1a3a; border-left:3px solid #667eea; border-radius:8px; padding:0.9rem 1.2rem; margin:0.4rem 0; color:#ccc; }
.stButton>button { background:linear-gradient(135deg,#667eea,#764ba2)!important;
    color:white!important; border:none!important; border-radius:10px!important;
    font-weight:600!important; font-size:1rem!important; width:100%!important; }
h1,h2,h3 { color:#e0e0ff; }
p,li { color:#ccc; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>📄 AI Resume Analyzer</h1></div>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#888">ATS score · keyword gaps · actionable tips — powered by Claude AI</p>', unsafe_allow_html=True)

with st.expander("🔑 Anthropic API Key", expanded=not st.session_state.get("api_key")):
    key = st.text_input("Key", type="password", placeholder="sk-ant-...", label_visibility="collapsed")
    if key:
        st.session_state["api_key"] = key
        st.success("✅ Saved!")

if not st.session_state.get("api_key"):
    st.info("Add your Anthropic API key above → get one free at console.anthropic.com")
    st.stop()

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("### 📤 Upload Resume (PDF)")
    pdf = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
with c2:
    st.markdown("### 💼 Job Description *(optional)*")
    jd = st.text_area("JD", height=170, placeholder="Paste job description for match analysis...", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 Analyze My Resume"):
    if not pdf:
        st.warning("Please upload a PDF first.")
        st.stop()
    with st.spinner("Claude is reading your resume..."):
        reader = PyPDF2.PdfReader(io.BytesIO(pdf.read()))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        if len(text.strip()) < 50:
            st.error("Couldn't extract text — use a text-based (not scanned) PDF.")
            st.stop()
        client = anthropic.Anthropic(api_key=st.session_state["api_key"])
        prompt = f"""Analyze this resume against the job description.
RESUME: {text}
JOB DESCRIPTION: {jd or 'General full-stack developer role'}

Return ONLY valid JSON, no markdown fences:
{{"ats_score":<int>,"match_score":<int>,"summary":"<2 sentences>",
"strengths":["s1","s2","s3"],"improvements":["i1","i2","i3"],
"matched_keywords":["k1","k2","k3","k4","k5"],
"missing_keywords":["k1","k2","k3","k4","k5"],
"tips":[{{"title":"t","detail":"d"}},{{"title":"t","detail":"d"}},{{"title":"t","detail":"d"}}]}}"""
        try:
            msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1500,
                messages=[{"role":"user","content":prompt}])
            raw = msg.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:-1])
            r = json.loads(raw)
        except Exception as e:
            st.error(f"Error: {e}"); st.stop()

    st.markdown("---")
    ats, match = r.get("ats_score",0), r.get("match_score",0)
    sc = lambda v: "#4ade80" if v>=80 else "#facc15" if v>=60 else "#f87171"

    cols = st.columns(3)
    for col, label, val, em in zip(cols, ["ATS Score","Job Match","Overall"], [ats,match,(ats+match)//2], ["🤖","🎯","⭐"]):
        with col:
            st.markdown(f'<div class="card"><div style="font-size:2rem;text-align:center">{em}</div>'
                        f'<div class="score" style="color:{sc(val)}">{val}</div>'
                        f'<p style="text-align:center;color:#aaa;font-size:.85rem">{label} / 100</p></div>',
                        unsafe_allow_html=True)

    st.markdown(f'<div class="card"><b style="color:#a5b4fc">💬 Summary</b><br><br>'
                f'<span style="color:#ccc">{r.get("summary","")}</span></div>', unsafe_allow_html=True)

    kc1, kc2 = st.columns(2)
    with kc1:
        st.markdown('<div class="card"><b style="color:#a5b4fc">✅ Matched Keywords</b><br><br>' +
            " ".join(f'<span class="tag green">{k}</span>' for k in r.get("matched_keywords",[])) + "</div>", unsafe_allow_html=True)
    with kc2:
        st.markdown('<div class="card"><b style="color:#a5b4fc">❌ Missing Keywords</b><br><br>' +
            " ".join(f'<span class="tag red">{k}</span>' for k in r.get("missing_keywords",[])) + "</div>", unsafe_allow_html=True)

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown('<div class="card"><b style="color:#a5b4fc">💪 Strengths</b><br><br>' +
            "".join(f'<div class="good">✓ {s}</div>' for s in r.get("strengths",[])) + "</div>", unsafe_allow_html=True)
    with rc2:
        st.markdown('<div class="card"><b style="color:#a5b4fc">🔧 Improve These</b><br><br>' +
            "".join(f'<div class="bad">→ {s}</div>' for s in r.get("improvements",[])) + "</div>", unsafe_allow_html=True)

    st.markdown("### 💡 Actionable Tips")
    for t in r.get("tips",[]):
        st.markdown(f'<div class="tip"><b style="color:#a5b4fc">💡 {t.get("title","")}</b><br>{t.get("detail","")}</div>',
                    unsafe_allow_html=True)
    st.success("✅ Analysis complete — use these insights to level up your resume!")
```

---

## 🤖 Project 2: AI Code Reviewer
**GitHub repo name:** `ai-code-reviewer`

### `requirements.txt`
```
streamlit
anthropic
