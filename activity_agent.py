# /// script
# dependencies = [
#   "httpx",
#   "python_a2a[all]",
#   "fastapi",
#   "pydantic",
# ]
# ///

# activity_agent.py
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server
import json

class ActivityAgent(A2AServer):
    def handle_message(self, message):
        if message.content.type == "text":
            query = message.content.text.strip()
            # Simple activity database
            activities = {
                "tokyo": {
                    "sunny": ["Visit Tokyo Skytree", "Explore Meiji Shrine", "Shop in Ginza"],
                    "rainy": ["Tokyo National Museum", "TeamLab Borderless digital art", "Shopping at underground malls"],
                    "default": ["Tokyo Disneyland", "Try local cuisine in Shinjuku"]
                },
                "new york": {
                    "sunny": ["Central Park walk", "Top of the Rock observation deck", "High Line park"],
                    "rainy": ["Metropolitan Museum of Art", "American Museum of Natural History", "Broadway show"],
                    "default": ["Times Square", "Empire State Building", "Statue of Liberty"]
                }
            }

            # Extract city and weather from query
            city_key = ""
            weather_type = "default"

            for city in activities.keys():
                if city in query.lower():
                    city_key = city
                    break

            if "sunny" in query.lower():
                weather_type = "sunny"
            elif "rainy" in query.lower() or "cloudy" in query.lower():
                weather_type = "rainy"

            if city_key and city_key in activities:
                city_activities = activities[city_key]
                activity_list = city_activities.get(weather_type, city_activities["default"])
                response_text = f"Recommended activities in {city_key.title()}: {', '.join(activity_list)}"
            else:
                response_text = "No activity recommendations available for this location."

            return Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

# Agent Card creation
def create_agent_card():
    card = {
        "name": "Activity Recommendation Agent",
        "description": "Suggests activities based on location and weather",
        "version": "1.0.0",
        "skills": [{"name": "suggestActivities", "description": "Suggest activities for a location based on weather and preferences"}]
    }
    with open(".well-known/agent.json", "w") as f:
        json.dump(card, f)

if __name__ == "__main__":
    import os
    os.makedirs(".well-known", exist_ok=True)
    create_agent_card()
    agent = ActivityAgent()
    run_server(agent, host="0.0.0.0", port=5003)