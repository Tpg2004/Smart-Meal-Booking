import streamlit as st
from datetime import datetime, timedelta
import random
import time

# --- CONFIGURATION (MUST BE FIRST) ---
# Set the page to use wide layout for maximum screen usage
st.set_page_config(layout="wide", page_title="MessServe: Smart Meal Booking")

# --- CUSTOM CSS THEME (Modern University Feel: Deep Purple / Orange Accents) ---

CSS_STYLE = """
<style>

/* --- 1. FULL SCREEN LAYOUT OVERRIDE --- */
/* Remove Max-Width and Padding from main container */
.main .block-container {
    max-width: 100% !important;
    padding-left: 1rem;
    padding-right: 1rem;
    padding-top: 1rem;
}
/* Center content within the Streamlit columns for cleaner flow */
div.st-emotion-cache-1pxn4x8 {
    width: 100% !important;
}

/* --- 2. COLOR AND THEME STYLING --- */
/* Main App Background */
[data-testid="stAppViewContainer"] {
    background-color: #F8F8FF; /* Ghost White (very light base) */
}

/* Sidebar Styling (Deep Purple) */
[data-testid="stSidebar"] {
    background-color: #4B0082; /* Indigo (Deep Purple) */
}
[data-testid="stSidebar"] * {
    color: #E6E6FA !important; /* Lavender for text/labels */
}

/* Main Titles and Headers */
h1, h2, h3 {
    color: #4B0082; /* Deep Purple for headings */
}
h1 {
    font-size: 2.5em;
    font-weight: 800;
    margin-bottom: 0.5em;
    border-bottom: 3px solid #FF8C00; /* Orange underline accent */
    padding-bottom: 5px;
}
h3 {
    border-left: 5px solid #FF8C00;
    padding-left: 10px;
    line-height: 1.5;
}

/* Run/Primary Button (Orange) */
[data-testid="stButton"] button {
    background: linear-gradient(45deg, #FF8C00, #FFA500); /* Dark Orange to Orange gradient */
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
    transition: all 0.2s ease;
    box-shadow: 0 4px 10px rgba(255, 140, 0, 0.4);
}
[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(255, 140, 0, 0.6);
}

/* Metric Cards (Clean, Interactive) */
[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #D8BFD8; /* Thistle (light purple border) */
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 15px rgba(75, 0, 130, 0.1);
}

/* Success Message Background (for booking) */
[data-testid="stAlert"] {
    border-left: 8px solid #FF8C00;
    background-color: #FFF5EE; /* SeaShell light background */
}

/* Instructions and Feedback Box */
.info-box {
    background-color: #E6E6FA; /* Lavender for info boxes */
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #D8BFD8;
}

</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# --- CONFIGURATION CONTINUED ---
MEAL_TIMES = ["Breakfast", "Lunch", "Dinner"]
MAX_CAPACITY = 2000
MIN_RESERVATION_BUFFER = 100 
TODAY = datetime.now().date()
SESSION_ID = st.session_state.get('session_id', str(random.randint(1000, 9999)))
st.session_state['session_id'] = SESSION_ID

# --- DATA SIMULATION (Database replacement for Streamlit) ---
def init_data_state():
    """Initializes session state variables for persistence."""
    if 'reservations' not in st.session_state:
        # Key: 'YYYY-MM-DD_MealTime', Value: count of bookings
        st.session_state.reservations = {
            # Seed data: assume some bookings already exist for today
            f"{TODAY.strftime('%Y-%m-%d')}_Lunch": 150,
            f"{TODAY.strftime('%Y-%m-%d')}_Dinner": 120,
            f"{(TODAY + timedelta(days=1)).strftime('%Y-%m-%d')}_Breakfast": 80
        }
    if 'student_bookings' not in st.session_state:
        # Key: Session ID, Value: Set of booked slots
        st.session_state.student_bookings = {}
    
    if SESSION_ID not in st.session_state.student_bookings:
        st.session_state.student_bookings[SESSION_ID] = set()

    if 'feedback' not in st.session_state:
        st.session_state.feedback = []

init_data_state()


# --- UI COMPONENTS AND LOGIC ---

def get_meal_date_options():
    """Generates next meal slot options (B/L/D) for the next 3 days."""
    options = []
    
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    # Check if today's lunch/dinner slots are still open based on cutoffs
    if now.hour < 10 and current_time_str < "10:00": # Cutoff time 10 AM for lunch
        options.append((TODAY, "Lunch"))
    if now.hour < 16 and current_time_str < "16:00": # Cutoff time 4 PM for dinner
        options.append((TODAY, "Dinner"))

    # Add tomorrow's meals and future days (up to 3 days ahead)
    for i in range(1, 4):
        date = TODAY + timedelta(days=i)
        for meal in MEAL_TIMES:
            options.append((date, meal))

    # Format for display: "Today, Lunch" or "Mon 11/11, Dinner"
    formatted_options = []
    for date, meal in options:
        date_str = "Today" if date == TODAY else date.strftime("%a %m/%d")
        formatted_options.append(f"{date_str}, {meal}")
    
    return options, formatted_options


def display_reservation_tab():
    """Handles the core meal slot booking interface."""
    st.header("Book Your Meal Slot")
    
    meal_options, formatted_options = get_meal_date_options()

    if not meal_options:
        st.warning("All booking slots for the next available window are currently closed or passed.")
        return

    # Use columns to divide the booking interface
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("### Choose Meal")
        selected_index = st.selectbox(
            "Select the date and meal you wish to reserve:",
            options=range(len(formatted_options)),
            format_func=lambda x: formatted_options[x]
        )
        selected_date, selected_meal = meal_options[selected_index]
        slot_key = f"{selected_date.strftime('%Y-%m-%d')}_{selected_meal}"
        
        is_booked = slot_key in st.session_state.student_bookings[SESSION_ID]
        
        st.markdown(f"**Your Session ID:** `{SESSION_ID}`", help="This ID tracks your unique reservations.")
        
        st.markdown("---")
        
        if is_booked:
            st.success(f"You have already reserved this slot. Enjoy your {selected_meal}!")
            st.button("❌ Cancel Reservation", on_click=cancel_reservation, args=(slot_key, selected_meal), use_container_width=True)
        else:
            if st.button(f"✅ Reserve Slot for {selected_meal}", use_container_width=True, type="primary"):
                reserve_slot(slot_key, selected_meal)

    with col2:
        st.markdown("### Current Demand Analysis")
        current_bookings = st.session_state.reservations.get(slot_key, 0)
        
        # Determine Status and color
        available_slots = MAX_CAPACITY - current_bookings
        buffer_status = "Safe"
        status_color = "green"
        if available_slots < 500 and available_slots > MIN_RESERVATION_BUFFER:
            buffer_status = "Moderate"
            status_color = "orange"
        elif available_slots <= MIN_RESERVATION_BUFFER:
            buffer_status = "Critical (High Demand)"
            status_color = "red"
        
        # Display Core Metric
        st.metric(
            label=f"Total Reservations for {selected_meal}",
            value=f"{current_bookings} / {MAX_CAPACITY}",
        )
        
        # Display Slots Remaining and Status explicitly using Markdown for colored text
        st.markdown(f"## Slots Remaining: :{status_color}[{available_slots}]")
        st.markdown(f"**Wastage Buffer Status:** :{status_color}[{buffer_status}]")
        
        st.markdown("---")
        st.markdown(f"""
        <div class="info-box">
            <h4>Wastage Reduction Focus</h4>
            <p>We need accurate bookings to prevent ordering extra food beyond the reserved total.</p>
            <ul>
                <li>Demand is tracked against maximum hall capacity.</li>
                <li>Your reservation helps the kitchen plan accurately.</li>
                <li>Cut-off time: 10:00 AM for Lunch, 4:00 PM for Dinner, 10:00 PM (night before) for Breakfast.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def reserve_slot(slot_key, meal_name):
    """Adds a reservation to the simulated database."""
    if slot_key not in st.session_state.student_bookings[SESSION_ID]:
        # Update system-wide count
        st.session_state.reservations[slot_key] = st.session_state.reservations.get(slot_key, 0) + 1
        # Update user's personal booking list
        st.session_state.student_bookings[SESSION_ID].add(slot_key)
        st.success(f"Successfully reserved your slot for **{meal_name}**! Thank you for reducing waste.")
    else:
        st.error("You have already reserved this slot.")


