import streamlit as st
import time
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

# ── ADVANCED CSS ────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    .logo-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }

    .logo-icon {
        font-size: 3.5rem;
        display: block;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 0 20px #4f46e5);
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

    .card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: rgba(255,255,255,0.9);
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .generate-btn {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 700;
        cursor: pointer;
        letter-spacing: 0.5px;
        box-shadow: 0 8px 32px rgba(102,126,234,0.4);
        transition: all 0.3s ease;
    }

    .generate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(102,126,234,0.6);
    }

    .email-card {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 16px;
        padding: 2rem;
        position: relative;
        overflow: hidden;
    }

    .email-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
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

    .cta-box {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-top: 1rem;
        color: #c4b5fd;
        font-size: 0.9rem;
    }

    .metric-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
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
        transition: width 1s ease;
    }

    .score-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .score-excellent { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
    .score-good { background: rgba(102,126,234,0.2); color: #667eea; border: 1px solid rgba(102,126,234,0.3); }
    .score-fair { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
    .score-poor { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: rgba(255,255,255,0.3);
    }

    .empty-state-icon {
        font-size: 4rem;
        display: block;
        margin-bottom: 1rem;
        filter: grayscale(1) opacity(0.3);
    }

    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        color: rgba(255,255,255,0.7);
        font-size: 0.9rem;
    }

    .step-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.5); }
    }

    .history-item {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .history-item:hover {
        background: rgba(102,126,234,0.1);
        border-color: rgba(102,126,234,0.3);
    }

    .nav-btn {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        color: rgba(255,255,255,0.7);
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        width: 100%;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }

    .nav-btn:hover, .nav-btn-active {
        background: rgba(102,126,234,0.2);
        border-color: rgba(102,126,234,0.4);
        color: white;
    }

    div[data-testid="stForm"] {
        background: transparent;
        border: none;
    }

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
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important;
    }

    .stDownloadButton > button {
        background: rgba(255,255,255,0.08) !important;
        color: rgba(255,255,255,0.8) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
    }

    .stAlert { border-radius: 12px !important; }

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

    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.5);
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(102,126,234,0.3) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ───────────────────────────────────────────
if "current_email" not in st.session_state:
    st.session_state.current_email = None
if "current_prospect" not in st.session_state:
    st.session_state.current_prospect = None
if "page" not in st.session_state:
    st.session_state.page = "generator"
if "generating" not in st.session_state:
    st.session_state.generating = False


