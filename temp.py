import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="Social Insight Engine v2", layout="wide")
st.title("🎥 Social Insight Engine: Multi-Media")

if "post_history" not in st.session_state:
    st.session_state.post_history = []

# --- SIDEBAR: API SETUP ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.header("🏢 Industry Context")
    # This is the new input field
    industry_context = st.text_area(
        "Describe your niche & goal:", 
        placeholder="e.g., I am a luxury travel creator aiming for high-ticket bookings. My audience is 30-50 year old professionals.",
        help="The more specific you are, the less 'generic' the advice will be."
    )
    
    if st.button("Clear History"):
        st.session_state.post_history = []
        st.rerun()

# --- FILE UPLOADS ---
col1, col2 = st.columns(2)
with col1:
    image_files = st.file_uploader("📸 Upload Analytics Screenshots", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
with col2:
    video_file = st.file_uploader("🎬 Upload the Post Video (Optional)", type=["mp4", "mov", "avi"])

if st.button("🚀 Run Deep Analysis"):
    prompt = f"""
        You are a Top 1% Viral Content Strategist and Behavioral Psychologist. You charge $10,000/month for your advice.
        INDUSTRY CONTEXT: {industry_context if industry_context else 'General Content Creation'}

        I am providing a video file AND analytics screenshots. Do not hold back. I need a ruthless, high-level breakdown of why this performed the way it did, followed by a specific blueprint for my NEXT post.

        1. ## 🩸 The Bleed Point (Retention Audit):
           - Look at the retention graph. At what EXACT second did the steepest drop-off occur? 
           - Cross-reference that timestamp with the video. What was the 'Visual Sin' or 'Audio Lull' that killed the pacing? Be brutally honest. Was the frame stagnant? Did I repeat myself?

        2. ## 🧠 The 'Friction' Report:
           - Grade the first 3 seconds out of 10. Did it create an undeniable 'Curiosity Gap'? 
           - Look at the audience demographic data in the screenshots. Did this content actually resonate with the intended age group/gender for my industry?

        3. ## 🔮 Blueprint for the NEXT Post (Do This Next):
           Based strictly on the data of what failed and what worked in these assets, build my next video:
           - 🎯 **The Concept:** What specific topic should I cover next that leans into my core audience's actual interests?
           - 🪝 **3 Word-for-Word Text Hooks:** Give me three highly aggressive, psychologically triggering text hooks for the first frame. They must be thumb-stopping and NOT generic.
           - 🎬 **1 Visual Hook:** What EXACTLY should be happening on screen during the first 3 seconds to match those text hooks? (e.g., "Pouring coffee while the text pops up", "Walking quickly toward the camera").
           - 🗣️ **The 'Anti-Drop' CTA:** Give me a frictionless Call-To-Action that feels natural, not salesy.
        """
    if not api_key:
        st.error("Please enter your API Key!")
    elif not image_files and not video_file:
        st.warning("Upload screenshots or a video first.")
    else:
        genai.configure(api_key=api_key)
        # 1. Use the most stable 2026 model
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        
        content_to_send = [prompt]

        with st.spinner("AI is processing your media..."):
            try:
                # Add Images
                if image_files:
                    for f in image_files:
                        content_to_send.append(Image.open(f))

                # Add Video with a "Health Check"
                if video_file:
                    with open("temp_vid.mp4", "wb") as f:
                        f.write(video_file.getbuffer())
                    
                    gemini_file = genai.upload_file(path="temp_vid.mp4")
                    
                    # 2. Wait longer and check for 'FAILED' state
                    while gemini_file.state.name == "PROCESSING":
                        time.sleep(3) # Wait 3 seconds instead of 2
                        gemini_file = genai.get_file(gemini_file.name)
                    
                    if gemini_file.state.name == "FAILED":
                        st.error("Video processing failed. Try a shorter clip.")
                    else:
                        content_to_send.append(gemini_file)

                # 3. Call with Safety Settings (prevents gRPC 403/Safety errors)
                response = model.generate_content(
                    content_to_send,
                    safety_settings={
                        'HATE': 'BLOCK_NONE',
                        'HARASSMENT': 'BLOCK_NONE',
                        'SEXUAL': 'BLOCK_NONE',
                        'DANGEROUS': 'BLOCK_NONE'
                    }
                )
                
                st.session_state.post_history.append({
                    "report": response.text,
                    "time": time.strftime("%I:%M %p")
                })
                st.rerun() # Refresh to show the new report immediately

            except Exception as e:
                # This catches that specific gRPC error and makes it readable
                st.error(f"⚠️ Connection Error: {str(e)}")
                st.info("Tip: Try uploading just the screenshots first to see if it's a video size issue.")

# --- DISPLAY HISTORY ---
if st.session_state.post_history:
    st.divider()
    st.subheader("📊 Past Analyses")
    for item in reversed(st.session_state.post_history):
        # We use .get() so if 'time' or 'timestamp' is missing, it doesn't crash
        report_time = item.get("time") or item.get("timestamp") or "Unknown Time"
        
        with st.expander(f"Report - {report_time}", expanded=True):
            st.markdown(item.get("report", "No report content found."))