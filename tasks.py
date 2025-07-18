from crewai import Task
from agents import flight_planner_agent, hotel_planner_agent, tour_guide_agent
import json

def load_data(filename):
    with open(filename, encoding="utf-8") as f:
        return f.read()

def create_flight_task():
    flight_data = load_data("scraped_data/flight_search.json")
    return Task(
        agent=flight_planner_agent,
        description=(
            f"Using the following flight search data:\n{flight_data}\n\n"
            "Recommend the best flight options from the specified origin to the destination "
            "for the given date range. Focus on balancing cost, duration, layovers, and airline quality."
            "for the booking link if booking link is not available we can provied with google flight card url in it's place."
        ),
        output_file="flight_task_output.txt",
        expected_output=(
            "A detailed list of at least three flight options including:\n"
            "- Airline names\n"
            "- Price\n"
            "- Duration\n"
            "- Number of layovers\n"
            "- Departure\n"
            "- Arrival\n"
            "- Booking Link\n"

        )
    )

def create_tour_task():
    tour_data = load_data("scraped_data/tour_search.json")
    return Task(
        agent=tour_guide_agent,
        description=(
            f"Using the following attractions data:\n{tour_data}\n\n"
            "Design a detailed sightseeing itinerary for the destination. "
            "Organize attractions in a logical day-wise order to minimize travel time. "
            "Consider opening hours, peak times, and user enjoyment. "
            "Include hidden gems or local tips that could enhance the trip."
        ),
        output_file="tour_task_output.txt",
        expected_output=(
            "A day-wise sightseeing plan that includes:\n"
            "- Attraction names\n"
            "- Suggested visit time\n"
            "- Local tips\n"
            "- Logical travel flow to minimize time on the road"
        )
    )

def create_hotel_task():
    try:
        with open("scraped_data/hotel_search.json", encoding="utf-8") as f:
            hotel_list = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load hotel_search.json: {e}")
        hotel_list = []

    readable_hotel_data = []
    for hotel in hotel_list:
        name = hotel.get("hotel_name") or hotel.get("Name")
        if not name:
            continue

        summary = f"**{name}**"
        price = hotel.get("price_info") or hotel.get("Price")
        rating = hotel.get("rating") or hotel.get("Rating")
        location = hotel.get("location") or hotel.get("Location")
        link = hotel.get("link") or hotel.get("Link")
        checkin_time = hotel.get("Checkin", "N/A")
        checkout_time = hotel.get("Checkout", "N/A")

        if price:
            summary += f"\n- Price: {price}"
        if rating:
            summary += f"\n- Reviews: {rating}"
        if location:
            summary += f"\n- Location: {location}"
        if checkin_time:
            summary += f"\n- Check-in time: {checkin_time}"
        if checkout_time:
            summary += f"\n- Check-out time: {checkout_time}"
        if link:
            summary += f"\n- Booking link: {link}"

        readable_hotel_data.append(summary)

    hotel_text = "\n\n".join(readable_hotel_data).strip() or "No valid hotel data available."
    print("[DEBUG] Hotel text passed to agent:\n", hotel_text)

    return Task(
        agent=hotel_planner_agent,
        description=(
            f"You are a hotel planning expert.\n\n"
            f"Here is structured data about hotels in the destination city, including pricing, reviews, and check-in/out times:\n\n"
            f"{hotel_text}\n\n"
            "Your task is to analyze the above hotel options and select 2 or 3 hotels that:\n"
            "- Have competitive pricing\n"
            "- Are located near main attractions\n"
            "- Have good user reviews or ratings\n"
            "- Offer convenient check-in/check-out times (e.g., early check-in or late check-out)\n"
            "- Have booking links\n\n"
            "DO NOT ask the user for more information — you must use only the data provided above.\n\n"
            "Format your response like this:\n"
            "1. **Hotel Name**\n"
            "   - Location: (if available)\n"
            "   - Price: ...\n"
            "   - Reviews: ...\n"
            "   - Check-in / Check-out time: ...\n"
            "   - Why it's a good fit: ...\n"
            "   - Booking link: ..."
        ),
        output_file="hotel_task_output.txt",
        expected_output=(
            "3-4 hotel recommendations with:\n"
            "- Name\n- Location\n- Price\n- Reviews\n- Check-in/out time\n- Booking link\n- Reason why it fits the itinerary"
        )
    )