# ── QUALITY SCORER ──────────────────────────────────────────
def score_email(email) -> dict:
    score = 0
    feedback = []

    # Word count check
    if 80 <= email.word_count <= 150:
        score += 25
        feedback.append(("✅", "Perfect length (80-150 words)"))
    elif email.word_count < 80:
        score += 10
        feedback.append(("⚠️", "Too short — add more context"))
    else:
        score += 15
        feedback.append(("⚠️", "A bit long — try to trim it"))

    # Subject line check
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

    # CTA check
    if email.call_to_action and len(email.call_to_action) > 10:
        score += 25
        feedback.append(("✅", "Clear call-to-action present"))
    else:
        score += 5
        feedback.append(("❌", "Missing or weak call-to-action"))

    # Spam word check
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

    st.markdown("---")

    st.markdown("""
    <div style='padding: 1rem; background: rgba(102,126,234,0.1); 
                border-radius: 12px; border: 1px solid rgba(102,126,234,0.2);'>
        <div style='color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;'>
            ⚡ Powered by
        </div>
        <div style='color: #a78bfa; font-size: 0.8rem;'>Groq × Llama 3.3-70b</div>
        <div style='color: rgba(255,255,255,0.4); font-size: 0.75rem; margin-top: 0.3rem;'>Free · Fast · Reliable</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 1 — EMAIL GENERATOR
# ════════════════════════════════════════════════════════════
if st.session_state.page == "generator":

    col_input, col_output = st.columns([2, 3], gap="large")

    with col_input:
        st.markdown("""
        <div class='card-title' style='font-size:1.3rem; color:white; font-weight:700; margin-bottom:1.5rem;'>
            📋 Prospect Details
        </div>
        """, unsafe_allow_html=True)

        with st.form("prospect_form", clear_on_submit=False):

            prospect_name = st.text_input("👤 Prospect Name *", placeholder="e.g., Sarah Johnson")
            company_name = st.text_input("🏢 Company Name *", placeholder="e.g., Acme Corp")
            prospect_role = st.text_input("💼 Prospect Role *", placeholder="e.g., VP of Sales")

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

            st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)

            with st.expander("✨ Optional — Improves Personalization"):
                company_website = st.text_input("🌐 Company Website", placeholder="https://acmecorp.com")
                linkedin_summary = st.text_area("🔗 LinkedIn Summary", placeholder="Paste their LinkedIn About section...", height=80)
                additional_notes = st.text_area("📝 Additional Notes", placeholder="e.g., Recently raised Series B...", height=60)

            col_gen, col_regen = st.columns([3, 1])
            with col_gen:
                submitted = st.form_submit_button("⚡ Generate Email", use_container_width=True)
            with col_regen:
                regenerate = st.form_submit_button("🔄", use_container_width=True, help="Regenerate a new version")

    with col_output:
        st.markdown("""
        <div class='card-title' style='font-size:1.3rem; color:white; font-weight:700; margin-bottom:1.5rem;'>
            📧 Generated Email
        </div>
        """, unsafe_allow_html=True)

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
                steps = [
                    "🔍 Researching company intelligence...",
                    "🧠 Engineering your personalized prompt...",
                    "⚡ Generating email with Groq AI...",
                    "✨ Scoring and formatting output...",
                ]

                progress_bar = st.progress(0)
                status_box = st.empty()

                try:
                    for i, step in enumerate(steps[:2]):
                        status_box.markdown(f"""
                        <div class='step-indicator'>
                            <div class='step-dot'></div> {step}
                        </div>
                        """, unsafe_allow_html=True)
                        progress_bar.progress((i + 1) * 20)
                        if i == 0:
                            research = research_company(prospect)
                        else:
                            system_prompt, user_prompt = build_prompt(prospect, research)
                        time.sleep(0.3)

                    status_box.markdown(f"""
                    <div class='step-indicator'>
                        <div class='step-dot'></div> {steps[2]}
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress(60)

                    start_time = time.time()
                    raw_response = generate_email(system_prompt, user_prompt)
                    generation_time_ms = int((time.time() - start_time) * 1000)

                    status_box.markdown(f"""
                    <div class='step-indicator'>
                        <div class='step-dot'></div> {steps[3]}
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress(90)

                    email = parse_email_response(raw_response, prospect_id=prospect.id)
                    email.generation_time_ms = generation_time_ms

                    save_prospect(prospect)
                    save_email(email)

                    st.session_state.current_email = email
                    st.session_state.current_prospect = prospect

                    progress_bar.progress(100)
                    time.sleep(0.3)
                    status_box.empty()
                    progress_bar.empty()

                except Exception as e:
                    progress_bar.empty()
                    status_box.empty()
                    st.error(f"❌ Generation failed: {str(e)}")

        if st.session_state.current_email:
            email = st.session_state.current_email
            prospect = st.session_state.current_prospect
            quality = score_email(email)

            # Metrics row
            m1, m2, m3, m4 = st.columns(4)
            metrics = [
                (str(email.word_count), "Words"),
                (f"{email.generation_time_ms}ms", "Speed"),
                (f"{len(email.subject_line)}", "Subj Len"),
                (f"{quality['score']}", "Quality"),
            ]
            for col, (val, label) in zip([m1, m2, m3, m4], metrics):
                with col:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-value'>{val}</div>
                        <div class='metric-label'>{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

            # Email display
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
                <div class='email-body-text'>{email.email_body}</div>
                {f'<div class="cta-box">🎯 <strong>CTA:</strong> {email.call_to_action}</div>' if email.call_to_action else ''}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)

            # Quality score
            with st.expander(f"⭐ Email Quality Score: {quality['score']}/100 — {quality['grade'][0]}"):
                st.markdown(f"""
                <div class='quality-bar-container'>
                    <div class='quality-bar' style='width:{quality["score"]}%;'></div>
                </div>
                <div style='margin-top:1rem;'></div>
                """, unsafe_allow_html=True)
                for icon, text in quality["feedback"]:
                    st.markdown(f"<div style='color:rgba(255,255,255,0.7); padding:0.3rem 0;'>{icon} {text}</div>", unsafe_allow_html=True)

            # Copy and export buttons
            full_text = f"Subject: {email.subject_line}\n\n{email.email_body}"
            if email.call_to_action:
                full_text += f"\n\n{email.call_to_action}"

            st.code(full_text, language=None)

            b1, b2, b3 = st.columns(3)
            with b1:
                st.download_button(
                    "📊 CSV",
                    data=export_to_csv(prospect, email),
                    file_name=f"email_{prospect.company_name.lower().replace(' ','_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with b2:
                st.download_button(
                    "📄 TXT",
                    data=export_to_txt(prospect, email),
                    file_name=f"email_{prospect.company_name.lower().replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with b3:
                st.download_button(
                    "📋 Copy",
                    data=full_text.encode(),
                    file_name="email.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Download to copy"
                )

        else:
            st.markdown("""
            <div class='empty-state'>
                <span class='empty-state-icon'>⚡</span>
                <div style='font-size:1.2rem; color:rgba(255,255,255,0.4); font-weight:600;'>
                    Ready to generate
                </div>
                <div style='font-size:0.9rem; color:rgba(255,255,255,0.25); margin-top:0.5rem;'>
                    Fill in prospect details and click Generate
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 2 — EMAIL HISTORY
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "history":
    st.markdown("<h2 style='color:white;'>📚 Email History</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.5);'>All previously generated emails</p>", unsafe_allow_html=True)

    recent = get_recent_emails(50)

    if not recent:
        st.markdown("""
        <div class='empty-state'>
            <span class='empty-state-icon'>📭</span>
            <div style='font-size:1.1rem; color:rgba(255,255,255,0.4);'>No emails generated yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:rgba(255,255,255,0.4);'>{len(recent)} emails found</p>", unsafe_allow_html=True)

        for item in recent:
            with st.expander(f"📧 {item['prospect_name']} at {item['company_name']} — {item['created_at'][:10]}"):
                st.markdown(f"**Subject:** {item['subject_line']}")
                st.markdown(f"**Body:**")
                st.markdown(f"""
                <div class='email-body-text' style='background:rgba(255,255,255,0.03); 
                            padding:1rem; border-radius:8px;'>
                    {item['email_body']}
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 3 — BATCH UPLOAD
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "batch":
    st.markdown("<h2 style='color:white;'>📊 Batch Email Generator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.5);'>Upload a CSV to generate emails for multiple prospects at once</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class='card'>
        <div class='card-title'>📋 Required CSV Format</div>
    </div>
    """, unsafe_allow_html=True)

    import pandas as pd
    sample_df = pd.DataFrame({
        "prospect_name": ["John Smith", "Sarah Lee"],
        "company_name": ["Acme Corp", "TechStart"],
        "prospect_role": ["VP Sales", "CEO"],
        "tone": ["friendly", "executive"],
        "company_website": ["https://acme.com", ""],
    })
    st.dataframe(sample_df, use_container_width=True)

    sample_csv = sample_df.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Download Sample CSV",
        data=sample_csv,
        file_name="sample_prospects.csv",
        mime="text/csv"
    )

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
                st.success(f"✅ Found {len(df)} prospects")
                st.dataframe(df, use_container_width=True)

                if st.button("⚡ Generate All Emails", use_container_width=True):
                    results = []
                    progress = st.progress(0)
                    status = st.empty()

                    for i, row in df.iterrows():
                        status.markdown(f"""
                        <div class='step-indicator'>
                            <div class='step-dot'></div>
                            Processing {row['prospect_name']} at {row['company_name']}... ({i+1}/{len(df)})
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
                                "email_body": f"Validation error: {error_msg}",
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
                    progress.progress(100)

                    results_df = pd.DataFrame(results)
                    st.success(f"✅ Generated {len([r for r in results if r['subject_line'] != 'FAILED'])} emails successfully")
                    st.dataframe(results_df, use_container_width=True)

                    st.download_button(
                        "📊 Download All Emails CSV",
                        data=results_df.to_csv(index=False).encode(),
                        file_name="generated_emails.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")