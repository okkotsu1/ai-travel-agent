import streamlit as st
import os
import json
import shutil
from crewai import Crew
from langchain_core.messages import HumanMessage
from universal_llm import get_llm

from nlp_parser import parse_user_prompt
from tools import fetch_all_needed
from tasks import create_flight_task, create_hotel_task, create_tour_task
from agents import flight_planner_agent, hotel_planner_agent, tour_guide_agent

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="AI Travel Assistant", page_icon="🌍", layout="centered")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/airplane-emoji.png", width=64)
    st.markdown("## ✈️ Travel Assistant")
    st.markdown("Plan your flights, hotels, and tours with AI.")
    
    st.markdown("---")
    st.markdown("### 🛠 How to use:")
    st.markdown("""
    1. Ask a travel-related question  
    2. Specify destination, origin, and dates  
    3. Let the AI plan it for you!
    """)

    st.markdown("---")
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.parsed_data = {}
        st.experimental_rerun()

    st.markdown("---")
    st.caption("Made by Shivam · Powered by LangChain & Ollama")


# ---------- CUSTOM CSS ----------
st.markdown("""
    <style>
        /* Global background and font */
        body, .main {
            background-color: #f7f9fc;
            font-family: 'Segoe UI', sans-serif;
        }

        /* Header styling */
        .app-header {
            background: linear-gradient(to right, #3498db, #2ecc71);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
        }

        .app-header h1 {
            font-size: 2.5rem;
            margin: 0;
        }

        /* Chat bubble base style */
        .chat-bubble {
            padding: 1rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            line-height: 1.5;
            white-space: pre-wrap;
            color: #111; /* Ensures visibility in dark mode */
        }

        /* User bubble */
        .chat-bubble.user {
            background-color: #fff9e6;
            border-left: 5px solid #f39c12;
        }

        /* Assistant bubble */
        .chat-bubble.assistant {
            background-color: #eaf4ff;
            border-left: 5px solid #3498db;
        }

        /* Footer style */
        .footer {
            text-align: center;
            color: #999;
            margin-top: 2rem;
            font-size: 0.85rem;
        }

        /* Optional: fix overflow or layout bugs in dark mode */
        [data-testid="stChatMessage"] {
            overflow-wrap: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
    <div class="app-header">
        <h1>🧳 AI Travel Assistant</h1>
        <p>Your friendly planner for flights, hotels, and tours</p>
    </div>
""", unsafe_allow_html=True)

# ---------- SESSION INIT ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = {}

