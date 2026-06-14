import streamlit as st
import time
import random
from config.settings import settings
from services.validator import validate_prospect_input, VALID_TONES
from services.researcher import research_company
from services.prompt_builder import build_prompt
from services.openai_client import generate_email
from services.parser import parse_email_response
from services.database import initialize_database, save_prospect, save_email, get_recent_emails
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

#particles-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
}

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.1);
    z-index: 1;
}

.main .block-container { position: relative; z-index: 1; }

.logo-container {
    text-align: center;
    padding: 2rem 0 1rem 0;
}

.logo-icon {
    font-size: 3.5rem;
    display: block;
    margin-bottom: 0.5rem;
    animation: floatLogo 3s ease-in-out infinite;
    filter: drop-shadow(0 0 20px #4f46e5);
}

@keyframes floatLogo {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

.logo-text {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
}

.logo-tagline {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.5);
    margin-top: 0.3rem;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.metric-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    background: rgba(102,126,234,0.1);
    border-color: rgba(102,126,234,0.3);
    transform: translateY(-3px);
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
}

.email-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(102,126,234,0.3);
    border-radius: 16px;
    padding: 2rem;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.6s ease;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.email-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { opacity: 1; }
    50% { opacity: 0.6; }
    100% { opacity: 1; }
}

.subject-pill {
    background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
    border: 1px solid rgba(102,126,234,0.4);
    border-radius: 50px;
    padding: 0.6rem 1.2rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #a78bfa;
    display: inline-block;
    margin-bottom: 1rem;
    width: 100%;
}

.email-body-text {
    color: rgba(255,255,255,0.85);
    font-size: 0.95rem;
    line-height: 1.9;
    white-space: pre-wrap;
}

.typewriter {
    overflow: hidden;
    animation: typing 2s steps(40, end);
}

@keyframes typing {
    from { max-height: 0; opacity: 0; }
    to { max-height: 1000px; opacity: 1; }
}

.cta-box {
    background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
    border: 1px solid rgba(102,126,234,0.3);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-top: 1rem;
    color: #c4b5fd;
    font-size: 0.9rem;
}

.skeleton {
    background: linear-gradient(90deg, 
        rgba(255,255,255,0.05) 25%, 
        rgba(255,255,255,0.1) 50%, 
        rgba(255,255,255,0.05) 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 8px;
    height: 16px;
    margin: 8px 0;
}

@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-title { height: 24px; width: 60%; }
.skeleton-line { height: 14px; width: 100%; }
.skeleton-line-short { height: 14px; width: 75%; }

.glow-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 1.1rem;
    font-weight: 700;
    padding: 0.9rem 2rem;
    width: 100%;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 20px rgba(102,126,234,0.5),
                0 0 40px rgba(102,126,234,0.3),
                0 0 80px rgba(102,126,234,0.1);
    animation: glowPulse 2s ease-in-out infinite;
    transition: all 0.3s ease;
}

@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 20px rgba(102,126,234,0.5), 0 0 40px rgba(102,126,234,0.3); }
    50% { box-shadow: 0 0 30px rgba(102,126,234,0.8), 0 0 60px rgba(102,126,234,0.5), 0 0 100px rgba(118,75,162,0.3); }
}

.glow-btn:hover { transform: translateY(-3px) scale(1.02); }

.step-indicator {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1rem;
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    margin: 0.4rem 0;
    color: rgba(255,255,255,0.8);
    font-size: 0.9rem;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
}

.step-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #f093fb);
    animation: pulse 1s infinite;
    flex-shrink: 0;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(102,126,234,0.4); }
    50% { opacity: 0.8; transform: scale(1.3); box-shadow: 0 0 0 6px rgba(102,126,234,0); }
}

.confetti-container {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 9999;
}

.quality-bar-container {
    background: rgba(255,255,255,0.1);
    border-radius: 50px;
    height: 8px;
    width: 100%;
    margin-top: 0.5rem;
}

.quality-bar {
    height: 8px;
    border-radius: 50px;
    background: linear-gradient(135deg, #667eea, #f093fb);
    transition: width 1.5s ease;
}

.score-excellent { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid rgba(16,185,129,0.3); padding: 0.3rem 1rem; border-radius: 50px; }
.score-good { background: rgba(102,126,234,0.2); color: #667eea; border: 1px solid rgba(102,126,234,0.3); padding: 0.3rem 1rem; border-radius: 50px; }
.score-fair { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); padding: 0.3rem 1rem; border-radius: 50px; }
.score-poor { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); padding: 0.3rem 1rem; border-radius: 50px; }

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: rgba(255,255,255,0.3);
}

