import json
import os
import time
import urllib.error
import urllib.request
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SwiftSOS | Campus Rapid Response", page_icon="🚨", layout="wide")

st.markdown("""
<style>
    :root {
        --ink: #172033;
        --muted: #64748b;
        --line: #e2e8f0;
        --accent: #e11d48;
        --accent-dark: #be123c;
        --surface: #ffffff;
    }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 10% 0%, rgba(244, 63, 94, .09), transparent 34rem),
            #f5f7fb;
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    section.main > div.block-container {
        max-width: 1440px;
        padding: 2rem 2.25rem 3rem;
    }
    h1, h2, h3 { color: var(--ink); letter-spacing: -.025em; }
    h1 { font-size: clamp(2rem, 3.2vw, 2.8rem) !important; }
    h2, h3 { font-weight: 750 !important; }
    [data-testid="stCaptionContainer"] { color: var(--muted); }
    [data-testid="stTabs"] [role="tablist"] {
        gap: .55rem;
        border-bottom: 1px solid var(--line);
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px 10px 0 0;
        padding: .8rem 1rem;
        color: #475569;
        font-weight: 650;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--accent-dark);
        border-bottom-color: var(--accent);
    }
    .stButton > button {
        border-radius: 10px;
        min-height: 2.8rem;
        font-weight: 650;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, .12);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(115deg, #e11d48, #fb4b61);
        border: 0;
        padding: 1rem 1.4rem;
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: .035em;
        box-shadow: 0 8px 22px rgba(225, 29, 72, .24);
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input {
        border-radius: 9px;
        border-color: #d7deea;
        background: var(--surface);
    }
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: 0 5px 18px rgba(15, 23, 42, .045);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-weight: 800; }
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(226, 232, 240, .85);
        border-radius: 12px;
        background: var(--surface);
        padding: .8rem 1rem;
        margin-bottom: .6rem;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"], iframe {
        border-radius: 12px;
        overflow: hidden;
    }
    .sms-box {
        background: linear-gradient(145deg, #172033, #25334b);
        border-left: 4px solid #fb4b61;
        padding: 1.1rem 1.2rem;
        border-radius: 10px;
        font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
        color: #f8fafc;
        line-height: 1.65;
        overflow-wrap: anywhere;
        margin-top: .75rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, .12);
    }
    .first-aid-box {
        background: linear-gradient(145deg, #fffbeb, #fff7d6);
        border: 1px solid #fde68a;
        border-left: 4px solid #eab308;
        padding: 1.1rem 1.2rem;
        border-radius: 10px;
        color: #334155;
        line-height: 1.8;
        margin-top: .9rem;
    }
    @media (max-width: 700px) {
        section.main > div.block-container { padding: 1.25rem 1rem 2rem; }
        [data-testid="stTabs"] button[role="tab"] { padding: .65rem .55rem; }
    }
</style>
""", unsafe_allow_html=True)

if "alerts" not in st.session_state:
    st.session_state.alerts = [
        {"ID": "SOS-102", "Time": "10:14 PM", "Emergency": "Security Threat", "Location": "Zik's Flats Axis", "Lat": 6.8670, "Lon": 7.4083, "Status": "PATROL DISPATCHED"},
        {"ID": "SOS-101", "Time": "09:42 PM", "Emergency": "Medical Emergency", "Location": "Tetfund Hostel", "Lat": 6.8645, "Lon": 7.4120, "Status": "RESOLVED"},
    ]

if "last_sms" not in st.session_state:
    st.session_state.last_sms = None

if "last_emergency_type" not in st.session_state:
    st.session_state.last_emergency_type = None
if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = [
        {"role": "assistant", "content": "👋 I'm **SwiftAI**. Tell me what's happening, and I'll talk it through with you. If someone is in immediate danger, call **112** now."}
    ]

if "demo_logged_in" not in st.session_state:
    st.session_state.demo_logged_in = False

