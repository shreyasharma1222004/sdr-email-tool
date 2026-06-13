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
    page_title="SDR Email Generator",
    page_icon="✉️",
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
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .email-output {
        background-color: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 1.5rem;
        border-radius: 0 8px 8px 0;
        font-family: 'Georgia', serif;
        line-height: 1.8;
    }
    .subject-box {
        background-color: #e3f2fd;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #1a1a2e;
        color: white;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✉️ SDR Email Generator</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Generate personalized cold emails in seconds using AI</div>',
    unsafe_allow_html=True
)
st.divider()

col_input, col_output = st.columns([2, 3], gap="large")

with col_input:
    st.subheader("📋 Prospect Details")

    with st.form("prospect_form", clear_on_submit=False):

        st.markdown("**Required Information**")

        prospect_name = st.text_input(
            "Prospect Name *",
            placeholder="e.g., Sarah Johnson",
        )

        company_name = st.text_input(
            "Company Name *",
            placeholder="e.g., Acme Corp",
        )

        prospect_role = st.text_input(
            "Prospect's Role *",
            placeholder="e.g., VP of Sales",
        )

        tone = st.selectbox(
            "Email Tone *",
            options=VALID_TONES,
            format_func=lambda x: x.capitalize(),
        )

        st.divider()

        st.markdown("**Optional (Improves Personalization)**")

        company_website = st.text_input(
            "Company Website",
            placeholder="https://acmecorp.com",
        )

        linkedin_summary = st.text_area(
            "LinkedIn Summary",
            placeholder="Paste the prospect's LinkedIn About section...",
            height=100,
        )

        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="e.g., They recently raised Series B...",
            height=80,
        )

        submitted = st.form_submit_button(
            "⚡ Generate Email",
            use_container_width=True
        )

with col_output:
    st.subheader("📧 Generated Email")

    if "current_email" not in st.session_state:
        st.session_state.current_email = None
    if "current_prospect" not in st.session_state:
        st.session_state.current_prospect = None

    if submitted:
        form_data = {
            "prospect_name": prospect_name,
            "company_name": company_name,
            "prospect_role": prospect_role,
            "tone": tone,
            "company_website": company_website,
            "linkedin_summary": linkedin_summary,
            "additional_notes": additional_notes,
        }

        is_valid, error_msg, prospect = validate_prospect_input(form_data)

        if not is_valid:
            st.error(f"⚠️ Please fix these issues:\n{error_msg}")
        else:
            progress_bar = st.progress(0, text="Starting...")
            status = st.empty()

            try:
                status.info("🔍 Researching company...")
                progress_bar.progress(20, text="Researching company...")
                research = research_company(prospect)

                if research.research_successful:
                    status.success("✅ Found company information!")
                else:
                    status.info("ℹ️ Proceeding without website research")

                progress_bar.progress(40, text="Building personalized prompt...")
                system_prompt, user_prompt = build_prompt(prospect, research)

                status.info("🤖 Generating email with AI...")
                progress_bar.progress(60, text="AI is writing your email...")

                start_time = time.time()
                raw_response = generate_email(system_prompt, user_prompt)
                generation_time_ms = int((time.time() - start_time) * 1000)

                progress_bar.progress(80, text="Formatting output...")
                email = parse_email_response(raw_response, prospect_id=prospect.id)
                email.generation_time_ms = generation_time_ms

                save_prospect(prospect)
                save_email(email)

                st.session_state.current_email = email
                st.session_state.current_prospect = prospect

                progress_bar.progress(100, text="Done!")
                status.empty()
                progress_bar.empty()

            except Exception as e:
                progress_bar.empty()
                status.empty()
                logger.error(f"Generation failed: {e}", exc_info=True)
                st.error(
                    f"❌ Generation failed: {str(e)}\n\n"
                    "Check your API key in the .env file."
                )

    if st.session_state.current_email:
        email = st.session_state.current_email
        prospect = st.session_state.current_prospect

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Word Count", email.word_count)
        with m2:
            st.metric("Gen Time", f"{email.generation_time_ms}ms")
        with m3:
            st.metric("Subject Length", f"{len(email.subject_line)} chars")

        st.markdown("---")

        st.markdown("**📌 Subject Line**")
        st.markdown(f'<div class="subject-box">{email.subject_line}</div>',
                    unsafe_allow_html=True)

        st.markdown("**📝 Email Body**")
        st.markdown(f'<div class="email-output">{email.email_body}</div>',
                    unsafe_allow_html=True)

        if email.call_to_action:
            st.markdown("**🎯 Call to Action**")
            st.info(email.call_to_action)

        st.markdown("---")

        full_email_text = f"Subject: {email.subject_line}\n\n{email.email_body}"
        st.code(full_email_text, language=None)

        btn1, btn2 = st.columns(2)

        with btn1:
            csv_data = export_to_csv(prospect, email)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"email_{prospect.company_name.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

        with btn2:
            txt_data = export_to_txt(prospect, email)
            st.download_button(
                label="📄 Download TXT",
                data=txt_data,
                file_name=f"email_{prospect.company_name.lower().replace(' ', '_')}.txt",
                mime="text/plain",
            )

    else:
        st.markdown("""
        <div style='text-align: center; padding: 3rem; color: #888;
                    border: 2px dashed #ddd; border-radius: 12px;'>
            <div style='font-size: 3rem;'>✉️</div>
            <div style='font-size: 1.2rem; margin-top: 1rem;'>
                Fill in prospect details and click Generate
            </div>
            <div style='font-size: 0.9rem; margin-top: 0.5rem; color: #aaa;'>
                Your personalized email will appear here
            </div>
        </div>
        """, unsafe_allow_html=True)

with st.sidebar:
    st.subheader("📚 Recent Emails")

    recent = get_recent_emails(5)

    if recent:
        for item in recent:
            with st.expander(f"📧 {item['company_name']} — {item['prospect_name']}"):
                st.write(f"**Subject:** {item['subject_line']}")
                st.write(f"**Generated:** {item['created_at'][:10]}")
                st.write(item['email_body'][:150] + "...")
    else:
        st.info("No emails generated yet.")

    st.divider()
    st.markdown("**About This Tool**")
    st.markdown("""
    - 🤖 Powered by Groq (Free)
    - ⚡ Results in seconds
    - 📊 All emails saved locally
    - 🔒 Your data stays on your machine
    """)