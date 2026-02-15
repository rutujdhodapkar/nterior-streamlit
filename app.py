import streamlit as st
import requests
import json
import os
import base64
from PIL import Image

# =========================
# CONFIG
# =========================

API_KEY = "ddc-a4f-5d489223ebb84c0387b2c7e3cb01a751"
IMAGE_MODEL = "provider-4/imagen-4"
REASON_MODEL = "provider-2/deepseek-r1-distill-llama-70b"
BASE_URL = "https://api.a4f.co/v1"

# =========================
# INIT FILES
# =========================

def init_file(name, default):
    if not os.path.exists(name):
        with open(name, "w") as f:
            json.dump(default, f)

init_file("users.json", {})
init_file("settings.json", {})
init_file("structure.json", {})

# =========================
# JSON HELPERS
# =========================

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# LOGIN
# =========================

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_json("users.json")
        if username in users and users[username] == password:
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Register"):
        users = load_json("users.json")
        users[username] = password
        save_json("users.json", users)
        st.success("Registered")

# =========================
# API CALLS
# =========================

def call_reasoning(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": REASON_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(f"{BASE_URL}/chat/completions",
                      headers=headers,
                      json=data)

    return r.json()

def generate_image(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1024"
    }

    r = requests.post(f"{BASE_URL}/images/generations",
                      headers=headers,
                      json=data)

    return r.json()

# =========================
# STRUCTURE FUNCTIONS
# =========================

def get_structure(user):
    return load_json("structure.json").get(user, {})

def save_structure(user, data):
    all_data = load_json("structure.json")
    all_data[user] = data
    save_json("structure.json", all_data)

def add_floor(user, floor):
    structure = get_structure(user)
    if floor not in structure:
        structure[floor] = {}
    save_structure(user, structure)

def add_room(user, floor, room):
    structure = get_structure(user)
    structure[floor][room] = {}
    save_structure(user, structure)

# =========================
# START APP
# =========================

if "user" not in st.session_state:
    login()
else:

    user = st.session_state.user
    structure = get_structure(user)

    # =========================
    # SIDEBAR HIERARCHY
    # =========================

    with st.sidebar:
        st.header("Hierarchy")

        if st.button("➕ Add Floor"):
            st.session_state.add_floor = True

        if st.session_state.get("add_floor"):
            new_floor = st.text_input("Floor Name")
            if st.button("Save Floor"):
                add_floor(user, new_floor)
                st.session_state.add_floor = False
                st.rerun()

        st.divider()

        if not structure:
            st.info("No floors yet")
        else:
            for floor, rooms in structure.items():
                with st.expander(f"🏢 {floor}", expanded=False):
                    if not rooms:
                        st.write("No rooms")
                    for room in rooms:
                        st.write(f"   └ 🛏 {room}")

        st.divider()

        if st.button("Logout"):
            del st.session_state.user
            st.rerun()

    # =========================
    # NAVBAR
    # =========================

    nav = st.radio("Navigation",
                   ["Interior", "2D Plan", "3D", "Exterior"],
                   horizontal=True)

    # =========================
    # INTERIOR
    # =========================

    if nav == "Interior":
        st.header("Interior Generator")

        prompt = st.text_area("Describe interior")

        if st.button("Generate Image"):
            result = generate_image(prompt)
            st.json(result)

    # =========================
    # 2D PLAN
    # =========================

    if nav == "2D Plan":
        st.header("2D Planning")

        col1, col2 = st.columns(2)

        with col1:
            floor_name = st.text_input("Floor Name")
            if st.button("Add Floor (2D)"):
                add_floor(user, floor_name)
                st.rerun()

        with col2:
            room_name = st.text_input("Room Name")
            selected_floor = st.selectbox("Select Floor",
                                          list(structure.keys()) if structure else [])
            if st.button("Add Room (2D)"):
                add_room(user, selected_floor, room_name)
                st.rerun()

        st.divider()

        # PRE PLAN
        st.subheader("Add Pre-Plan")
        plan_desc = st.text_area("Describe layout")

        if st.button("Add Pre-Plan"):
            response = call_reasoning(
                f"Extract floors and rooms from this: {plan_desc}"
            )
            st.json(response)

        if st.button("Generate 2D Plan Image"):
            img = generate_image(f"2D architectural floor plan of {plan_desc}")
            st.json(img)

        # Show each floor 2D plan
        st.subheader("Generate Each Floor Plan")
        for floor in structure:
            if st.button(f"Generate {floor} Plan"):
                img = generate_image(f"2D plan for floor {floor}")
                st.json(img)

    # =========================
    # 3D
    # =========================

    if nav == "3D":
        st.header("3D Model Generator")

        uploaded = st.file_uploader("Upload Reference Image",
                                    type=["png", "jpg", "jpeg"])

        desc = st.text_area("Describe 3D changes")

        if st.button("Generate 3D Model"):
            img = generate_image(f"3D render based on {desc}")
            st.json(img)

    # =========================
    # EXTERIOR
    # =========================

    if nav == "Exterior":
        st.header("Exterior Views")

        desc = st.text_area("Describe exterior design")

        if st.button("Generate Exterior Views"):

            front = generate_image(f"Front view of house: {desc}")
            side1 = generate_image(f"Left side view of house: {desc}")
            side2 = generate_image(f"Right side view of house: {desc}")

            st.subheader("Front")
            st.json(front)

            st.subheader("Side 1")
            st.json(side1)

            st.subheader("Side 2")
            st.json(side2)