if not st.session_state.demo_logged_in:
    st.markdown(
        """
        <div style="
            max-width: 760px; margin: 3rem auto 1rem; padding: 1.5rem 1.7rem;
            border: 1px solid #e2e8f0; border-radius: 18px;
            background: linear-gradient(115deg, #fff, #fff6f7);
            box-shadow: 0 12px 32px rgba(15,23,42,.07);">
          <div style="font-size:.76rem; font-weight:800; letter-spacing:.14em;
                      text-transform:uppercase; color:#e11d48; margin-bottom:.45rem;">
            Student access
          </div>
          <div style="font-size:2rem; font-weight:850; color:#172033;">
            🚨 SwiftSOS
          </div>
          <div style="margin-top:.4rem; color:#64748b;">
            Enter demo details to continue to the campus response dashboard.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    login_col, _ = st.columns([1.2, 1])
    with login_col:
        st.subheader("Student sign-in")
        st.warning(
            "Demo only — this form does not verify student identity. Use sample data, "
            "not a real registration number or real medical history. Details are kept "
            "only in this active app session, are not saved to a database, and are not "
            "sent to SwiftAI."
        )
        with st.form("demo_student_login"):
            student_reg_no = st.text_input(
                "Student registration number",
                placeholder="e.g., DEMO/2026/001",
            )
            medical_history = st.text_area(
                "Medical history",
                placeholder="For demo data: allergies, conditions, medications, or relevant emergency notes",
                height=130,
            )
            login_submitted = st.form_submit_button(
                "Continue to SwiftSOS",
                type="primary",
                use_container_width=True,
            )

        if login_submitted:
            if not student_reg_no.strip() or not medical_history.strip():
                st.error("Enter both a registration number and medical history to continue.")
            else:
                st.session_state.student_profile = {
                    "registration_number": student_reg_no.strip(),
                    "medical_history": medical_history.strip(),
                }
                st.session_state.demo_logged_in = True
                st.rerun()
    st.stop()

def end_demo_session():
    st.session_state.pop("student_profile", None)
    st.session_state.demo_logged_in = False

st.markdown(
    """
    <div style="
        padding: 1.35rem 1.6rem; margin-bottom: 1.5rem;
        border: 1px solid rgba(226,232,240,.9); border-radius: 18px;
        background: linear-gradient(115deg, rgba(255,255,255,.98), rgba(255,246,247,.96));
        box-shadow: 0 12px 32px rgba(15,23,42,.06);">
      <div style="font-size:.76rem; font-weight:800; letter-spacing:.14em;
                  text-transform:uppercase; color:#e11d48; margin-bottom:.45rem;">
        Campus rapid response
      </div>
      <div style="font-size:clamp(1.7rem,3vw,2.5rem); font-weight:850;
                  line-height:1.15; letter-spacing:-.04em; color:#172033;">
        🚨 SwiftSOS
        <span style="font-size:.52em; font-weight:650; letter-spacing:-.01em; color:#475569;">
          Emergency coordination, made simple
        </span>
      </div>
      <div style="margin-top:.65rem; color:#64748b; font-size:.94rem;">
        SOS alerts · Campus dispatch map · First-aid guidance
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

session_info, logout_column = st.columns([5, 1])
session_info.caption("Demo student session · Profile details are not sent to SwiftAI.")
logout_column.button(
    "Sign out",
    use_container_width=True,
    on_click=end_demo_session,
)

tab1, tab2, tab3 = st.tabs(["📱 Student SOS Trigger", "🛡️ Security Command Center", "📞 Verified Campus Responders"])

with tab1:
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.subheader("Need Immediate Help?")
        emergency_type = st.selectbox("1. Select Emergency Type", [
            "Medical Emergency",
            "Security / Armed Threat",
            "Harassment / Assault",
            "Fire Outbreak",
            "Campus Road Accident"
        ])
        landmark = st.selectbox("2. Location (Type to Search Remote/Campus Spots or Use Live GPS)", [
            "Bello Hostel",
            "📍 Auto-Detect Live Satellite GPS (Any Remote / Off-Campus Spot)",
            "Hilltop (Off-Campus Lodges)",
            "Behind Flat (Off-Campus)",
            "Odenigwe Axis",
            "Odim Gate / Green House",
            "Mbanefo Hostel",
            "Akintola Hostel",
            "Okpara Hostel",
            "Alvan Ikoku Hostel",
            "Franco Hostel",
            "Zik's Flats Axis",
            "Nnamdi Azikiwe Library",
            "SUB (Student Union Building)",
            "Carver Building / Arts Complex",
            "Faculty of Physical Sciences",
            "Faculty of Engineering",
            "Presidential Road Gate",
            "New Market / Beach Junction"
        ])

        coords = {
            "Bello Hostel": (6.8690, 7.4110),
            "📍 Auto-Detect Live Satellite GPS (Any Remote / Off-Campus Spot)": (6.8725, 7.4060),
            "Hilltop (Off-Campus Lodges)": (6.8760, 7.4035),
            "Behind Flat (Off-Campus)": (6.8615, 7.4045),
            "Odenigwe Axis": (6.8745, 7.4125),
            "Odim Gate / Green House": (6.8715, 7.4040),
            "Mbanefo Hostel": (6.8685, 7.4118),
            "Akintola Hostel": (6.8678, 7.4105),
            "Okpara Hostel": (6.8695, 7.4102),
            "Alvan Ikoku Hostel": (6.8662, 7.4128),
            "Franco Hostel": (6.8645, 7.4120),
            "Zik's Flats Axis": (6.8670, 7.4083),
            "Nnamdi Azikiwe Library": (6.8682, 7.4068),
            "SUB (Student Union Building)": (6.8665, 7.4095),
            "Carver Building / Arts Complex": (6.8658, 7.4075),
            "Faculty of Physical Sciences": (6.8650, 7.4055),
            "Faculty of Engineering": (6.8638, 7.4062),
            "Presidential Road Gate": (6.8620, 7.4140),
            "New Market / Beach Junction": (6.8585, 7.4150),
        }

        extra_note = st.text_input("3. Optional Custom Spot / Note (e.g., 'Hilltop Lodge, Room 12')", placeholder="Leave blank for silent 1-tap SOS...")

        if st.button("🆘 TRIGGER SOS", type="primary", use_container_width=True):
            lat, lon = coords[landmark]
            alert_id = f"SOS-{100 + len(st.session_state.alerts) + 1}"
            now_str = datetime.now().strftime("%I:%M %p")
            display_loc = extra_note if ("Auto-Detect" in landmark and extra_note) else landmark

            st.session_state.alerts.insert(0, {
                "ID": alert_id,
                "Time": now_str,
                "Emergency": emergency_type,
                "Location": display_loc,
                "Lat": lat,
                "Lon": lon,
                "Status": "ACTIVE SOS"
            })

            if emergency_type == "Medical Emergency":
                responder_unit = "UNN Medical Centre (A/E Ambulance)"
            elif emergency_type == "Fire Outbreak":
                responder_unit = "Enugu State Fire Service (Nsukka)"
            else:
                responder_unit = "UNN Security Q.I.U"

            note_txt = f" | Note: {extra_note}" if extra_note else ""
            st.session_state.last_sms = (
                f"[SWIFTSOS ALERT • {alert_id}] {emergency_type.upper()} reported at {display_loc} ({now_str}). "
                f"GPS: https://google.com{lat},{lon}{note_txt} — Dispatched to {responder_unit} & 3 Trusted Contacts."
            )
            alert_banner = st.empty()
            alert_banner.success("🚨 EMERGENCY BEACON ACTIVATED! Live coordinates transmitted to Responder Command & Trusted Contacts.")
            time.sleep(1.2)
            alert_banner.empty()

            st.session_state.last_emergency_type = emergency_type

    with col2:
        st.subheader("📡 Live Transmission & Golden-5-Min Guide")
        if st.session_state.last_sms:
            st.success("✅ SMS & Data Payload Delivered (< 2.4s)")
            st.markdown(f"<div class='sms-box'>{st.session_state.last_sms}</div>", unsafe_allow_html=True)

            etype = st.session_state.last_emergency_type
            if etype == "Medical Emergency":
                guide_html = """
                <b>🩺 OFFLINE FIRST-AID GUIDE (While Medical Team Arrives in 3–5 Mins):</b><br><br>
                1. <b>Sit the person upright</b> — Do NOT lay them flat on their back.<br>
                2. <b>Loosen tight clothing</b> around the neck and chest.<br>
                3. <b>Guide slow, steady breaths</b> (4s in, 6s out) to reduce panic.<br>
                4. <b>Clear bystanders back</b> so fresh air circulates freely.
                """
            elif etype == "Fire Outbreak":
                guide_html = """
                <b>🔥 OFFLINE FIRE SAFETY GUIDE (While Fire Service En Route):</b><br><br>
                1. <b>Stay low below smoke</b> and cover nose/mouth with damp cloth.<br>
                2. <b>Evacuate immediately</b> via nearest staircase — never use elevators.
                """
            elif etype == "Campus Road Accident":
                guide_html = """
                <b>🚑 OFFLINE TRAUMA FIRST-AID (While Ambulance En Route):</b><br><br>
                1. <b>Apply firm, direct pressure</b> on any bleeding with a clean cloth.<br>
                2. <b>Do NOT move the victim</b> unnecessarily if neck/back injury is suspected.
                """
            else:
                guide_html = """
                <b>🛡️ OFFLINE SAFETY PROTOCOL (While Q.I.U Patrol En Route):</b><br><br>
                1. <b>Move to a safe, well-lit area</b> or lock doors immediately.<br>
                2. <b>Keep your phone on silent</b> if hiding from an active threat.
                """
            st.markdown(f"<div class='first-aid-box'>{guide_html}</div>", unsafe_allow_html=True)
        else:
            st.info("Tap the red SOS button to simulate an instant emergency dispatch, SMS payload, and offline bystander First-Aid Guide.")
        st.divider()
        st.subheader("🤖 SwiftAI — Emergency Chat")
        chat_box = st.container(height=240)
        for msg in st.session_state.ai_messages:
            with chat_box.chat_message(msg["role"]):
                st.markdown(msg["content"])

        with st.form("swiftai_chat_form", clear_on_submit=True):
            c_in, c_btn = st.columns([4, 1])
            user_prompt = c_in.text_input("Message", placeholder="Ask SwiftAI (e.g., 'asthma no inhaler', 'bleeding')...", label_visibility="collapsed")
            submitted = c_btn.form_submit_button("Send", use_container_width=True)

        if submitted and user_prompt.strip():
            prompt = user_prompt.strip()
            st.session_state.ai_messages.append({"role": "user", "content": prompt})

            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                reply = (
                    "I can't reach the conversational AI yet because `GEMINI_API_KEY` "
                    "isn't configured. Set that environment variable and restart the app "
                    "to enable interactive replies. If this is an emergency, call **112**."
                )
            else:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-3.5-flash-lite:generateContent?key={api_key}"
                )
                conversation = [
                    {
                        "role": "user" if message["role"] == "user" else "model",
                        "parts": [{"text": message["content"]}],
                    }
                    for message in st.session_state.ai_messages
                    if message["role"] in ("user", "assistant")
                    and not (
                        message["role"] == "assistant"
                        and message["content"].startswith("👋 I'm **SwiftAI**.")
                    )
                ][-12:]
                if conversation and conversation[0]["role"] == "model":
                    conversation = conversation[1:]

                payload = json.dumps({
                    "systemInstruction": {
                        "parts": [{
                            "text": (
                                "You are SwiftAI, a warm, calm, conversational emergency "
                                "first-aid guide for a student. Have a real back-and-forth "
                                "conversation and use the full conversation history. Respond "
                                "naturally to greetings. Ask one short, relevant follow-up "
                                "question at a time when you need more information, and adapt "
                                "your next response to the answer; do not give the same generic "
                                "steps to every message. Give clear, brief, safe first-aid "
                                "guidance when appropriate. For severe or life-threatening "
                                "symptoms, tell them to call 112 or get emergency medical help "
                                "immediately. Do not diagnose, prescribe medication, or claim "
                                "that help has been dispatched."
                            )
                        }]
                    },
                    "contents": conversation,
                }).encode("utf-8")
                request = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(request, timeout=15) as response:
                        data = json.loads(response.read().decode("utf-8"))
                    cloud_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    reply = cloud_text
                except urllib.error.HTTPError as error:
                    if error.code == 404:
                        reply = (
                            "The Gemini model or API endpoint isn't available for this "
                            "request (HTTP 404). Check that the selected model is enabled "
                            "for this API key. If this is an emergency, call **112**."
                        )
                    else:
                        reply = (
                            f"I couldn't get a reply from the AI service (HTTP {error.code}). "
                            "Check the Gemini API key and its access, then try again. "
                            "If this is an emergency, call **112**."
                        )
                except (urllib.error.URLError, TimeoutError):
                    reply = (
                        "I couldn't connect to the AI service just now. Please check your "
                        "internet connection and try again. If this is an emergency, call **112**."
                    )
                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                    reply = (
                        "The AI service returned an unreadable response, so I couldn't "
                        "answer. Please try again. If this is an emergency, call **112**."
                    )

            st.session_state.ai_messages.append({"role": "assistant", "content": reply})
            st.rerun()