def cancel_reservation(slot_key, meal_name):
    """Removes a reservation from the simulated database."""
    if slot_key in st.session_state.student_bookings[SESSION_ID]:
        # Update system-wide count
        st.session_state.reservations[slot_key] = st.session_state.reservations.get(slot_key, 1) - 1
        if st.session_state.reservations[slot_key] < 0:
             st.session_state.reservations[slot_key] = 0 # Safety check

        # Update user's personal booking list
        st.session_state.student_bookings[SESSION_ID].remove(slot_key)
        st.warning(f"Your reservation for **{meal_name}** has been cancelled. If you re-book, please do so before the cutoff time.")
    else:
        st.info("You do not have an active reservation for this slot.")


def display_menu_tab():
    """Displays menu information and system instructions."""
    st.header("Menu and Booking Instructions")
    
    st.markdown("### Today's Menu Highlight (Chef's Choice)")
    
    menu_data = [
        ("Breakfast (7:30 AM - 9:00 AM)", "Scrambled Eggs, Sausage/Vada, Fresh Fruit, Coffee/Tea"),
        ("Lunch (12:30 PM - 1:30 PM)", "Butter Chicken / Paneer Makhani, Naan, Mixed Vegetable Curry, Rice"),
        ("Dinner (7:00 PM - 8:30 PM)", "South Indian Thali: Sambar, Rasam, Mixed Vegetable Poriyal, Curd Rice")
    ]

    for meal, items in menu_data:
        st.markdown(f"**{meal}:** {items}")

    st.markdown("---")
    
    st.markdown("### 📝 System Instructions")
    st.markdown("""
    <div class="info-box">
        <p>This system, **MessServe**, is designed to help our kitchen prepare the right amount of food, reducing the significant waste caused by over-preparation.</p>
        <ol>
            <li>**Booking:** Use the 'Book Your Meal Slot' tab to confirm your attendance for a specific meal. This is a commitment for the kitchen.</li>
            <li>**Wastage Metric:** The system tracks live demand. Higher booking numbers help the kitchen optimize resource allocation.</li>
            <li>**Cancellation:** If your plans change, please cancel your slot immediately on the 'Book Your Meal Slot' tab to keep the demand metrics accurate.</li>
            <li>**Cut-Off Timings:**
                <ul>
                    <li>**Breakfast:** Booking closes at 10:00 PM the night before.</li>
                    <li>**Lunch:** Booking closes at 10:00 AM the same day.</li>
                    <li>**Dinner:** Booking closes at 4:00 PM the same day.</li>
                </ul>
            </li>
        </ol>
        <p>Thank you for helping us make the Mess more sustainable!</p>
    </div>
    """, unsafe_allow_html=True)


