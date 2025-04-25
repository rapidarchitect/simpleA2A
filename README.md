# A2A demonstration

There are three agents, as an exemplar activity_agent has JWT authentication, the rest don't.
Idea here was to replicate a real world scenario (calling 2 internal agents, one external)
The original reference was all unauthenticated (see link below)

## Servers (Agents)

uv run each of these:

    - activity_agent.py
    - hotel_agent.py
    - weather_agent.py

### This sets up 3 agents waiting for requests on ports 5001 -> 5003

## Execution

- uv run main.py

## Reference

edit the city on line 120 of main.py, any city not in the "database" will return a

https://medium.com/data-science-collective/build-anything-with-a2a-agent-heres-how-part-1-dd25d31c1265
