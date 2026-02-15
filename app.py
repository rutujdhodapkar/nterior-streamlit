import streamlit as st
import requests
import json
import os
import base64

# ================= CONFIG =================

API_KEY = "ddc-a4f-5d489223ebb84c0387b2c7e3cb01a751"
IMAGE_MODEL = "provider-4/imagen-4"
REASON_MODEL = "provider-2/deepseek-r1-distill-llama-70b"
BASE_URL = "https://api.a4f.co/v1"

# ================= INIT =================

def init_file(name, default):
    if not os.path.exists(name):
        with open(name, "w") as f:
            json.dump(default, f)

init_file("users.json", {})
init_file("structure.json", {})

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ================= API =================

def generate_image(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {"model": IMAGE_MODEL, "prompt": prompt, "size": "1024x1024"}
    r = requests.post(f"{BASE_URL}/images/generations",
                      headers=headers, json=data)
    return r.json()

def call_reason(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": REASON_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(f"{BASE_URL}/chat/completions",
                      headers=headers, json=data)
    return r.json()

# ================= STRUCTURE =================

def get_structure(user):
    return load_json("structure.json").get(user, {})

def save_structure(user, data):
    all_data = load_json("structure.json")
    all_data[user] = data
    save_json("structure.json", all_data)

# ================= LOGIN =================

def login():
    st.title("Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_json("users.json")
        if u in users and users[u] == p:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid")

    if st.button("Register"):
        users = load_json("users.json")
        users[u] = p
        save_json("users.json", users)
        st.success("Registered")

# ================= APP =================

if "user" not in st.session_state:
    login()
else:

    user = st.session_state.user
    structure = get_structure(user)

    # ================= SIDEBAR =================

    with st.sidebar:
        st.header("Project Structure")

        # ADD FLOOR
        with st.expander("➕ Add Floor"):
            floor_name = st.text_input("Floor Name")
            floor_dim = st.text_input("Optional Floor Dimensions")
            if st.button("Save Floor"):
                if floor_name:
                    structure[floor_name] = {
                        "floor_dimensions": floor_dim,
                        "rooms": {}
                    }
                    save_structure(user, structure)
                    st.rerun()

        st.divider()

        # HIERARCHY VIEW
        for floor, data in structure.items():
            with st.expander(f"🏢 {floor}"):

                if data["floor_dimensions"]:
                    st.write("📐", data["floor_dimensions"])

                # ADD ROOM BUTTON PER FLOOR
                if st.button(f"Add Room to {floor}"):
                    st.session_state.active_floor = floor

                # ROOM INPUT
                if st.session_state.get("active_floor") == floor:
                    room_name = st.text_input("Room Name", key=floor+"room")
                    dim = st.text_input("Room Dimensions")
                    img = st.file_uploader("Upload Room Image",
                                           type=["png","jpg"],
                                           key=floor+"img")

                    if st.button("Save Room", key=floor+"save"):
                        img_data = None
                        if img:
                            img_data = base64.b64encode(
                                img.read()).decode("utf-8")

                        structure[floor]["rooms"][room_name] = {
                            "dimensions": dim,
                            "image": img_data
                        }

                        save_structure(user, structure)
                        st.session_state.active_floor = None
                        st.rerun()

                # SHOW ROOMS
                for room, rdata in data["rooms"].items():
                    st.write("   └ 🛏", room)

        st.divider()
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()

    # ================= NAVIGATION =================

    nav = st.radio("Navigation",
                   ["Interior", "2D Plan", "3D"],
                   horizontal=True)

    # ================= INTERIOR =================

    if nav == "Interior":
        st.header("Interior Generator")

        for floor, data in structure.items():
            st.subheader(floor)

            for room, rdata in data["rooms"].items():
                st.write("Room:", room)

                col1, col2, col3, col4 = st.columns(4)

                if col1.button("Color", key=room+"color"):
                    img = generate_image(
                        f"{room} interior color redesign")
                    st.json(img)

                if col2.button("Furniture", key=room+"furn"):
                    img = generate_image(
                        f"{room} furniture styling")
                    st.json(img)

                if col3.button("Accent", key=room+"accent"):
                    img = generate_image(
                        f"{room} accent decor design")
                    st.json(img)

                if col4.button("Theme", key=room+"theme"):
                    img = generate_image(
                        f"{room} full theme redesign")
                    st.json(img)

    # ================= 2D PLAN =================

    if nav == "2D Plan":
        st.header("2D Planning")

        if st.button("Auto Generate Plan"):
            st.session_state.ask_floor_count = True

        if st.session_state.get("ask_floor_count"):
            floor_count = st.number_input(
                "How many floors?", min_value=1, step=1)

            if st.button("Create Floors"):
                for i in range(int(floor_count)):
                    structure[f"Floor {i+1}"] = {
                        "floor_dimensions": "",
                        "rooms": {}
                    }
                save_structure(user, structure)
                st.session_state.ask_floor_count = False
                st.rerun()

        # Generate full plan
        if st.button("Generate Full 2D Plan"):
            img = generate_image("Complete 2D architectural floor plan")
            st.json(img)

        # Generate each floor
        for floor in structure:
            if st.button(f"Generate {floor} 2D Plan"):
                img = generate_image(
                    f"2D floor plan for {floor}")
                st.json(img)

    # ================= 3D =================

    if nav == "3D":
        st.header("3D Customization")

        col1, col2, col3 = st.columns(3)

        if col1.button("Lighting"):
            img = generate_image("3D render with cinematic lighting")
            st.json(img)

        if col2.button("Materials"):
            img = generate_image("3D render premium materials")
            st.json(img)

        if col3.button("Landscape"):
            img = generate_image("3D house with landscape design")
            st.json(img)

        st.divider()

        custom = st.text_area("Custom 3D Prompt")
        if st.button("Generate Custom 3D"):
            img = generate_image(custom)
            st.json(img)