.char-counter {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.3);
    text-align: right;
    margin-top: -0.5rem;
    margin-bottom: 0.5rem;
}

.char-counter-warn { color: #f59e0b; }
.char-counter-error { color: #ef4444; }

.history-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: all 0.2s ease;
}

.history-card:hover {
    background: rgba(102,126,234,0.08);
    border-color: rgba(102,126,234,0.25);
}

.dashboard-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}

.dashboard-card:hover {
    background: rgba(102,126,234,0.1);
    transform: translateY(-4px);
    border-color: rgba(102,126,234,0.3);
}

.dashboard-value {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.dashboard-label {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

div[data-testid="stForm"] { background: transparent; border: none; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(102,126,234,0.6) !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
}

label { color: rgba(255,255,255,0.7) !important; font-size: 0.85rem !important; }

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102,126,234,0.5) !important;
}

.stDownloadButton > button {
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.8) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
}

h1, h2, h3 { color: white !important; }
p { color: rgba(255,255,255,0.7); }

.stProgress > div > div {
    background: linear-gradient(135deg, #667eea, #f093fb) !important;
    border-radius: 50px !important;
}

hr { border-color: rgba(255,255,255,0.1) !important; }

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 4px;
}

.stTabs [aria-selected="true"] {
    background: rgba(102,126,234,0.3) !important;
    color: white !important;
}
</style>

<!-- Particle Background -->
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
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color},${p.opacity})`;
        ctx.fill();
    });

    // Draw lines between nearby particles
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 120) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(102,126,234,${0.1 * (1 - dist/120)})`;
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


# ── SESSION STATE ───────────────────────────────────────────
if "current_email" not in st.session_state:
    st.session_state.current_email = None
if "current_prospect" not in st.session_state:
    st.session_state.current_prospect = None
if "page" not in st.session_state:
    st.session_state.page = "generator"
if "show_confetti" not in st.session_state:
    st.session_state.show_confetti = False


# ── CONFETTI ────────────────────────────────────────────────
def show_confetti():
    st.markdown("""
    <script>
    function launchConfetti() {
        const colors = ['#667eea','#764ba2','#f093fb','#4ade80','#facc15','#f87171'];
        for (let i = 0; i < 150; i++) {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                top: -10px;
                left: ${Math.random() * 100}vw;
                width: ${Math.random() * 10 + 5}px;
                height: ${Math.random() * 10 + 5}px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                animation: confettiFall ${Math.random() * 2 + 2}s ease-in forwards;
                z-index: 9999;
                opacity: 0.9;
            `;
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 4000);
        }
    }

    const style = document.createElement('style');
    style.textContent = `
        @keyframes confettiFall {
            to {
                transform: translateY(105vh) rotate(${Math.random() * 720}deg);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    launchConfetti();
    </script>
    """, unsafe_allow_html=True)


# ── QUALITY SCORER ──────────────────────────────────────────
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
        feedback.append(("❌", "Missing or weak call-to-action"))

    spam_words = ["guaranteed", "free", "urgent", "act now", "limited time"]
    body_lower = email.email_body.lower()
    spam_found = [w for w in spam_words if w in body_lower]
    if not spam_found:
        score += 25
        feedback.append(("✅", "No spam trigger words detected"))
    else:
        score += 5
        feedback.append(("❌", f"Spam words found: {', '.join(spam_found)}"))

    if score >= 90:
        grade = ("Excellent", "score-excellent")
    elif score >= 70:
        grade = ("Good", "score-good")
    elif score >= 50:
        grade = ("Fair", "score-fair")
    else:
        grade = ("Needs Work", "score-poor")

    return {"score": score, "grade": grade, "feedback": feedback}


# ── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <span class="logo-icon">⚡</span>
        <div class="logo-text">MailCraft AI</div>
        <div class="logo-tagline">SDR Email Generator</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("✍️  Email Generator", use_container_width=True):
        st.session_state.page = "generator"
    if st.button("📚  Email History", use_container_width=True):
        st.session_state.page = "history"
    if st.button("📊  Batch Upload", use_container_width=True):
        st.session_state.page = "batch"
    if st.button("📈  Analytics", use_container_width=True):
        st.session_state.page = "analytics"
    if st.button("👤  About", use_container_width=True):
        st.session_state.page = "about"

    st.markdown("---")
    st.markdown("""
    <div style='padding:1rem; background:rgba(102,126,234,0.1);
                border-radius:12px; border:1px solid rgba(102,126,234,0.2);'>
        <div style='color:rgba(255,255,255,0.9); font-size:0.85rem; font-weight:600; margin-bottom:0.5rem;'>
            ⚡ Powered by
        </div>
        <div style='color:#a78bfa; font-size:0.8rem;'>Groq × Llama 3.3-70b</div>
        <div style='color:rgba(255,255,255,0.4); font-size:0.75rem; margin-top:0.3rem;'>
            Free · Fast · Reliable
        </div>
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
                color = "char-counter-warn" if len(prospect_name) > 80 else "char-counter"
                st.markdown(f"<div class='{color}'>{len(prospect_name)}/100</div>", unsafe_allow_html=True)

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

            with st.expander("✨ Optional — Improves Personalization"):
                company_website = st.text_input("🌐 Company Website", placeholder="https://acmecorp.com")
                linkedin_summary = st.text_area("🔗 LinkedIn Summary", placeholder="Paste their LinkedIn About section...", height=80, max_chars=1000)
                if linkedin_summary:
                    color = "char-counter-warn" if len(linkedin_summary) > 800 else "char-counter"
                    st.markdown(f"<div class='{color}'>{len(linkedin_summary)}/1000</div>", unsafe_allow_html=True)
                additional_notes = st.text_area("📝 Additional Notes", placeholder="e.g., Recently raised Series B...", height=60, max_chars=500)
                if additional_notes:
                    color = "char-counter-warn" if len(additional_notes) > 400 else "char-counter"
                    st.markdown(f"<div class='{color}'>{len(additional_notes)}/500</div>", unsafe_allow_html=True)

            col_gen, col_regen = st.columns([3, 1])
            with col_gen:
                submitted = st.form_submit_button("⚡ Generate Email", use_container_width=True)
            with col_regen:
                regenerate = st.form_submit_button("🔄 New", use_container_width=True, help="Regenerate")

    with col_output:
        st.markdown("<h3 style='color:white;'>📧 Generated Email</h3>", unsafe_allow_html=True)

        should_generate = submitted or (regenerate and st.session_state.current_prospect)

        if should_generate:
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
                # Skeleton loading
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
                        <div class='skeleton skeleton-line-short'></div>
                    </div>
                    """, unsafe_allow_html=True)

                steps_placeholder = st.empty()
                progress_bar = st.progress(0)

                try:
                    steps = [
                        ("🔍", "Researching company intelligence..."),
                        ("🧠", "Engineering personalized prompt..."),
                        ("⚡", "Generating with Groq AI..."),
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
                            system_prompt, user_prompt = build_prompt(prospect, research)
                        elif i == 2:
                            start_time = time.time()
                            raw_response = generate_email(system_prompt, user_prompt)
                            generation_time_ms = int((time.time() - start_time) * 1000)
                        else:
                            email = parse_email_response(raw_response, prospect_id=prospect.id)
                            email.generation_time_ms = generation_time_ms
                            save_prospect(prospect)
                            save_email(email)

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

        # Show confetti once
        if st.session_state.get("show_confetti"):
            show_confetti()
            st.session_state.show_confetti = False

        if st.session_state.current_email:
            email = st.session_state.current_email
            prospect = st.session_state.current_prospect
            quality = score_email(email)

            m1, m2, m3, m4 = st.columns(4)
            for col, (val, label) in zip(
                [m1, m2, m3, m4],
                [(str(email.word_count), "Words"),
                 (f"{email.generation_time_ms}ms", "Speed"),
                 (f"{len(email.subject_line)}", "Subject"),
                 (f"{quality['score']}", "Quality")]
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
                    st.markdown(
                        f"<div style='color:rgba(255,255,255,0.7); padding:0.3rem 0;'>{icon} {text}</div>",
                        unsafe_allow_html=True
                    )

            full_text = f"Subject: {email.subject_line}\n\n{email.email_body}"
            if email.call_to_action:
                full_text += f"\n\n{email.call_to_action}"

            st.code(full_text, language=None)

            b1, b2, b3 = st.columns(3)
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

        else:
            st.markdown("""
            <div class='empty-state'>
                <div style='font-size:4rem; animation: floatLogo 3s ease-in-out infinite;'>⚡</div>
                <div style='font-size:1.2rem; color:rgba(255,255,255,0.4); font-weight:600; margin-top:1rem;'>
                    Ready to generate
                </div>
                <div style='font-size:0.9rem; color:rgba(255,255,255,0.25); margin-top:0.5rem;'>
                    Fill in prospect details and click Generate
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 2 — HISTORY
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "history":
    st.markdown("<h2 style='color:white;'>📚 Email History</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.5);'>All previously generated emails</p>",
                unsafe_allow_html=True)

    recent = get_recent_emails(50)

    if not recent:
        st.markdown("""
        <div class='empty-state'>
            <div style='font-size:3rem;'>📭</div>
            <div style='font-size:1.1rem; color:rgba(255,255,255,0.4); margin-top:1rem;'>
                No emails generated yet
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        search = st.text_input("🔍 Search by name or company", placeholder="Type to filter...")
        filtered = [i for i in recent if
                    search.lower() in i['prospect_name'].lower() or
                    search.lower() in i['company_name'].lower()] if search else recent

        st.markdown(f"<p style='color:rgba(255,255,255,0.4);'>{len(filtered)} emails found</p>",
                    unsafe_allow_html=True)

        for item in filtered:
            with st.expander(f"📧 {item['prospect_name']} at {item['company_name']} — {item['created_at'][:10]}"):
                st.markdown(f"**Subject:** {item['subject_line']}")
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); padding:1rem;
                            border-radius:8px; color:rgba(255,255,255,0.8);
                            font-size:0.9rem; line-height:1.8; margin-top:0.5rem;'>
                    {item['email_body']}
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 3 — BATCH
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "batch":
    st.markdown("<h2 style='color:white;'>📊 Batch Email Generator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.5);'>Generate emails for multiple prospects at once</p>",
                unsafe_allow_html=True)

    import pandas as pd

    sample_df = pd.DataFrame({
        "prospect_name": ["John Smith", "Sarah Lee"],
        "company_name": ["Acme Corp", "TechStart"],
        "prospect_role": ["VP Sales", "CEO"],
        "tone": ["friendly", "executive"],
        "company_website": ["https://acme.com", ""],
    })

    st.markdown("<h4 style='color:white;'>📋 Required CSV Format</h4>", unsafe_allow_html=True)
    st.dataframe(sample_df, use_container_width=True)

    st.download_button("⬇️ Download Sample CSV", data=sample_df.to_csv(index=False).encode(),
                       file_name="sample_prospects.csv", mime="text/csv")

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload your prospects CSV", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ["prospect_name", "company_name", "prospect_role", "tone"]
            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                st.error(f"❌ Missing columns: {', '.join(missing)}")
            else:
                st.success(f"✅ Found {len(df)} prospects ready to process")
                st.dataframe(df, use_container_width=True)

                if st.button("⚡ Generate All Emails", use_container_width=True):
                    results = []
                    progress = st.progress(0)
                    status = st.empty()

                    for i, row in df.iterrows():
                        status.markdown(f"""
                        <div class='step-indicator'>
                            <div class='step-dot'></div>
                            Processing {row['prospect_name']} at {row['company_name']}
                            ({i+1}/{len(df)})
                        </div>
                        """, unsafe_allow_html=True)

                        form_data = {
                            "prospect_name": str(row.get("prospect_name", "")),
                            "company_name": str(row.get("company_name", "")),
                            "prospect_role": str(row.get("prospect_role", "")),
                            "tone": str(row.get("tone", "friendly")),
                            "company_website": str(row.get("company_website", "")),
                            "linkedin_summary": str(row.get("linkedin_summary", "")),
                            "additional_notes": str(row.get("additional_notes", "")),
                        }

                        is_valid, error_msg, prospect = validate_prospect_input(form_data)

                        if not is_valid:
                            results.append({
                                "prospect_name": row["prospect_name"],
                                "company_name": row["company_name"],
                                "subject_line": "FAILED",
                                "email_body": f"Error: {error_msg}",
                                "call_to_action": ""
                            })
                            continue

                        try:
                            research = research_company(prospect)
                            system_prompt, user_prompt = build_prompt(prospect, research)
                            raw_response = generate_email(system_prompt, user_prompt)
                            email = parse_email_response(raw_response, prospect_id=prospect.id)
                            save_prospect(prospect)
                            save_email(email)
                            results.append({
                                "prospect_name": prospect.prospect_name,
                                "company_name": prospect.company_name,
                                "subject_line": email.subject_line,
                                "email_body": email.email_body,
                                "call_to_action": email.call_to_action
                            })
                        except Exception as e:
                            results.append({
                                "prospect_name": row["prospect_name"],
                                "company_name": row["company_name"],
                                "subject_line": "FAILED",
                                "email_body": str(e),
                                "call_to_action": ""
                            })

                        progress.progress((i + 1) / len(df))
                        time.sleep(0.5)

                    status.empty()
                    results_df = pd.DataFrame(results)
                    success_count = len([r for r in results if r['subject_line'] != 'FAILED'])
                    st.success(f"✅ Generated {success_count}/{len(df)} emails successfully")
                    st.dataframe(results_df, use_container_width=True)
                    st.download_button("📊 Download All Emails",
                                       data=results_df.to_csv(index=False).encode(),
                                       file_name="generated_emails.csv",
                                       mime="text/csv", use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")


# ════════════════════════════════════════════════════════════
# PAGE 4 — ANALYTICS
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "analytics":
    st.markdown("<h2 style='color:white;'>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)

    import pandas as pd
    recent = get_recent_emails(100)

    if not recent:
        st.markdown("""
        <div class='empty-state'>
            <div style='font-size:3rem;'>📊</div>
            <div style='font-size:1.1rem; color:rgba(255,255,255,0.4); margin-top:1rem;'>
                No data yet — generate some emails first
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = len(recent)
        avg_words = sum(len(r['email_body'].split()) for r in recent) // total

        d1, d2, d3 = st.columns(3)
        for col, (val, label) in zip(
            [d1, d2, d3],
            [(str(total), "Total Emails"),
             (str(avg_words), "Avg Words"),
             (str(len(set(r['company_name'] for r in recent))), "Companies")]
        ):
            with col:
                st.markdown(f"""
                <div class='dashboard-card'>
                    <div class='dashboard-value'>{val}</div>
                    <div class='dashboard-label'>{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin:2rem 0;'></div>", unsafe_allow_html=True)

        df = pd.DataFrame(recent)
        df['date'] = pd.to_datetime(df['created_at']).dt.date

        st.markdown("<h4 style='color:white;'>📅 Emails Generated Over Time</h4>",
                    unsafe_allow_html=True)
        daily = df.groupby('date').size().reset_index(name='count')
        st.bar_chart(daily.set_index('date'), color="#667eea")

        st.markdown("<h4 style='color:white;'>🏢 Top Companies</h4>", unsafe_allow_html=True)
        top_companies = df['company_name'].value_counts().head(10).reset_index()
        top_companies.columns = ['Company', 'Emails']
        st.dataframe(top_companies, use_container_width=True)


# ════════════════════════════════════════════════════════════
# PAGE 5 — ABOUT
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "about":
    st.markdown("<h2 style='color:white;'>👤 About MailCraft AI</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
                border-radius:16px; padding:2rem; margin-bottom:1rem;'>
        <div style='font-size:1.1rem; color:rgba(255,255,255,0.85); line-height:1.8;'>
            <strong style='color:#a78bfa;'>MailCraft AI</strong> is an AI-powered cold email 
            personalization tool built for Sales Development Representatives (SDRs), recruiters, 
            and startup founders who want to send highly personalized outreach at scale.
            <br><br>
            Built with Python, Streamlit, and Groq AI — this tool reduces email writing time 
            from 20 minutes to under 30 seconds while maintaining human-quality output.
        </div>
    </div>

    <div style='background:rgba(102,126,234,0.1); border:1px solid rgba(102,126,234,0.2);
                border-radius:16px; padding:2rem;'>
        <div style='color:white; font-weight:700; font-size:1.1rem; margin-bottom:1rem;'>
            🛠️ Tech Stack
        </div>
        <div style='color:rgba(255,255,255,0.7); line-height:2;'>
            ⚡ <strong style='color:#a78bfa;'>Frontend:</strong> Streamlit<br>
            🐍 <strong style='color:#a78bfa;'>Backend:</strong> Python 3.13<br>
            🤖 <strong style='color:#a78bfa;'>AI:</strong> Groq API × Llama 3.3-70b<br>
            🗄️ <strong style='color:#a78bfa;'>Database:</strong> SQLite<br>
            🔍 <strong style='color:#a78bfa;'>Research:</strong> BeautifulSoup4<br>
            ☁️ <strong style='color:#a78bfa;'>Deployment:</strong> Streamlit Cloud
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:white;'>💬 Feedback</h4>", unsafe_allow_html=True)
    feedback = st.text_area("Share your thoughts or suggestions", placeholder="What would you like to see improved?", height=100)
    if st.button("Send Feedback"):
        if feedback:
            st.success("✅ Thank you for your feedback!")
        else:
            st.warning("Please write something first.")