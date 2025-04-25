# /// script
# dependencies = [
#   "httpx",
#   "python_a2a[all]",
#   "fastapi",
#   "pydantic",
# ]
# ///

# hotel_agent.py
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server
import json

class HotelAgent(A2AServer):
    def handle_message(self, message):
        if message.content.type == "text":
            query = message.content.text.strip()
            # Simple hotel database
            hotels = {
                "tokyo": [
                    "Grand Tokyo Hotel - Near city center, indoor pool, 5-star",
                    "Budget Inn Tokyo - Economic option with free breakfast"
                ],
                "new york": [
                    "Manhattan Suites - Central location, luxury accommodations",
                    "Brooklyn Boutique Hotel - Hip neighborhood, rooftop bar"
                ]
            }

            # Extract city name from query
            city_key = ""
            for city in hotels.keys():
                if city in query.lower():
                    city_key = city
                    break

            if city_key:
                hotel_list = hotels[city_key]
                response_text = f"Recommended hotels in {city_key.title()}: {', '.join(hotel_list)}"
            else:
                response_text = "No hotel information available for this location."

            return Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

# Agent Card creation
def create_agent_card():
    card = {
        "name": "Hotel Recommendation Agent",
        "description": "Recommends hotels based on location and preferences",
        "version": "1.0.0",
        "skills": [{"name": "findHotels", "description": "Find hotels in a specified location"}]
    }
    with open(".well-known/agent.json", "w") as f:
        json.dump(card, f)

if __name__ == "__main__":
    import os
    os.makedirs(".well-known", exist_ok=True)
    create_agent_card()
    agent = HotelAgent()
    run_server(agent, host="0.0.0.0", port=5002)