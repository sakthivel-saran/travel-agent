from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

from backend import final_agent, TravelState

from backend import run_travel_agent

state = {
    "messages": [],
    "user_query": "Plan a trip from Chennai to Dubai",
    "flight_results": "Flight AI123, Chennai to Dubai",
    "hotel_results": "Hotel XYZ, Dubai",
    "itinerary": "Day 1: Dubai Mall",
    "llm_calls": 0
}

user_input=input("enter travel reques: ")

response=run_travel_agent(user_input=user_input, 
                          thread_id="test_user")

print(response["answer"])

# res=tavily_search("best hotels in india")
# print(res)


