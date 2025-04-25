# /// script
# dependencies = [
#   "httpx",
#   "python_a2a[all]",
#   "fastapi",
#   "pydantic",
#   "asyncio",
# ]
# ///

import asyncio
from python_a2a import A2AClient, Message, TextContent, MessageRole

async def orchestrate_trip_planning(city):

    weather_client = A2AClient("http://localhost:5001/a2a")
    hotel_client = A2AClient("http://localhost:5002/a2a")
    activity_client = A2AClient("http://localhost:5003/a2a")

    # 1. Get weather information
    weather_msg = Message(content=TextContent(text=city), role=MessageRole.USER)
    try:
        weather_resp = weather_client.send_message(weather_msg)
        # Check response type by its type attribute or class name
        if hasattr(weather_resp.content, 'text'):
            weather_info = weather_resp.content.text
        else:
            weather_info = f"Error getting weather information"
    except Exception as e:
        weather_info = f"Error connecting to weather service: {str(e)}"

    # 2. Get hotel information
    hotel_msg = Message(
        content=TextContent(text=f"Find hotels in {city} considering: {weather_info}"),
        role=MessageRole.USER
    )
    try:
        hotel_resp = hotel_client.send_message(hotel_msg)
        # Check response type more carefully
        content_type = type(hotel_resp.content).__name__
        if content_type == 'TextContent' and hasattr(hotel_resp.content, 'text'):
            hotel_info = hotel_resp.content.text
        else:
            hotel_info = f"Error getting hotel information"
    except Exception as e:
        hotel_info = f"Error connecting to hotel service: {str(e)}"

    # 3. Suggest activities
    activity_msg = Message(
        content=TextContent(
            text=f"Suggest activities in {city}. Weather: {weather_info}. Staying at: {hotel_info}"
        ),
        role=MessageRole.USER
    )
    try:
        activity_resp = activity_client.send_message(activity_msg)
        content_type = type(activity_resp.content).__name__
        if content_type == 'TextContent' and hasattr(activity_resp.content, 'text'):
            activity_info = activity_resp.content.text
        else:
            activity_info = f"Error getting activity information"
    except Exception as e:
        activity_info = f"Error connecting to activity service: {str(e)}"

    # Create the final travel plan
    return f"""
    Travel Plan for {city}
    ---------------------
    Weather: {weather_info}
    Accommodation: {hotel_info}
    Activities: {activity_info}
    """

if __name__ == "__main__":
    city = "New York"
    result = asyncio.run(orchestrate_trip_planning(city))
    print(result)