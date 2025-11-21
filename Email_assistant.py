import streamlit as st
from groq import Groq
import json
import os

# --- Page Config ---
st.set_page_config(
    page_title="Llama 3 Email Responder",
    page_icon="🦙",
    layout="centered"
)

# --- Logic to handle API Key ---
def get_api_key():
    # 1. Try to get from Streamlit Secrets
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    # 2. Fallback to Environment Variable
    elif os.environ.get("GROQ_API_KEY"):
        return os.environ.get("GROQ_API_KEY")
    return None

# --- Sidebar: Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Attempt to load key
    api_key = get_api_key()

    if api_key:
        st.success("✅ API Key loaded securely")
    else:
        # Only show input if key wasn't found in secrets
        api_key = st.text_input("Enter Groq API Key", type="password")
        st.caption("To save permanently, add `GROQ_API_KEY` to `.streamlit/secrets.toml`")
        st.caption("Get your key at [console.groq.com](https://console.groq.com/)")
    
    st.markdown("---")
    st.write("**Model:** Llama 3 8B (Instant)")

# --- Main UI ---
st.title("🦙 AI Email Responder")
st.markdown("Instantly analyze emails using **Groq + Llama 3**.")

# Input Area
email_input = st.text_area("Paste Incoming Email Here:", height=200, placeholder="Dear Team, I am writing to inquire about...")

# Tone Selection
selected_tone = st.radio(
    "Target Tone:",
    ["Auto-detect", "Formal", "Friendly", "Persuasive"],
    horizontal=True
)

generate_btn = st.button("✨ Generate Reply", type="primary")

# --- Logic ---
if generate_btn:
    if not api_key:
        st.error("Missing API Key. Please add it to .streamlit/secrets.toml or enter it in the sidebar.")
    elif not email_input.strip():
        st.warning("Please paste an email to analyze.")
    else:
        try:
            client = Groq(api_key=api_key)

            with st.spinner("Consulting Llama 3..."):
                tone_instruction = f"Use a {selected_tone} tone." if selected_tone != "Auto-detect" else "Determine the best tone (Formal, Friendly, or Persuasive)."
                
                # System Prompt strictly enforcing JSON
                system_prompt = f"""
                You are an expert email assistant. 
                1. Detect the intent (Inquiry, Complaint, Offer, or Information).
                2. {tone_instruction}
                3. Draft a professional reply.
                
                Output MUST be a valid JSON object with these keys: "intent", "tone", "reply".
                Do not include any text outside the JSON object.
                """

                # API Call
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": email_input}
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )

                response_content = completion.choices[0].message.content
                
                # Parse JSON
                try:
                    data = json.loads(response_content)
                    
                    # Store in session state
                    st.session_state['generated_reply'] = data.get("reply", "")
                    st.session_state['intent'] = data.get("intent", "Unknown")
                    st.session_state['tone'] = data.get("tone", "Professional")
                    st.session_state['has_generated'] = True
                    
                except json.JSONDecodeError:
                    st.error("Failed to parse Llama 3 response. Please try again.")
                    st.caption(f"Raw output: {response_content}")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- Results Display ---
if st.session_state.get('has_generated'):
    st.markdown("---")
    
    # Top Row: Metrics
    col1, col2 = st.columns(2)
    
    intent = st.session_state.get('intent', 'General')
    intent_color = {
        "Inquiry": "blue",
        "Complaint": "red",
        "Offer": "green",
        "Information": "orange"
    }.get(intent, "gray")
    
    with col1:
        st.markdown(f"**Detected Intent:**")
        st.markdown(f":{intent_color}[{intent}]")
        
    with col2:
        st.markdown(f"**Suggested Tone:**")
        st.markdown(f"_{st.session_state.get('tone', 'Professional')}_")

    # Editable Draft Box
    st.markdown("### ✍️ Draft Reply")
    final_reply = st.text_area(
        "Edit your reply:",
        value=st.session_state.get('generated_reply', ''),
        height=300
    )
    
    if st.button("Confirm & Copy"):
        st.toast("Ready to copy! (Use Ctrl+C / Cmd+C)", icon="✅")