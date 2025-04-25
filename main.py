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
import uuid

load_dotenv()

class AuthenticatedA2AClient:
    def __init__(self, url: str, jwt_token: str = None):
        self.url = url.rstrip('/')  # Remove trailing slash if present
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}" if jwt_token else ""
        }

    async def send_message(self, message: Message) -> Message:
        async with httpx.AsyncClient() as client:
            # Ensure we have required fields
            if not message.message_id:
                message.message_id = str(uuid.uuid4())
            if not message.conversation_id:
                message.conversation_id = str(uuid.uuid4())

            # Convert Message to dictionary manually with all required fields
            message_dict = {
                "content": {
                    "type": "text",  # Explicitly set type
                    "text": message.content.text
                },
                "role": "user",  # Explicitly set role
                "message_id": message.message_id,
                "conversation_id": message.conversation_id,
                "parent_message_id": message.parent_message_id if message.parent_message_id else None,
                "created_at": datetime.utcnow().isoformat()  # Add timestamp
            }

            response = await client.post(
                self.url,
                json=message_dict,
                headers=self.headers
            )
            response.raise_for_status()
            # Create a new Message object directly
            return Message(
                content=TextContent(text=response.json()["content"]["text"]),
                role=MessageRole.AGENT,
                message_id=response.json().get("message_id"),
                conversation_id=response.json().get("conversation_id"),
                parent_message_id=response.json().get("parent_message_id")
            )

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

async def get_weather_info(client: A2AClient, city: str) -> str:
    try:
        message = Message(
            content=TextContent(text=city),
            role=MessageRole.USER,
            message_id=str(uuid.uuid4()),
            conversation_id=str(uuid.uuid4())
        )
        response = client.send_message(message)
        return response.content.text if hasattr(response.content, 'text') else "Error getting weather information"
    except Exception as e:
        return f"Error connecting to weather service: {str(e)}"

async def get_hotel_info(client: A2AClient, city: str, weather_info: str) -> str:
    try:
        message = Message(
            content=TextContent(text=f"Find hotels in {city} considering: {weather_info}"),
            role=MessageRole.USER,
            message_id=str(uuid.uuid4()),
            conversation_id=str(uuid.uuid4())
        )
        response = client.send_message(message)
        return response.content.text if hasattr(response.content, 'text') else "Error getting hotel information"
    except Exception as e:
        return f"Error connecting to hotel service: {str(e)}"

async def get_activity_info(client: AuthenticatedA2AClient, city: str, weather_info: str, hotel_info: str) -> str:
    try:
        message = Message(
            content=TextContent(text=f"Suggest activities in {city}. Weather: {weather_info}. Staying at: {hotel_info}"),
            role=MessageRole.USER,
            message_id=str(uuid.uuid4()),
            conversation_id=str(uuid.uuid4())
        )
        response = await client.send_message(message)
        return response.content.text if hasattr(response.content, 'text') else "Error getting activity information"
    except Exception as e:
        return f"Error connecting to activity service: {str(e)}"

async def orchestrate_trip_planning(city):
    # Create JWT token for activity service only
    try:
        jwt_token = create_jwt_token()
    except ValueError as e:
        print(f"JWT Token creation failed: {str(e)}")
        return "Authentication configuration error"

    # Initialize clients
    weather_client = A2AClient("http://localhost:5001/a2a")
    hotel_client = A2AClient("http://localhost:5002/a2a")
    activity_client = AuthenticatedA2AClient("http://localhost:5003/a2a", jwt_token)

    # Get information from all services
    weather_info = await get_weather_info(weather_client, city)
    hotel_info = await get_hotel_info(hotel_client, city, weather_info)
    activity_info = await get_activity_info(activity_client, city, weather_info, hotel_info)

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
