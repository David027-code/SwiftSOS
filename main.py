import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SwiftSOS | Campus Rapid Response", page_icon="🚨", layout="wide")

# Custom UI/UX Styling
st.markdown("""
<style>
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #d90429, #ef233c);
        border: none;
        padding: 18px 24px;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 1px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(239, 35, 60, 0.45);
    }
    .sms-box {
        background-color: #1e293b;
        border-left: 5px solid #ef233c;
        padding: 16px;
        border-radius: 8px;
        font-family: monospace;
        color: #f8fafc;
        margin-top: 12px;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 14px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

if "alerts" not in st.session_state:
    st.session_state.alerts = [
        {"ID": "SOS-102", "Time": "10:14 PM", "Emergency": "Security Threat", "Location": "Zik's Flats Axis", "Lat": 6.8670, "Lon": 7.4083, "Status": "PATROL DISPATCHED"},
        {"ID": "SOS-101", "Time": "09:42 PM", "Emergency": "Medical Emergency", "Location": "Franco Hostel", "Lat": 6.8645, "Lon": 7.4120, "Status": "RESOLVED"},
    ]

if "last_sms" not in st.session_state:
    st.session_state.last_sms = None

st.title("🚨 SwiftSOS — Rapid Campus Emergency Response")
st.caption("Built by Team Quad-Core Coders • Auto-GPS + Offline SMS Fallback")

tab1, tab2, tab3 = st.tabs(["📱 Student SOS Trigger", "🛡️ Security Command Center", "📞 Verified Campus Responders"])

with tab1:
    col1, col2 = st.columns([1.3, 1])
    
    with col1:
        st.subheader("Need Immediate Help?")
        emergency_type = st.selectbox("1. Select Emergency Type", [
            "Security / Armed Threat",
            "Medical Emergency",
            "Harassment / Assault",
            "Fire Outbreak",
            "Campus Road Accident"
        ])
        
        landmark = st.selectbox("2. Nearest Campus Landmark (Auto-GPS + Fallback)", [
            "Nnamdi Azikiwe Library",
            "SUB (Student Union Building)",
            "Zik's Flats Axis",
            "Franco Hostel",
            "Bello Hostel",
            "Faculty of Physical Sciences",
            "Odim Gate",
            "Presidential Road Gate"
        ])
        
        extra_note = st.text_input("3. Optional Quick Note (e.g., '2 people injured', 'Room 204')", placeholder="Leave blank for silent 1-tap SOS...")

        coords = {
            "Nnamdi Azikiwe Library": (6.8682, 7.4068),
            "SUB (Student Union Building)": (6.8665, 7.4095),
            "Zik's Flats Axis": (6.8670, 7.4083),
            "Franco Hostel": (6.8645, 7.4120),
            "Bello Hostel": (6.8690, 7.4110),
            "Faculty of Physical Sciences": (6.8650, 7.4055),
            "Odim Gate": (6.8715, 7.4040),
            "Presidential Road Gate": (6.8620, 7.4140),
        }

        if st.button("🆘 TRIGGER INSTANT SOS", type="primary", use_container_width=True):
            lat, lon = coords[landmark]
            alert_id = f"SOS-{100 + len(st.session_state.alerts) + 1}"
            now_str = datetime.now().strftime("%I:%M %p")
            
            st.session_state.alerts.insert(0, {
                "ID": alert_id,
                "Time": now_str,
                "Emergency": emergency_type,
                "Location": landmark,
                "Lat": lat,
                "Lon": lon,
                "Status": "ACTIVE SOS"
            })
            
            note_txt = f" | Note: {extra_note}" if extra_note else ""
            st.session_state.last_sms = (
                f"[SWIFTSOS ALERT • {alert_id}] {emergency_type.upper()} reported at {landmark} ({now_str}). "
                f"GPS: https://google.com{lat},{lon}{note_txt} — Dispatched to Campus Security & 3 Trusted Contacts."
            )
            st.error("🚨 EMERGENCY BEACON ACTIVATED! Live coordinates transmitted to Security Command & Trusted Contacts.")

    with col2:
        st.subheader("📡 Live Transmission Preview")
        if st.session_state.last_sms:
            st.success("✅ SMS & Data Payload Delivered (< 2.4s)")
            st.markdown(f"<div class='sms-box'>{st.session_state.last_sms}</div>", unsafe_allow_html=True)
        else:
            st.info("Tap the red SOS button to simulate an instant emergency dispatch and view the automated SMS payload.")

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
            for a in st.session_state.alerts:
                if a["ID"] == selected_id:
                    a["Status"] = new_status
            st.rerun()

    st.dataframe(pd.DataFrame(st.session_state.alerts), use_container_width=True)

with tab3:
    st.subheader("📞 Verified University Quick-Response Directory")
    st.caption("Update these numbers with the verified campus contacts collected by your team.")
    responders = pd.DataFrame([
        {"Unit": "University Security Control Room", "Coverage": "All Hostels & Academic Areas", "Hotlines": "+234-XXX-XXX-XXXX (Update)", "Avg ETA": "3–5 mins"},
        {"Unit": "University Medical Centre (Emergency)", "Coverage": "Ambulance & First Aid", "Hotlines": "+234-XXX-XXX-XXXX (Update)", "Avg ETA": "5–8 mins"},
        {"Unit": "Campus Fire & Safety Unit", "Coverage": "Labs, Hostels & Admin Blocks", "Hotlines": "+234-XXX-XXX-XXXX (Update)", "Avg ETA": "4–7 mins"},
        {"Unit": "SUG Welfare & Emergency Desk", "Coverage": "Student Peer Support & Escort", "Hotlines": "+234-XXX-XXX-XXXX (Update)", "Avg ETA": "2–4 mins"},
    ])
    st.table(responders)
