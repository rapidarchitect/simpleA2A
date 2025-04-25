#!/usr/bin/env python3
# /// script
# dependencies = [
#   "httpx",
#   "python_a2a[all]",
#   "fastapi",
#   "pydantic",
#   "python-jose[cryptography]",
#   "python-dotenv"
# ]
# ///

from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
import json
from functools import wraps
from typing import Dict, List

load_dotenv()

security = HTTPBearer()
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"

# Activity database
ACTIVITIES: Dict[str, List[str]] = {
    "new york": [
        "Visit Central Park",
        "Explore Times Square",
        "Visit the Metropolitan Museum of Art",
        "Take a walk on the High Line",
        "See a Broadway show"
    ],
    "tokyo": [
        "Visit Senso-ji Temple",
        "Explore Shibuya Crossing",
        "Tour the Imperial Palace",
        "Shop in Harajuku",
        "Experience the Robot Restaurant"
    ]
}

class AuthenticatedActivityAgent(A2AServer):
    def __init__(self):
        super().__init__()
        if not SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable is not set")

    def verify_token(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True
        except JWTError:
            return False

    def handle_message(self, message: Message) -> Message:
        """
        Non-async version of handle_message
        """
        if not hasattr(message, 'content') or not hasattr(message.content, 'text'):
            return Message(
                content=TextContent(text="Invalid message format"),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=getattr(message, 'conversation_id', None)
            )

        # Extract city and context from the message
        text = message.content.text.lower()

        # Find activities for the mentioned city
        activity_list = []
        for city, city_activities in ACTIVITIES.items():
            if city in text:
                activity_list = city_activities
                break

        if activity_list:
            response_text = f"Recommended activities: {', '.join(activity_list)}"
        else:
            response_text = "No activity recommendations available for this location."

        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )

def create_agent_card():
    card = {
        "name": "Activity Recommendation Agent",
        "description": "Suggests activities based on location and context",
        "version": "1.0.0",
        "authentication": {
            "type": "bearer",
            "description": "JWT Bearer token required for authentication"
        },
        "skills": [{
            "name": "suggestActivities",
            "description": "Get activity recommendations for a specific location"
        }]
    }
    os.makedirs(".well-known", exist_ok=True)
    with open(".well-known/agent-activity.json", "w") as f:
        json.dump(card, f)

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Get the Authorization header
        auth_header = environ.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return self._unauthorized(start_response)

        token = auth_header.split(' ')[1]

        if not AuthenticatedActivityAgent().verify_token(token):
            return self._unauthorized(start_response)

        return self.app(environ, start_response)

    def _unauthorized(self, start_response):
        start_response('401 Unauthorized', [
            ('Content-Type', 'application/json'),
            ('WWW-Authenticate', 'Bearer')
        ])
        return [b'{"detail": "Invalid authentication credentials"}']

if __name__ == "__main__":
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")

    create_agent_card()

    agent = AuthenticatedActivityAgent()
    app = run_server(agent, host="0.0.0.0", port=5003)