# ---------- DISPLAY CHAT HISTORY ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        role_class = msg["role"]
        st.markdown(f'<div class="chat-bubble {role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# ---------- USER INPUT ----------
user_input = st.chat_input("Ask me anything about your travel plans!")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(f'<div class="chat-bubble user">{user_input}</div>', unsafe_allow_html=True)

    # ---------- LLM RESPONSE ----------
    nlp_llm = get_llm(provider="openrouter", model="mistralai/mistral-small-3.2-24b-instruct")
    chat_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages])

    enhanced_prompt = (
        f"You are a friendly, smart travel agent. Understand the user's true intent naturally (flight booking, hotel, tour, or any combination). "
        f"Ask missing info like origin, destination, travel dates only when needed. "
        f"Do not assume things like budget if not mentioned. Be precise and clear.\n\n"
        f"Conversation so far:\n{chat_history}\n"
        f"User: {user_input}\n"
        f"Respond politely, ask the next necessary detail. Do not proceed with planning until all real required info is provided."
    )

    llm_response = nlp_llm.invoke([HumanMessage(content=enhanced_prompt)])
    assistant_reply = llm_response.content.strip()
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(f'<div class="chat-bubble assistant">{assistant_reply}</div>', unsafe_allow_html=True)

    # ---------- PARSE DATA ----------
    try:
        parsed = parse_user_prompt(chat_history + f"\nUser: {user_input}")
        if isinstance(parsed, dict):
            st.session_state.parsed_data.update(parsed)
    except Exception as e:
        st.warning(f"⚠️ Could not parse details: {e}")

    pd = st.session_state.parsed_data
    needed = []

    if pd.get("needs_flight"):
        if not pd.get("origin"):
            needed.append("origin")
        if not pd.get("destination"):
            needed.append("destination")
        if not pd.get("date_range"):
            needed.append("travel dates")

    if pd.get("needs_hotel"):
        if not pd.get("destination"):
            needed.append("destination")
        if not pd.get("date_range"):
            needed.append("stay dates")

    if pd.get("needs_tour"):
        if not pd.get("destination"):
            needed.append("destination")
        if not pd.get("date_range"):
            needed.append("tour dates")

    if needed:
        needed_str = ", ".join(needed)
        st.info(f"📝 To proceed, I still need: {needed_str}. Please provide these details.")
        st.stop()

    # ---------- CLEANUP ----------
    output_files = ["flight_task_output.txt", "hotel_task_output.txt", "tour_task_output.txt"]
    for file in output_files:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists("scraped_data"):
        shutil.rmtree("scraped_data")
    os.makedirs("scraped_data", exist_ok=True)

    # ---------- PLAN TRIP ----------
    with st.spinner("🚀 Planning your trip..."):
        try:
            fetch_all_needed(pd)

            agents, tasks = [], []
            if pd.get("needs_flight"):
                agents.append(flight_planner_agent)
                tasks.append(create_flight_task())
            if pd.get("needs_hotel"):
                agents.append(hotel_planner_agent)
                tasks.append(create_hotel_task())
            if pd.get("needs_tour"):
                agents.append(tour_guide_agent)
                tasks.append(create_tour_task())

            if agents and tasks:
                crew = Crew(agents=agents, tasks=tasks, verbose=False)
                crew.kickoff()

                result_parts = []

                import pandas as pd

                def render_output(title, file, icon):
                    if "Flight" in title and os.path.exists("scraped_data/flight_search.json"):
                        with open("scraped_data/flight_search.json", "r", encoding="utf-8") as f:
                            flights = json.load(f)
                        if flights:
                            st.subheader(f"{icon} {title}")
                            df = pd.DataFrame(flights)[["price", "airline", "departure_time", "arrival_time", "duration", "booking_link"]]

                            # Turn BookingLink into markdown links
                            df["booking_link"] = df["booking_link"].apply(lambda url: f"[Book]({url})" if url != "N/A" else "N/A")

                            # Rename columns for readability
                            df.columns = ["Price", "Airline", "Departure", "Arrival", "Duration", "Book Now"]

                            st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)
                        else:
                            st.warning(f"No {title.lower()} data to show.")
                        return


                    if "Hotel" in title and os.path.exists("scraped_data/hotel_search.json"):
                        with open("scraped_data/hotel_search.json", "r", encoding="utf-8") as f:
                            hotels = json.load(f)
                        if hotels:
                            st.subheader(f"{icon} {title}")
                            df = pd.DataFrame(hotels)[["Name", "Price", "Rating", "Location", "Contact", "Checkin", "Checkout", "Website"]]
                            df["Website"] = df["Website"].apply(lambda url: f"[Website]({url})" if url != "N/A" else "N/A")
                            df.columns = ["Hotel Name", "Price", "Rating", "Location","Contact", "Check-in", "Check-out", "Booking Link"]
                            st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)

                        else:
                            st.warning(f"No {title.lower()} data to show.")
                        return

                    # fallback to text output from LLM
                    if os.path.exists(file):
                        with open(file, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if content:
                                st.subheader(f"{icon} {title}")
                                st.markdown(content, unsafe_allow_html=True)
                            else:
                                st.warning(f"{title} generated no content.")
                    else:
                        st.warning(f"{title} file not found.")


                render_output("Flight Options", "flight_task_output.txt", "✈️")
                render_output("Hotel Options", "hotel_task_output.txt", "🏨")
                render_output("Tour Itinerary", "tour_task_output.txt", "🗺️")

                final_result = "\n\n---\n\n".join(result_parts)
                if final_result:
                    st.markdown(f'<div class="chat-bubble assistant">{final_result}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": final_result})
                else:
                    st.info("✅ Planning done, but no output was generated. Try refining your request.")
            else:
                st.warning("🤖 I identified no valid task. Please specify what you'd like to plan (flight, hotel, tour).")

        except Exception as e:
            st.error(f"❌ Error during planning: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"❌ Error during planning: {e}"})

# ---------- FOOTER ----------
st.markdown("""
    <div class="footer">
        AI Travel Planner
    </div>
""", unsafe_allow_html=True)
