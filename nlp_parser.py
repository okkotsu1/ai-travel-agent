import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

llm = ChatGroq(
    model="llama3-70b-8192",  # Ensure this matches Groq’s supported model exactly
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def parse_user_prompt(prompt):
    system_instruction = '''
You are an intelligent travel planner assistant.

The user will describe their travel intent in natural language. Your job is to extract their intent and return structured information.

Respond with a valid JSON object in the following format:

{
  "origin": "City the user is traveling from (empty string if not stated)",
  "destination": "City the user is going to",
  "date_range": "Dates mentioned (e.g., 'August 10–15')",
  "needs_flight": true/false,
  "needs_hotel": true/false,
  "needs_tour": true/false
}

Guidelines:
- Think like a human assistant: infer what the user wants based on clues in their message.
- Set 'needs_flight' to true if they mention flying, travel between cities, or a departure point.
- Set 'needs_hotel' to true if they mention staying, booking, accommodations, or anything implying overnight stay.
- Set 'needs_tour' to true if they mention sightseeing, attractions, exploring, or ask for plans.
- If the user's message is vague or general (e.g., “I want to visit Paris”), it's okay to make reasonable assumptions — but keep them minimal.
- Only mark something as true if it's clearly mentioned or reasonably implied.
- Do not include any explanations or extra text. Output valid JSON only.
'''
    


    messages = [
        HumanMessage(content=system_instruction),
        HumanMessage(content=prompt)
    ]
    response = llm.invoke(messages)
    return json.loads(response.content)
