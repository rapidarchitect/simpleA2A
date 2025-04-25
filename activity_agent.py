#!/usr/bin/env python3
# /// script
# dependencies = [
#   "httpx",
#   "python_a2a[all]",
#   "fastapi",
#   "pydantic",
#   "asyncio",
#   "python-jose[cryptography]",
#   "python-dotenv"
# ]
# ///

import asyncio
import os
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
from python_a2a import A2AClient, Message, TextContent, MessageRole
import httpx

load_dotenv()

class AuthenticatedA2AClient(A2AClient):
    def __init__(self, url: str, jwt_token: str = None):
        self.url = url
        self.headers = {"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}

    async def send_message(self, message: Message) -> Message:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/messages",
                json=message.dict(),
                headers=self.headers
            )
            response.raise_for_status()
            return Message.parse_obj(response.json())

def create_jwt_token():
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")

    payload = {
        "sub": "travel_planner",
        "name": "Travel Planning Service",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

async def orchestrate_trip_planning(city):
    # Create JWT token for activity service
    try:
        jwt_token = create_jwt_token()
    except ValueError as e:
        print(f"JWT Token creation failed: {str(e)}")
        return "Authentication configuration error"

    # Initialize clients - only activity client needs authentication
    weather_client = A2AClient("http://localhost:5001/a2a")
    hotel_client = A2AClient("http://localhost:5002/a2a")
    activity_client = AuthenticatedA2AClient("http://localhost:5003/a2a", jwt_token)

    # 1. Get weather information
    weather_msg = Message(content=TextContent(text=city), role=MessageRole.USER)
    try:
        weather_resp = await weather_client.send_message(weather_msg)
        if hasattr(weather_resp.content, 'text'):
            weather_info = weather_resp.content.text
        else:
            weather_info = "Error getting weather information"
    except Exception as e:
        weather_info = f"Error connecting to weather service: {str(e)}"

    # 2. Get hotel information
    hotel_msg = Message(
        content=TextContent(text=f"Find hotels in {city} considering: {weather_info}"),
        role=MessageRole.USER
    )
    try:
        hotel_resp = await hotel_client.send_message(hotel_msg)
        content_type = type(hotel_resp.content).__name__
        if content_type == 'TextContent' and hasattr(hotel_resp.content, 'text'):
            hotel_info = hotel_resp.content.text
        else:
            hotel_info = "Error getting hotel information"
    except Exception as e:
        hotel_info = f"Error connecting to hotel service: {str(e)}"

    # 3. Suggest activities (with authentication)
    activity_msg = Message(
        content=TextContent(
            text=f"Suggest activities in {city}. Weather: {weather_info}. Staying at: {hotel_info}"
        ),
        role=MessageRole.USER
    )
    try:
        activity_resp = await activity_client.send_message(activity_msg)
        content_type = type(activity_resp.content).__name__
        if content_type == 'TextContent' and hasattr(activity_resp.content, 'text'):
            activity_info = activity_resp.content.text
        else:
            activity_info = "Error getting activity information"
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
