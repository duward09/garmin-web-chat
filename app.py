import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Garmin AI Coach", page_icon="🏃", layout="centered")

st.title("🏃 Garmin AI Running Coach")
st.caption("Asisten Lari Pribadi — Terkoneksi dengan Garmin MCP & Gemini AI")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    gemini_api_key = st.text_input(
        "Gemini API Key", 
        value=os.getenv("GEMINI_API_KEY", ""), 
        type="password"
    )
    mcp_url = st.text_input(
        "Garmin MCP URL", 
        value=os.getenv("GARMIN_MCP_URL", "http://garminmcp.railway.internal:8000/mcp")
    )

if not gemini_api_key:
    st.info("💡 Masukkan Gemini API Key Anda di sidebar (atau atur di Environment Variables Railway).")
    st.stop()

def fetch_garmin_mcp_data():
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload_call = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_latest_activity",
            "arguments": {}
        }
    }
    try:
        res = requests.post(mcp_url, json=payload_call, headers=headers, timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    try:
        payload_list = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        res_list = requests.post(mcp_url, json=payload_list, headers=headers, timeout=8)
        if res_list.status_code == 200:
            return res_list.json()
    except Exception as e:
        return {"error": f"Gagal terhubung ke MCP: {str(e)}"}
        
    return {"status": "Tidak ada respon dari server MCP"}

def call_gemini_api(prompt, api_key):
    # Memanggil endpoint resmi v1beta Gemini 2.0 Flash via REST HTTP
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    if response.status_code == 200:
        res_data = response.json()
        try:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Format respon Gemini tidak sesuai."
    else:
        return f"Error Google API ({response.status_code}): {response.text}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Halo! Saya Garmin AI Coach Anda. Ada yang bisa saya bantu terkait analisis lari Anda?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input("Tanyakan performa lari Anda..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.spinner("Mengambil data Garmin & menganalisis dengan Gemini..."):
        garmin_data = fetch_garmin_mcp_data()
        
        system_prompt = f"""
        Kamu adalah AI Running & Performance Coach pribadi. Tugasmu adalah menganalisis data lari dari Garmin MCP (seperti Pace min/km, Heart Rate Zone 2, Cadence, dan Jarak).
        Berikan jawaban yang ramah, berbobot, ringkas, mudah dibaca di layar HP, dan berikan evaluasi performa yang motivatif.

        --- DATA GARMIN MCP ---
        {json.dumps(garmin_data, indent=2)}

        --- PERTANYAAN USER ---
        {user_input}
        """

        bot_response = call_gemini_api(system_prompt, gemini_api_key)

    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.chat_message("assistant").write(bot_response)
