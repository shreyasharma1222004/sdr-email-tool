import streamlit as st
import time
import uuid
from datetime import datetime
from config.settings import settings
from services.validator import validate_prospect_input, VALID_TONES
from services.researcher import research_company
from services.prompt_builder import (
    build_prompt, ALL_LANGUAGES,
    INTERNATIONAL_LANGUAGES, INDIAN_LANGUAGES,
    LANGUAGE_INSTRUCTIONS
)
from services.openai_client import generate_email
from services.parser import parse_email_response
from services.database import (
    initialize_database, save_prospect, save_email,
    get_recent_emails, update_email_status, soft_delete_email,
    restore_email, permanent_delete_email, save_reply,
    get_replies, get_email_tracking, save_contact,
    get_all_contacts, delete_contact, get_analytics_data
)
from services.exporter import export_to_csv, export_to_txt
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="MailCraft AI — SDR Email Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    settings.validate()
except ValueError as e:
    st.error(f"⚠️ Configuration Error: {e}")
    st.stop()

initialize_database()

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; }
#particles-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
section[data-testid="stSidebar"] { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-right: 1px solid rgba(255,255,255,0.1); z-index: 1; }
.main .block-container { position: relative; z-index: 1; }
.logo-container { text-align: center; padding: 2rem 0 1rem 0; }
.logo-icon { font-size: 3.5rem; display: block; margin-bottom: 0.5rem; animation: floatLogo 3s ease-in-out infinite; filter: drop-shadow(0 0 20px #4f46e5); }
@keyframes floatLogo { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
.logo-text { font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: -1px; }
.logo-tagline { font-size: 0.9rem; color: rgba(255,255,255,0.5); margin-top: 0.3rem; letter-spacing: 2px; text-transform: uppercase; }
.metric-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; text-align: center; transition: all 0.3s ease; }
.metric-card:hover { background: rgba(102,126,234,0.1); border-color: rgba(102,126,234,0.3); transform: translateY(-3px); }
.metric-value { font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #667eea, #f093fb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.metric-label { font-size: 0.75rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; margin-top: 0.2rem; }
.email-card { background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(102,126,234,0.3); border-radius: 16px; padding: 2rem; position: relative; overflow: hidden; animation: fadeInUp 0.6s ease; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.email-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); }
.subject-pill { background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2)); border: 1px solid rgba(102,126,234,0.4); border-radius: 50px; padding: 0.6rem 1.2rem; font-size: 0.95rem; font-weight: 600; color: #a78bfa; display: inline-block; margin-bottom: 1rem; width: 100%; }
.email-body-text { color: rgba(255,255,255,0.85); font-size: 0.95rem; line-height: 1.9; white-space: pre-wrap; }
.typewriter { animation: fadeInUp 0.8s ease; }
.cta-box { background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15)); border: 1px solid rgba(102,126,234,0.3); border-radius: 12px; padding: 1rem 1.5rem; margin-top: 1rem; color: #c4b5fd; font-size: 0.9rem; }
.skeleton { background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%); background-size: 200% 100%; animation: skeleton-loading 1.5s infinite; border-radius: 8px; height: 16px; margin: 8px 0; }
@keyframes skeleton-loading { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.skeleton-title { height: 24px; width: 60%; }
.skeleton-line { height: 14px; width: 100%; }
.skeleton-line-short { height: 14px; width: 75%; }
.step-indicator { display: flex; align-items: center; gap: 0.8rem; padding: 0.8rem 1rem; background: rgba(255,255,255,0.05); border-radius: 10px; margin: 0.4rem 0; color: rgba(255,255,255,0.8); font-size: 0.9rem; animation: slideIn 0.3s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
.step-dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #f093fb); animation: pulse 1s infinite; flex-shrink: 0; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.8; transform: scale(1.3); } }
.quality-bar-container { background: rgba(255,255,255,0.1); border-radius: 50px; height: 8px; width: 100%; margin-top: 0.5rem; }
.quality-bar { height: 8px; border-radius: 50px; background: linear-gradient(135deg, #667eea, #f093fb); transition: width 1.5s ease; }
.score-excellent { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid rgba(16,185,129,0.3); padding: 0.3rem 1rem; border-radius: 50px; display: inline-block; }
.score-good { background: rgba(102,126,234,0.2); color: #667eea; border: 1px solid rgba(102,126,234,0.3); padding: 0.3rem 1rem; border-radius: 50px; display: inline-block; }
.score-fair { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); padding: 0.3rem 1rem; border-radius: 50px; display: inline-block; }
.score-poor { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); padding: 0.3rem 1rem; border-radius: 50px; display: inline-block; }
.empty-state { text-align: center; padding: 4rem 2rem; color: rgba(255,255,255,0.3); }
.char-counter { font-size: 0.75rem; color: rgba(255,255,255,0.3); text-align: right; margin-top: -0.5rem; margin-bottom: 0.5rem; }
.char-counter-warn { color: #f59e0b; font-size: 0.75rem; text-align: right; }
.char-counter-error { color: #ef4444; font-size: 0.75rem; text-align: right; }
.pipeline-step { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 1rem; border-radius: 50px; font-size: 0.8rem; font-weight: 600; margin: 0.2rem; }
.status-draft { background: rgba(156,163,175,0.2); color: #9ca3af; border: 1px solid rgba(156,163,175,0.3); }
.status-sent { background: rgba(59,130,246,0.2); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); }
.status-opened { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.status-replied { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.status-bounced { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.contact-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem; transition: all 0.2s; }
.contact-card:hover { background: rgba(102,126,234,0.08); border-color: rgba(102,126,234,0.2); }
.lang-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; background: rgba(102,126,234,0.2); color: #a78bfa; border: 1px solid rgba(102,126,234,0.3); margin-left: 0.5rem; }
.dashboard-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1.5rem; text-align: center; transition: all 0.3s ease; }
.dashboard-card:hover { background: rgba(102,126,234,0.1); transform: translateY(-4px); border-color: rgba(102,126,234,0.3); }
.dashboard-value { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #667eea, #f093fb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.dashboard-label { font-size: 0.8rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; margin-top: 0.3rem; }
div[data-testid="stForm"] { background: transparent; border: none; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div { background: rgba(255,255,255,0.07) !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 10px !important; color: white !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: rgba(102,126,234,0.6) !important; box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important; }
label { color: rgba(255,255,255,0.7) !important; font-size: 0.85rem !important; }
.stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important; transition: all 0.3s ease !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(102,126,234,0.5) !important; }
.stDownloadButton > button { background: rgba(255,255,255,0.08) !important; color: rgba(255,255,255,0.8) !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 10px !important; }
h1, h2, h3 { color: white !important; }
p { color: rgba(255,255,255,0.7); }
.stProgress > div > div { background: linear-gradient(135deg, #667eea, #f093fb) !important; border-radius: 50px !important; }
hr { border-color: rgba(255,255,255,0.1) !important; }
.stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 4px; }
.stTabs [aria-selected="true"] { background: rgba(102,126,234,0.3) !important; color: white !important; }
</style>

<canvas id="particles-canvas"></canvas>
<script>
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const particles = [];
for (let i = 0; i < 80; i++) {
    particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.4 + 0.1,
        color: Math.random() > 0.5 ? '102,126,234' : '240,147,251'
    });
}
function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color},${p.opacity})`;
        ctx.fill();
    });
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 120) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(102,126,234,${0.1*(1-dist/120)})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(animateParticles);
}
animateParticles();
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
</script>
""", unsafe_allow_html=True)


# ── SESSION STATE ────────────────────────────────────────────
for key, default in {
    "current_email": None,
    "current_prospect": None,
    "current_language": "English",
    "page": "generator",
    "show_confetti": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── HELPERS ──────────────────────────────────────────────────
def show_confetti():
    st.markdown("""
    <script>
    (function() {
        const colors = ['#667eea','#764ba2','#f093fb','#4ade80','#facc15','#f87171'];
        const style = document.createElement('style');
        style.textContent = '@keyframes confettiFall { to { transform: translateY(105vh) rotate(720deg); opacity: 0; } }';
        document.head.appendChild(style);
        for (let i = 0; i < 150; i++) {
            const el = document.createElement('div');
            el.style.cssText = `position:fixed;top:-10px;left:${Math.random()*100}vw;
                width:${Math.random()*10+5}px;height:${Math.random()*10+5}px;
                background:${colors[Math.floor(Math.random()*colors.length)]};
                border-radius:${Math.random()>0.5?'50%':'0'};
                animation:confettiFall ${Math.random()*2+2}s ease-in forwards;
                z-index:9999;opacity:0.9;`;
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 4000);
        }
    })();
    </script>
    """, unsafe_allow_html=True)


def score_email(email) -> dict:
    score = 0
    feedback = []
    if 80 <= email.word_count <= 150:
        score += 25
        feedback.append(("✅", "Perfect length (80-150 words)"))
    elif email.word_count < 80:
        score += 10
        feedback.append(("⚠️", "Too short — add more context"))
    else:
        score += 15
        feedback.append(("⚠️", "A bit long — try to trim it"))
    subject_len = len(email.subject_line)
    if 20 <= subject_len <= 60:
        score += 25
        feedback.append(("✅", "Subject line length is ideal"))
    elif subject_len < 20:
        score += 10
        feedback.append(("⚠️", "Subject line too short"))
    else:
        score += 15
        feedback.append(("⚠️", "Subject line too long"))
    if email.call_to_action and len(email.call_to_action) > 10:
        score += 25
        feedback.append(("✅", "Clear call-to-action present"))
    else:
        score += 5
        feedback.append(("❌", "Missing or weak CTA"))
    spam_words = ["guaranteed", "free", "urgent", "act now", "limited time"]
    spam_found = [w for w in spam_words if w in email.email_body.lower()]
    if not spam_found:
        score += 25
        feedback.append(("✅", "No spam trigger words"))
    else:
        score += 5
        feedback.append(("❌", f"Spam words: {', '.join(spam_found)}"))
    if score >= 90:
        grade = ("Excellent", "score-excellent")
    elif score >= 70:
        grade = ("Good", "score-good")
    elif score >= 50:
        grade = ("Fair", "score-fair")
    else:
        grade = ("Needs Work", "score-poor")
    return {"score": score, "grade": grade, "feedback": feedback}


STATUS_ICONS = {
    "draft": "📝",
    "sent": "📤",
    "opened": "👁️",
    "replied": "💬",
    "bounced": "❌"
}


# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <span class="logo-icon">⚡</span>
        <div class="logo-text">MailCraft AI</div>
        <div class="logo-tagline">SDR Email Generator</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    pages = [
        ("✍️", "Email Generator", "generator"),
        ("📚", "Email History", "history"),
        ("📊", "Batch Upload", "batch"),
        ("📇", "Contacts", "contacts"),
        ("📈", "Analytics", "analytics"),
        ("🗑️", "Recycle Bin", "recycle"),
        ("👤", "About", "about"),
    ]

    for icon, label, key in pages:
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_{key}"):
            st.session_state.page = key

    st.markdown("---")
    st.markdown("""
    <div style='padding:1rem; background:rgba(102,126,234,0.1);
                border-radius:12px; border:1px solid rgba(102,126,234,0.2);'>
        <div style='color:rgba(255,255,255,0.9); font-size:0.85rem; font-weight:600; margin-bottom:0.5rem;'>⚡ Powered by</div>
        <div style='color:#a78bfa; font-size:0.8rem;'>Groq × Llama 3.3-70b</div>
        <div style='color:rgba(255,255,255,0.4); font-size:0.75rem; margin-top:0.3rem;'>Free · Fast · Reliable</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 1 — GENERATOR
# ════════════════════════════════════════════════════════════
if st.session_state.page == "generator":
    col_input, col_output = st.columns([2, 3], gap="large")

    with col_input:
        st.markdown("<h3 style='color:white;'>📋 Prospect Details</h3>", unsafe_allow_html=True)

        with st.form("prospect_form", clear_on_submit=False):
            prospect_name = st.text_input("👤 Prospect Name *", placeholder="e.g., Sarah Johnson", max_chars=100)
            if prospect_name:
                st.markdown(f"<div class='char-counter'>{len(prospect_name)}/100</div>", unsafe_allow_html=True)

            company_name = st.text_input("🏢 Company Name *", placeholder="e.g., Acme Corp", max_chars=100)
            if company_name:
                st.markdown(f"<div class='char-counter'>{len(company_name)}/100</div>", unsafe_allow_html=True)

            prospect_role = st.text_input("💼 Prospect Role *", placeholder="e.g., VP of Sales", max_chars=100)
            if prospect_role:
                st.markdown(f"<div class='char-counter'>{len(prospect_role)}/100</div>", unsafe_allow_html=True)

            tone = st.selectbox(
                "🎨 Email Tone *",
                options=VALID_TONES,
                format_func=lambda x: {
                    "friendly": "😊 Friendly",
                    "formal": "👔 Formal",
                    "direct": "⚡ Direct",
                    "consultative": "🤝 Consultative",
                    "executive": "🎯 Executive"
                }.get(x, x.capitalize())
            )

            st.markdown("**🌍 Email Language**")
            lang_tab1, lang_tab2 = st.tabs(["🌐 International", "🇮🇳 Indian"])
            with lang_tab1:
                selected_lang_intl = st.selectbox(
                    "Select Language",
                    options=["-- Select --"] + INTERNATIONAL_LANGUAGES,
                    key="lang_intl"
                )
            with lang_tab2:
                selected_lang_india = st.selectbox(
                    "Select Language",
                    options=["-- Select --"] + INDIAN_LANGUAGES,
                    key="lang_india"
                )

            with st.expander("✨ Optional — Improves Personalization"):
                company_website = st.text_input("🌐 Company Website", placeholder="https://acmecorp.com")
                linkedin_summary = st.text_area("🔗 LinkedIn Summary", placeholder="Paste their LinkedIn About section...", height=80, max_chars=1000)
                if linkedin_summary:
                    st.markdown(f"<div class='char-counter'>{len(linkedin_summary)}/1000</div>", unsafe_allow_html=True)
                additional_notes = st.text_area("📝 Additional Notes", placeholder="e.g., Recently raised Series B...", height=60, max_chars=500)
                if additional_notes:
                    st.markdown(f"<div class='char-counter'>{len(additional_notes)}/500</div>", unsafe_allow_html=True)

            col_gen, col_regen = st.columns([3, 1])
            with col_gen:
                submitted = st.form_submit_button("⚡ Generate Email", use_container_width=True)
            with col_regen:
                regenerate = st.form_submit_button("🔄 New", use_container_width=True)

    with col_output:
        st.markdown("<h3 style='color:white;'>📧 Generated Email</h3>", unsafe_allow_html=True)

        should_generate = submitted or (regenerate and st.session_state.current_prospect)

        if should_generate:
            # Determine language
            if selected_lang_india != "-- Select --":
                language = selected_lang_india
            elif selected_lang_intl != "-- Select --":
                language = selected_lang_intl
            else:
                language = "English"

            st.session_state.current_language = language

            if regenerate and st.session_state.current_prospect:
                prospect = st.session_state.current_prospect
                is_valid = True
                error_msg = ""
            else:
                form_data = {
                    "prospect_name": prospect_name,
                    "company_name": company_name,
                    "prospect_role": prospect_role,
                    "tone": tone,
                    "company_website": company_website if 'company_website' in dir() else "",
                    "linkedin_summary": linkedin_summary if 'linkedin_summary' in dir() else "",
                    "additional_notes": additional_notes if 'additional_notes' in dir() else "",
                }
                is_valid, error_msg, prospect = validate_prospect_input(form_data)

            if not is_valid:
                st.error(f"⚠️ {error_msg}")
            else:
                lang_data = LANGUAGE_INSTRUCTIONS.get(language, {})
                flag = lang_data.get("flag", "🌍")

                skeleton_placeholder = st.empty()
                with skeleton_placeholder.container():
                    st.markdown("""
                    <div style='background:rgba(255,255,255,0.05); border-radius:16px; padding:2rem;'>
                        <div class='skeleton skeleton-title'></div>
                        <div style='margin:1.5rem 0;'></div>
                        <div class='skeleton skeleton-line'></div>
                        <div class='skeleton skeleton-line'></div>
                        <div class='skeleton skeleton-line-short'></div>
                        <div style='margin:1rem 0;'></div>
                        <div class='skeleton skeleton-line'></div>
                        <div class='skeleton skeleton-line'></div>
                    </div>
                    """, unsafe_allow_html=True)

                steps_placeholder = st.empty()
                progress_bar = st.progress(0)

                try:
                    steps = [
                        ("🔍", f"Researching {prospect.company_name}..."),
                        ("🧠", f"Building {language} prompt..."),
                        (flag, f"Generating email in {language}..."),
                        ("✨", "Scoring and formatting..."),
                    ]

                    for i, (icon, text) in enumerate(steps):
                        steps_placeholder.markdown(f"""
                        <div class='step-indicator'>
                            <div class='step-dot'></div>
                            {icon} {text}
                        </div>
                        """, unsafe_allow_html=True)
                        progress_bar.progress((i + 1) * 20)

                        if i == 0:
                            research = research_company(prospect)
                        elif i == 1:
                            system_prompt, user_prompt = build_prompt(prospect, research, language)
                        elif i == 2:
                            start_time = time.time()
                            raw_response = generate_email(system_prompt, user_prompt)
                            generation_time_ms = int((time.time() - start_time) * 1000)
                        else:
                            email = parse_email_response(raw_response, prospect_id=prospect.id)
                            email.generation_time_ms = generation_time_ms
                            save_prospect(prospect)
                            save_email(email, language=language)

                        time.sleep(0.3)

                    st.session_state.current_email = email
                    st.session_state.current_prospect = prospect
                    st.session_state.show_confetti = True
                    skeleton_placeholder.empty()
                    steps_placeholder.empty()
                    progress_bar.empty()

                except Exception as e:
                    skeleton_placeholder.empty()
                    steps_placeholder.empty()
                    progress_bar.empty()
                    st.error(f"❌ Generation failed: {str(e)}")

        if st.session_state.get("show_confetti"):
            show_confetti()
            st.session_state.show_confetti = False

        if st.session_state.current_email:
            email = st.session_state.current_email
            prospect = st.session_state.current_prospect
            language = st.session_state.get("current_language", "English")
            quality = score_email(email)
            lang_data = LANGUAGE_INSTRUCTIONS.get(language, {})
            flag = lang_data.get("flag", "🌍")

            m1, m2, m3, m4 = st.columns(4)
            for col, (val, label) in zip(
                [m1, m2, m3, m4],
                [(str(email.word_count), "Words"),
                 (f"{email.generation_time_ms}ms", "Speed"),
                 (f"{quality['score']}", "Quality"),
                 (f"{flag} {language}", "Language")]
            ):
                with col:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{val}</div>
                        <div class='metric-label'>{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='email-card'>
                <div style='font-size:0.75rem; color:rgba(255,255,255,0.4);
                            text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;'>
                    Subject Line
                </div>
                <div class='subject-pill'>{email.subject_line}</div>
                <div style='font-size:0.75rem; color:rgba(255,255,255,0.4);
                            text-transform:uppercase; letter-spacing:1px;
                            margin-bottom:0.5rem; margin-top:1rem;'>
                    Email Body
                </div>
                <div class='email-body-text typewriter'>{email.email_body}</div>
                {f'<div class="cta-box">🎯 <strong>CTA:</strong> {email.call_to_action}</div>'
                 if email.call_to_action else ''}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

            with st.expander(f"⭐ Quality Score: {quality['score']}/100 — {quality['grade'][0]}"):
                st.markdown(f"""
                <div class='quality-bar-container'>
                    <div class='quality-bar' style='width:{quality["score"]}%;'></div>
                </div>
                <div style='margin-top:1rem;'></div>
                """, unsafe_allow_html=True)
                for icon, text in quality["feedback"]:
                    st.markdown(f"<div style='color:rgba(255,255,255,0.7); padding:0.3rem 0;'>{icon} {text}</div>", unsafe_allow_html=True)

            st.markdown("**📊 Update Email Status**")
            status_cols = st.columns(5)
            statuses = ["sent", "opened", "replied", "bounced", "draft"]
            for col, status in zip(status_cols, statuses):
                with col:
                    if st.button(f"{STATUS_ICONS[status]} {status.capitalize()}", key=f"status_{status}", use_container_width=True):
                        update_email_status(email.id, status)
                        st.success(f"Marked as {status}")

            full_text = f"Subject: {email.subject_line}\n\n{email.email_body}"
            if email.call_to_action:
                full_text += f"\n\n{email.call_to_action}"

            st.code(full_text, language=None)

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.download_button("📊 CSV", data=export_to_csv(prospect, email),
                    file_name=f"email_{prospect.company_name.lower().replace(' ','_')}.csv",
                    mime="text/csv", use_container_width=True)
            with b2:
                st.download_button("📄 TXT", data=export_to_txt(prospect, email),
                    file_name=f"email_{prospect.company_name.lower().replace(' ','_')}.txt",
                    mime="text/plain", use_container_width=True)
            with b3:
                st.download_button("📋 Copy", data=full_text.encode(),
                    file_name="email.txt", mime="text/plain", use_container_width=True)
            with b4:
                if st.button("🗑️ Delete", use_container_width=True, key="delete_current"):
                    soft_delete_email(email.id)
                    st.session_state.current_email = None
                    st.success("Moved to recycle bin")

        else:
            st.markdown("""
            <div class='empty-state'>
                <div style='font-size:4rem; animation: floatLogo 3s ease-in-out infinite;'>⚡</div>
                <div style='font-size:1.2rem; color:rgba(255,255,255,0.4); font-weight:600; margin-top:1rem;'>Ready to generate</div>
                <div style='font-size:0.9rem; color:rgba(255,255,255,0.25); margin-top:0.5rem;'>Fill in prospect details and click Generate</div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 2 — HISTORY
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "history":
    st.markdown("<h2 style='color:white;'>📚 Email History</h2>", unsafe_allow_html=True)

    recent = get_recent_emails(100)

    if not recent:
        st.markdown("<div class='empty-state'><div style='font-size:3rem;'>📭</div><div style='color:rgba(255,255,255,0.4); margin-top:1rem;'>No emails yet</div></div>", unsafe_allow_html=True)
    else:
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Search", placeholder="Search by name or company...")
        with col_filter:
            status_filter = st.selectbox("Filter by Status", ["All", "draft", "sent", "opened", "replied", "bounced"])

        filtered = recent
        if search:
            filtered = [i for i in filtered if search.lower() in i['prospect_name'].lower() or search.lower() in i['company_name'].lower()]
        if status_filter != "All":
            filtered = [i for i in filtered if i.get('status') == status_filter]

        st.markdown(f"<p style='color:rgba(255,255,255,0.4);'>{len(filtered)} emails found</p>", unsafe_allow_html=True)

        for item in filtered:
            status = item.get('status', 'draft')
            lang = item.get('language', 'English')
            lang_flag = LANGUAGE_INSTRUCTIONS.get(lang, {}).get('flag', '🌍')

            with st.expander(f"{STATUS_ICONS.get(status,'📝')} {item['prospect_name']} at {item['company_name']} — {item['created_at'][:10]}"):
                st.markdown(f"**Subject:** {item['subject_line']}")
                st.markdown(f"<span class='lang-badge'>{lang_flag} {lang}</span>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); padding:1rem;
                            border-radius:8px; color:rgba(255,255,255,0.8);
                            font-size:0.9rem; line-height:1.8; margin-top:0.5rem;'>
                    {item['email_body']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Update Status:**")
                s_cols = st.columns(5)
                for col, s in zip(s_cols, ["sent", "opened", "replied", "bounced", "draft"]):
                    with col:
                        if st.button(f"{STATUS_ICONS[s]} {s.capitalize()}", key=f"h_status_{item['id']}_{s}", use_container_width=True):
                            update_email_status(item['id'], s)
                            st.success(f"Updated to {s}")

                st.markdown("**💬 Log a Reply:**")
                reply_text = st.text_area("Reply received", key=f"reply_{item['id']}", height=80)
                if st.button("Save Reply", key=f"save_reply_{item['id']}"):
                    if reply_text:
                        save_reply(item['id'], reply_text)
                        st.success("✅ Reply saved!")
                    else:
                        st.warning("Please enter the reply text")

                replies = get_replies(item['id'])
                if replies:
                    st.markdown(f"**📬 {len(replies)} Reply/Replies Received:**")
                    for r in replies:
                        st.markdown(f"""
                        <div style='background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2);
                                    border-radius:8px; padding:0.8rem; margin:0.4rem 0;
                                    color:rgba(255,255,255,0.8); font-size:0.85rem;'>
                            💬 {r['reply_text']}
                            <div style='color:rgba(255,255,255,0.3); font-size:0.75rem; margin-top:0.3rem;'>
                                {r['replied_at'][:10]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                if st.button("🗑️ Move to Recycle Bin", key=f"del_{item['id']}"):
                    soft_delete_email(item['id'])
                    st.success("Moved to recycle bin")
                    st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE 3 — BATCH
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "batch":
    st.markdown("<h2 style='color:white;'>📊 Batch Email Generator</h2>", unsafe_allow_html=True)

    import pandas as pd

    batch_language = st.selectbox(
        "🌍 Generate all emails in:",
        options=ALL_LANGUAGES,
        format_func=lambda x: f"{LANGUAGE_INSTRUCTIONS[x]['flag']} {x}"
    )

    sample_df = pd.DataFrame({
        "prospect_name": ["John Smith", "Sarah Lee"],
        "company_name": ["Acme Corp", "TechStart"],
        "prospect_role": ["VP Sales", "CEO"],
        "tone": ["friendly", "executive"],
        "company_website": ["https://acme.com", ""],
    })

    st.markdown("<h4 style='color:white;'>📋 CSV Format</h4>", unsafe_allow_html=True)
    st.dataframe(sample_df, use_container_width=True)
    st.download_button("⬇️ Download Sample CSV", data=sample_df.to_csv(index=False).encode(),
                       file_name="sample_prospects.csv", mime="text/csv")

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload prospects CSV", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ["prospect_name", "company_name", "prospect_role", "tone"]
            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                st.error(f"❌ Missing columns: {', '.join(missing)}")
            else:
                st.success(f"✅ {len(df)} prospects ready")
                st.dataframe(df, use_container_width=True)

                if st.button("⚡ Generate All Emails", use_container_width=True):
                    results = []
                    progress = st.progress(0)
                    status = st.empty()

                    for i, row in df.iterrows():
                        status.markdown(f"""
                        <div class='step-indicator'>
                            <div class='step-dot'></div>
                            Processing {row['prospect_name']} ({i+1}/{len(df)})
                        </div>
                        """, unsafe_allow_html=True)

                        form_data = {
                            "prospect_name": str(row.get("prospect_name", "")),
                            "company_name": str(row.get("company_name", "")),
                            "prospect_role": str(row.get("prospect_role", "")),
                            "tone": str(row.get("tone", "friendly")),
                            "company_website": str(row.get("company_website", "")),
                            "linkedin_summary": "",
                            "additional_notes": "",
                        }

                        is_valid, error_msg, prospect = validate_prospect_input(form_data)
                        if not is_valid:
                            results.append({"prospect_name": row["prospect_name"], "company_name": row["company_name"], "subject_line": "FAILED", "email_body": error_msg, "call_to_action": "", "language": batch_language})
                            continue

                        try:
                            research = research_company(prospect)
                            system_prompt, user_prompt = build_prompt(prospect, research, batch_language)
                            raw_response = generate_email(system_prompt, user_prompt)
                            email = parse_email_response(raw_response, prospect_id=prospect.id)
                            save_prospect(prospect)
                            save_email(email, language=batch_language)
                            results.append({"prospect_name": prospect.prospect_name, "company_name": prospect.company_name, "subject_line": email.subject_line, "email_body": email.email_body, "call_to_action": email.call_to_action, "language": batch_language})
                        except Exception as e:
                            results.append({"prospect_name": row["prospect_name"], "company_name": row["company_name"], "subject_line": "FAILED", "email_body": str(e), "call_to_action": "", "language": batch_language})

                        progress.progress((i + 1) / len(df))
                        time.sleep(0.5)

                    status.empty()
                    results_df = pd.DataFrame(results)
                    success_count = len([r for r in results if r['subject_line'] != 'FAILED'])
                    st.success(f"✅ {success_count}/{len(df)} emails generated in {batch_language}")
                    st.dataframe(results_df, use_container_width=True)
                    st.download_button("📊 Download All", data=results_df.to_csv(index=False).encode(),
                                       file_name="generated_emails.csv", mime="text/csv", use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# ════════════════════════════════════════════════════════════
# PAGE 4 — CONTACTS
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "contacts":
    st.markdown("<h2 style='color:white;'>📇 Contact Manager</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Add Contact", "📋 All Contacts"])

    with tab1:
        with st.form("contact_form"):
            st.markdown("<h4 style='color:white;'>Add New Contact</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("👤 Full Name *", placeholder="John Smith")
                email_addr = st.text_input("📧 Email", placeholder="john@acme.com")
                phone = st.text_input("📱 Phone", placeholder="+1 234 567 8900")
                company = st.text_input("🏢 Company", placeholder="Acme Corp")
            with c2:
                linkedin = st.text_input("🔗 LinkedIn URL", placeholder="https://linkedin.com/in/john")
                twitter = st.text_input("🐦 Twitter", placeholder="https://twitter.com/john")
                website = st.text_input("🌐 Website", placeholder="https://johndoe.com")
            notes = st.text_area("📝 Notes", placeholder="Any additional notes...", height=80)

            if st.form_submit_button("💾 Save Contact", use_container_width=True):
                if full_name:
                    contact = {
                        "full_name": full_name,
                        "email": email_addr,
                        "phone": phone,
                        "company": company,
                        "linkedin_url": linkedin,
                        "twitter_url": twitter,
                        "website": website,
                        "notes": notes
                    }
                    if save_contact(contact):
                        st.success("✅ Contact saved!")
                    else:
                        st.error("❌ Failed to save contact")
                else:
                    st.warning("Full name is required")

    with tab2:
        contacts = get_all_contacts()
        if not contacts:
            st.markdown("<div class='empty-state'><div style='font-size:3rem;'>📭</div><div style='color:rgba(255,255,255,0.4); margin-top:1rem;'>No contacts yet</div></div>", unsafe_allow_html=True)
        else:
            search_contact = st.text_input("🔍 Search contacts", placeholder="Name or company...")
            filtered_contacts = [c for c in contacts if
                search_contact.lower() in c['full_name'].lower() or
                search_contact.lower() in (c['company'] or '').lower()
            ] if search_contact else contacts

            st.markdown(f"<p style='color:rgba(255,255,255,0.4);'>{len(filtered_contacts)} contacts</p>", unsafe_allow_html=True)

            for contact in filtered_contacts:
                with st.expander(f"👤 {contact['full_name']} — {contact.get('company', 'No company')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        if contact.get('email'):
                            st.markdown(f"📧 {contact['email']}")
                        if contact.get('phone'):
                            st.markdown(f"📱 {contact['phone']}")
                        if contact.get('company'):
                            st.markdown(f"🏢 {contact['company']}")
                    with c2:
                        if contact.get('linkedin_url'):
                            st.markdown(f"[🔗 LinkedIn]({contact['linkedin_url']})")
                        if contact.get('twitter_url'):
                            st.markdown(f"[🐦 Twitter]({contact['twitter_url']})")
                        if contact.get('website'):
                            st.markdown(f"[🌐 Website]({contact['website']})")
                    if contact.get('notes'):
                        st.markdown(f"📝 {contact['notes']}")
                    if st.button("🗑️ Delete Contact", key=f"del_contact_{contact['id']}"):
                        delete_contact(contact['id'])
                        st.success("Contact deleted")
                        st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE 5 — ANALYTICS
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "analytics":
    st.markdown("<h2 style='color:white;'>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)

    import pandas as pd
    analytics = get_analytics_data()

    if not analytics or analytics.get("total_emails", 0) == 0:
        st.markdown("<div class='empty-state'><div style='font-size:3rem;'>📊</div><div style='color:rgba(255,255,255,0.4); margin-top:1rem;'>No data yet</div></div>", unsafe_allow_html=True)
    else:
        d1, d2, d3, d4, d5 = st.columns(5)
        stats = [
            (str(analytics.get("total_emails", 0)), "Total Emails"),
            (str(analytics.get("total_replies", 0)), "Replies"),
            (str(analytics.get("total_contacts", 0)), "Contacts"),
            (f"{analytics.get('reply_rate', 0)}%", "Reply Rate"),
            (str(len(analytics.get("by_language", []))), "Languages"),
        ]
        for col, (val, label) in zip([d1, d2, d3, d4, d5], stats):
            with col:
                st.markdown(f"""
                <div class='dashboard-card'>
                    <div class='dashboard-value'>{val}</div>
                    <div class='dashboard-label'>{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin:2rem 0;'></div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("<h4 style='color:white;'>📊 Emails by Status</h4>", unsafe_allow_html=True)
            by_status = analytics.get("by_status", [])
            if by_status:
                status_df = pd.DataFrame(by_status)
                st.bar_chart(status_df.set_index("status"), color="#667eea")

        with col_b:
            st.markdown("<h4 style='color:white;'>🌍 Emails by Language</h4>", unsafe_allow_html=True)
            by_lang = analytics.get("by_language", [])
            if by_lang:
                lang_df = pd.DataFrame(by_lang)
                st.bar_chart(lang_df.set_index("language"), color="#f093fb")

        recent = get_recent_emails(100)
        if recent:
            st.markdown("<h4 style='color:white;'>📅 Emails Over Time</h4>", unsafe_allow_html=True)
            df = pd.DataFrame(recent)
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily = df.groupby('date').size().reset_index(name='count')
            st.bar_chart(daily.set_index('date'), color="#667eea")


# ════════════════════════════════════════════════════════════
# PAGE 6 — RECYCLE BIN
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "recycle":
    st.markdown("<h2 style='color:white;'>🗑️ Recycle Bin</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.5);'>Deleted emails — restore or permanently delete</p>", unsafe_allow_html=True)

    deleted = get_recent_emails(100, include_deleted=True)

    if not deleted:
        st.markdown("<div class='empty-state'><div style='font-size:3rem;'>🗑️</div><div style='color:rgba(255,255,255,0.4); margin-top:1rem;'>Recycle bin is empty</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:rgba(255,255,255,0.4);'>{len(deleted)} deleted emails</p>", unsafe_allow_html=True)

        for item in deleted:
            with st.expander(f"🗑️ {item['prospect_name']} at {item['company_name']} — {item['created_at'][:10]}"):
                st.markdown(f"**Subject:** {item['subject_line']}")
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); padding:1rem;
                            border-radius:8px; color:rgba(255,255,255,0.6);
                            font-size:0.9rem; line-height:1.8;'>
                    {item['email_body'][:200]}...
                </div>
                """, unsafe_allow_html=True)

                r1, r2 = st.columns(2)
                with r1:
                    if st.button("♻️ Restore", key=f"restore_{item['id']}", use_container_width=True):
                        restore_email(item['id'])
                        st.success("✅ Email restored!")
                        st.rerun()
                with r2:
                    if st.button("❌ Delete Forever", key=f"perm_{item['id']}", use_container_width=True):
                        permanent_delete_email(item['id'])
                        st.success("Permanently deleted")
                        st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE 7 — ABOUT
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "about":
    st.markdown("<h2 style='color:white;'>👤 About MailCraft AI</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
                border-radius:16px; padding:2rem; margin-bottom:1rem;'>
        <div style='font-size:1.1rem; color:rgba(255,255,255,0.85); line-height:1.8;'>
            <strong style='color:#a78bfa;'>MailCraft AI</strong> is an AI-powered cold email
            personalization tool built for SDRs, recruiters, and startup founders who want
            to send highly personalized outreach at scale in 18 languages.
            <br><br>
            Built with Python, Streamlit, and Groq AI — reducing email writing time
            from 20 minutes to under 30 seconds.
        </div>
    </div>

    <div style='background:rgba(102,126,234,0.1); border:1px solid rgba(102,126,234,0.2);
                border-radius:16px; padding:2rem; margin-bottom:1rem;'>
        <div style='color:white; font-weight:700; font-size:1.1rem; margin-bottom:1rem;'>🛠️ Tech Stack</div>
        <div style='color:rgba(255,255,255,0.7); line-height:2;'>
            ⚡ <strong style='color:#a78bfa;'>Frontend:</strong> Streamlit<br>
            🐍 <strong style='color:#a78bfa;'>Backend:</strong> Python 3.13<br>
            🤖 <strong style='color:#a78bfa;'>AI:</strong> Groq API × Llama 3.3-70b<br>
            🗄️ <strong style='color:#a78bfa;'>Database:</strong> SQLite<br>
            🔍 <strong style='color:#a78bfa;'>Research:</strong> BeautifulSoup4<br>
            ☁️ <strong style='color:#a78bfa;'>Deployment:</strong> Streamlit Cloud<br>
            🌍 <strong style='color:#a78bfa;'>Languages:</strong> 18 languages supported
        </div>
    </div>

    <div style='background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2);
                border-radius:16px; padding:2rem;'>
        <div style='color:white; font-weight:700; font-size:1.1rem; margin-bottom:1rem;'>🌍 Supported Languages</div>
        <div style='color:rgba(255,255,255,0.7); line-height:2;'>
            🌐 International: English, Spanish, French, German, Arabic, Chinese, Japanese<br>
            🇮🇳 Indian: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Urdu
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:white;'>💬 Feedback</h4>", unsafe_allow_html=True)
    feedback = st.text_area("Share your thoughts", placeholder="What would you like to see improved?", height=100)
    if st.button("Send Feedback", use_container_width=True):
        if feedback:
            st.success("✅ Thank you for your feedback!")
        else:
            st.warning("Please write something first.")