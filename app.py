import streamlit as st
import requests
import json
import os
from PIL import Image
import base64

# ===============================
# CONFIG
# ===============================

IMAGE_API_KEY = "ddc-a4f-5d489223ebb84c0387b2c7e3cb01a751"
IMAGE_MODEL = "provider-4/imagen-4"

REASONING_MODEL = "provider-2/deepseek-r1-distill-llama-70b"

BASE_URL = "https://api.a4f.co/v1"

# ===============================
# FILE INIT
# ===============================

def init_file(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

init_file("users.json", {})
init_file("settings.json", {})
init_file("structure.json", {})

# ===============================
# JSON HELPERS
# ===============================

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ===============================
# LOGIN SYSTEM
# ===============================

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_json("users.json")

        if username in users and users[username] == password:
            st.session_state.user = username
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Register"):
        users = load_json("users.json")
        users[username] = password
        save_json("users.json", users)
        st.success("Registered successfully")

# ===============================
# SETTINGS
# ===============================

def load_user_settings(username):
    settings = load_json("settings.json")
    return settings.get(username, {
        "account_name": username,
        "theme": "light"
    })

def save_user_settings(username, data):
    settings = load_json("settings.json")
    settings[username] = data
    save_json("settings.json", settings)

def apply_theme(theme):
    if theme == "dark":
        st.markdown("""
        <style>
        body {background-color:#111; color:white;}
        </style>
        """, unsafe_allow_html=True)

# ===============================
# API CALLS
# ===============================

def call_reasoning(prompt):
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": REASONING_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    res = requests.post(f"{BASE_URL}/chat/completions",
                        headers=headers,
                        json=data)

    return res.json()

def generate_image(prompt):
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1024"
    }

    res = requests.post(f"{BASE_URL}/images/generations",
                        headers=headers,
                        json=data)

    return res.json()

# ===============================
# FLOOR + ROOM STRUCTURE
# ===============================

def add_floor(user, floor_name):
    structure = load_json("structure.json")
    if user not in structure:
        structure[user] = {}

    structure[user][floor_name] = {}
    save_json("structure.json", structure)

def add_room(user, floor, room_data):
    structure = load_json("structure.json")
    structure[user][floor][room_data["room_name"]] = room_data
    save_json("structure.json", structure)

# ===============================
# MAIN UI
# ===============================

if "user" not in st.session_state:
    login()
else:
    user = st.session_state.user
    settings = load_user_settings(user)
    apply_theme(settings["theme"])

    # Sidebar
    with st.sidebar:
        st.header("Hierarchy")

        if st.button("Add Floor"):
            floor_name = st.text_input("Floor Name")
            if st.button("Save Floor"):
                add_floor(user, floor_name)

        structure = load_json("structure.json").get(user, {})
        for floor in structure:
            st.subheader(floor)
            for room in structure[floor]:
                st.write("↳", room)

        st.divider()
        st.write(user)
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()

        if st.button("Settings"):
            st.session_state.show_settings = True

    # SETTINGS POPUP
    if st.session_state.get("show_settings"):
        st.title("Settings")

        account_name = st.text_input("Account Name", settings["account_name"])
        theme = st.selectbox("Theme", ["light", "dark"])

        if st.button("Save Settings"):
            save_user_settings(user, {
                "account_name": account_name,
                "theme": theme
            })
            st.success("Saved")
            st.session_state.show_settings = False
            st.rerun()

    # Navbar
    nav = st.selectbox("Navigation",
                       ["Interior", "2D Plan", "Exterior"])

    if nav == "Interior":
        st.header("Interior Design")

        floor = st.selectbox("Select Floor",
                             list(structure.keys()))

        room_name = st.text_input("Room Name")
        dim = st.text_input("Dimensions (LxW)")
        style = st.selectbox("Interior Style",
                             ["Modern", "Minimal", "Luxury", "Custom"])
        color = st.text_input("Color")
        furniture = st.text_input("Furniture")

        uploaded = st.file_uploader("Upload Reference Image",
                                     type=["png", "jpg"])

        if st.button("Add Room"):
            room_data = {
                "room_name": room_name,
                "dimensions": dim,
                "style": style,
                "color": color,
                "furniture": furniture
            }

            add_room(user, floor, room_data)
            st.success("Room Added")

        if st.button("Generate Interior Image"):
            prompt = f"{style} {room_name} with {color} theme and {furniture}"
            result = generate_image(prompt)

            st.write(result)

    if nav == "2D Plan":
        st.header("2D Floor Planning")

        desc = st.text_area("Describe plan")

        if st.button("Generate Plan"):
            result = call_reasoning(desc)
            st.write(result)

    if nav == "Exterior":
        st.header("Exterior Design")

        prompt = st.text_area("Describe exterior")

        if st.button("Generate Exterior"):
            result = generate_image(prompt)
            st.write(result)