def display_feedback_tab():
    """Handles student feedback submission."""
    st.header("Feedback & Suggestions")
    
    with st.form("feedback_form"):
        st.markdown("### Your Opinion Matters")
        
        name = st.text_input("Name (Optional, defaults to Session ID):", value=f"Student {SESSION_ID}")
        rating = st.slider("Rate Your Experience (1: Poor to 5: Excellent)", 1, 5, 3)
        category = st.selectbox("Category of Feedback:", ["Food Quality", "Hygiene", "Mess Staff", "Booking System", "Other"])
        
        comments = st.text_area("Detailed Comments (Required):", height=150)
        
        submitted = st.form_submit_button("Submit Feedback", type="primary")
        
        if submitted:
            if not comments:
                st.error("Please provide detailed comments before submitting.")
            else:
                feedback_entry = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "rating": rating,
                    "category": category,
                    "comments": comments
                }
                # Store feedback in session state simulation
                st.session_state.feedback.append(feedback_entry)
                st.success("Thank you! Your feedback has been recorded.")
                
    st.markdown("---")
    st.markdown("### Recent Feedback (Admin View Simulation)")
    if st.session_state.feedback:
        for i, entry in enumerate(st.session_state.feedback[-5:]): # Show last 5 entries
            st.markdown(f"**{entry['category']}** by {entry['name']} on {entry['time']}")
            st.markdown(f"Rating: {entry['rating']} / 5")
            st.code(entry['comments'])
            if i < len(st.session_state.feedback[-5:]) - 1:
                st.markdown("---")
    else:
        st.info("No feedback has been submitted yet.")


# --- MAIN APP LAYOUT ---

# Use tabs for clean navigation
tab_book, tab_menu, tab_feedback = st.tabs([
    "📅 Book Your Slot", 
    "📜 Menu & Instructions", 
    "💬 Feedback"
])

with tab_book:
    display_reservation_tab()

with tab_menu:
    display_menu_tab()

with tab_feedback:
    display_feedback_tab()
