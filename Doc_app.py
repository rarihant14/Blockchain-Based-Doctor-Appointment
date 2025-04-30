import streamlit as st
import hashlib
import datetime
import json
import os

# ============ BLOCKCHAIN SETUP ============

class Block:
    def __init__(self, index, timestamp, patient_id, name, reason, prev_hash):
        self.index = index
        self.timestamp = timestamp
        self.patient_id = patient_id
        self.name = name
        self.reason = reason
        self.prev_hash = prev_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.patient_id}{self.name}{self.reason}{self.prev_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "patient_id": self.patient_id,
            "name": self.name,
            "reason": self.reason,
            "prev_hash": self.prev_hash,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(data):
        block = Block(
            data["index"],
            data["timestamp"],
            data["patient_id"],
            data["name"],
            data["reason"],
            data["prev_hash"]
        )
        block.hash = data["hash"]
        return block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.patients = {}
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.datetime.now()), "0", "Genesis", "Start", "0")
        self.chain.append(genesis_block)

    def add_appointment(self, patient_id, name, reason, timestamp=None):
        if patient_id not in self.patients:
            self.patients[patient_id] = name
        prev_block = self.chain[-1]
        if timestamp is None:
            timestamp = str(datetime.datetime.now())
        new_block = Block(len(self.chain), timestamp, patient_id, name, reason, prev_block.hash)
        self.chain.append(new_block)

    def get_patient_history(self, patient_id):
        return [block for block in self.chain if block.patient_id == patient_id]

    def to_json(self):
        return json.dumps([block.to_dict() for block in self.chain], indent=4)

    def save_to_file(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    def load_from_file(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                blocks = json.load(f)
                self.chain = [Block.from_dict(b) for b in blocks]
                self.patients = {block.patient_id: block.name for block in self.chain if block.index != 0}

# ============ STREAMLIT UI ============

st.set_page_config(page_title="Doctor Appointment Blockchain", layout="centered")
st.title("🩺 Doctor Appointment Booking with Blockchain")

# Set save path on Desktop
if 'save_path' not in st.session_state:
    st.session_state.save_path = os.path.join(os.path.expanduser("~"), "Desktop", "blockchain_data.json")

save_path = st.session_state.save_path

# Initialize blockchain
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
    if not os.path.exists(save_path):
        st.session_state.blockchain.save_to_file(save_path)
    st.session_state.blockchain.load_from_file(save_path)

blockchain = st.session_state.blockchain

# Sidebar Save/Load
st.sidebar.header("💾 Save / Load Blockchain")

if st.sidebar.button("💾 Save to Desktop"):
    blockchain.save_to_file(save_path)
    st.sidebar.success(f"Saved to {save_path}")

if st.sidebar.button("📂 Load from Desktop"):
    blockchain.load_from_file(save_path)
    st.sidebar.success(f"Loaded from {save_path}")

# Tabs for appointment and history
tab1, tab2 = st.tabs(["📋 Book Appointment", "📜 View History"])

# --- TAB 1: BOOKING FORM ---
with tab1:
    st.subheader("New or Revisit Appointment")

    with st.form("appointment_form"):
        patient_id = st.text_input("Enter Patient ID (e.g. email or phone)", max_chars=30)
        name = st.text_input("Enter Full Name")
        reason = st.text_area("Reason for Visit")

        appointment_date = st.date_input("Select Appointment Date", datetime.date.today())
        appointment_time = st.time_input("Select Appointment Time", datetime.datetime.now().time())

        submitted = st.form_submit_button("Book Appointment")

        if submitted:
            if not patient_id.strip() or not name.strip() or not reason.strip():
                st.error("Please fill all fields.")
            else:
                appointment_datetime = datetime.datetime.combine(appointment_date, appointment_time)
                timestamp_str = appointment_datetime.isoformat()
                blockchain.add_appointment(patient_id, name, reason, timestamp=timestamp_str)
                blockchain.save_to_file(save_path)
                st.success("✅ Appointment booked and saved to blockchain!")

# --- TAB 2: VIEW HISTORY ---
with tab2:
    st.subheader("Patient Appointment History")
    search_id = st.text_input("Enter Patient ID to Search")

    if st.button("Get History"):
        if not search_id.strip():
            st.warning("Please enter a patient ID.")
        else:
            history = blockchain.get_patient_history(search_id.strip())
            if not history:
                st.info("No records found.")
            else:
                for block in history:
                    try:
                        dt = datetime.datetime.fromisoformat(block.timestamp)
                        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
                    except ValueError:
                        formatted_time = block.timestamp

                    st.markdown(f"""
                    **🕒 Date & Time:** {formatted_time}  
                    **👤 Patient Name:** {block.name}  
                    **📝 Reason:** {block.reason}  
                    `Block Hash:` `{block.hash}`
                    """)
                    st.markdown("---")