with tab2:
    active_count = sum(1 for a in st.session_state.alerts if a["Status"] == "ACTIVE SOS")
    disp_count = sum(1 for a in st.session_state.alerts if a["Status"] == "PATROL DISPATCHED")
    m1, m2, m3 = st.columns(3)
    m1.metric("🔴 Active SOS Alerts", active_count)
    m2.metric("🟠 Patrols En Route", disp_count)
    m3.metric("⚡ Avg Dispatch Time", "1m 45s")

    st.subheader("Live Campus Dispatch Map")
    m = folium.Map(location=[6.8668, 7.4085], zoom_start=15)
    for alert in st.session_state.alerts:
        color = "red" if alert["Status"] == "ACTIVE SOS" else ("orange" if alert["Status"] == "PATROL DISPATCHED" else "green")
        folium.Marker(
            [alert["Lat"], alert["Lon"]],
            popup=f"<b>{alert['ID']}: {alert['Emergency']}</b><br>{alert['Location']}<br>Status: {alert['Status']}",
            tooltip=f"🚨 {alert['ID']} — {alert['Emergency']} ({alert['Status']})",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=1000, height=380)

    st.subheader("🎛️ Responder Action Controls")
    active_ids = [a["ID"] for a in st.session_state.alerts if a["Status"] != "RESOLVED"]
    if active_ids:
        c1, c2, c3 = st.columns([1.5, 1.5, 1])
        selected_id = c1.selectbox("Select Alert ID", active_ids)
        new_status = c2.selectbox("Update Status", ["PATROL DISPATCHED", "RESOLVED"])
        if c3.button("Update Dispatch Status", use_container_width=True):
            for alert in st.session_state.alerts:
                if alert["ID"] == selected_id:
                    alert["Status"] = new_status
            st.rerun()

    st.dataframe(pd.DataFrame(st.session_state.alerts), use_container_width=True)

with tab3:
    st.subheader("📞 Verified UNN & Nsukka Quick-Response Directory")
    st.caption("Official emergency lines sourced from UNN Security, UNN Medical Centre, and Nsukka Fire Station.")
    responders = pd.DataFrame([

        {"Unit": "UNN Security Q.I.U", "Coverage": "Rapid Campus Patrol", "Hotlines": "08037517228", "Avg ETA": "3-5 mins"},
        {"Unit": "UNN Security Duty Room", "Coverage": "Hostels & Gates", "Hotlines": "07030395891", "Avg ETA": "3-6 mins"},
        {"Unit": "UNN Medical Centre A/E", "Coverage": "Campus Ambulance", "Hotlines": "07036885702", "Avg ETA": "5-8 mins"},
        {"Unit": "Nsukka Fire Service", "Coverage": "Fire & Rescue", "Hotlines": "08068079367", "Avg ETA": "6-10 mins"},
        {"Unit": "National Emergency Line", "Coverage": "Police, Fire & Medical", "Hotlines": "112", "Avg ETA": "24/7 Dispatch"}
    ])
    st.table(responders)
