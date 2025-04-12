"""Module providing a generate AI walk summary and route map."""

import uuid  # For generating unique filenames
import os  # For environment variables
import folium  # For map visualization
from enum import Enum
from google import genai    # For Google Gemini API
from dotenv import load_dotenv  # For loading environment variables

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

OUTPUT_DIR = "trips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class Tone(Enum):
    FUN = "fun"
    SERIOUS = "serious"
    NEUTRAL = "neutral"
    POETIC = "poetic"
    TECHNICAL = "technical"
    CRINGE = "cringe"

class Focus(Enum):
    LANDMARKS = "landmarks"
    PARKS = "parks"
    BODIES_OF_WATER = "bodies_of_water"
    DISTANCE = "distance"
    TIME = "time"
    WEATHER = "weather"
    PLAYGROUNDS = "playgrounds"
    RESTAURANTS = "restaurants"
    COLORS = "colors"


# Example coordinates (latitude, longitude)
# could be enhanced to inputted as parameters, e.g. from GPS data
coordinates = [(45.43025807431552, -75.70863767151599, "2025-04-11 10:00:00"),
               (45.429000675621126, -75.70033355227784, "2025-04-11 10:05:00"),
               (45.427502301655224, -75.6970719860959, "2025-04-11 10:08:00"),
               (45.42494970371503, -75.69519443975263, "2025-04-11 10:15:00"),
               (45.42386537938022, -75.69826288691044, "2025-04-11 10:20:00"),
               (45.42600388793949, -75.69912655813056, "2025-04-11 10:30:00")]
tone = Tone.NEUTRAL
focus = Focus.COLORS

client = genai.Client(api_key=api_key)

PROMPT = f"""Summarize a walk as a journal entry with a {tone} tone that followed these GPS
coordinates with timestamp: {str(coordinates)} (don't report the coordinates or specific timestamps
back (start and end time okay). Try to focus on {focus} and otherwise identify one major landmark,
park, or body of water near each coordinate, and provide a fun fact about each (but don't
explicitly say fun fact each time). Comment on pace based on time and disctance covered. Include a
picture of one location on the route and also incorpoate the weather. Make the output HTML
formatted. Don't provide anything after the HTML, nor a blurb at start, just the journal entry."""

# Feed data to Gemini AI to generate journal entry
ai_summary = client.models.generate_content(model="gemini-2.0-flash",
                                            contents=PROMPT)

# Output result for debugging
# print(f"Walk Summary: {ai_summary.text}")


# Create a map centered around the first point
m = folium.Map(location=(coordinates[0][0], coordinates[0][1]), zoom_start=14)

# Add markers for each point
for coord in coordinates:
    folium.Marker((coord[0], coord[1]), popup=f"Time: {coord[2]}").add_to(m)

# Add a Polyline to connect the points
folium.PolyLine([(coord[0], coord[1]) for coord in coordinates], color="blue", weight=5).add_to(m)

# Get the HTML representation of the map
map_html = m.get_root().render()

# Inject the AI summary
summary_html = f"<div style='font-family: Arial; margin: 20px;'><h2>Walk Summary</h2><p>\
    {ai_summary.text}</p></div>"
custom_html = map_html.replace("<body>", f"<body>{summary_html}")

MAP_FILEPATH = os.path.join(OUTPUT_DIR, f"trip_{uuid.uuid4().hex}.html")
# Save the updated HTML directly
with open(MAP_FILEPATH, "w") as file:
    file.write(custom_html)
