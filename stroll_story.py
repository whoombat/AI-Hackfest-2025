"""Module providing a generated AI walk summary, image, and route map."""

import argparse
import base64
import os  # For environment variables
import uuid  # For generating unique filenames
from enum import Enum
from io import BytesIO

import folium  # For map visualization
import gpxpy
import gpxpy.gpx
from dotenv import load_dotenv  # For loading environment variables
from google import genai  # For Google Gemini API
from google.genai import types
from PIL import Image

OUTPUT_DIR = "outputs"

class Tone(Enum):
    """Class representing the tone of the journal entry."""
    FUN = "fun"
    SERIOUS = "serious"
    NEUTRAL = "neutral"
    POETIC = "poetic"
    TECHNICAL = "technical"
    CRINGE = "cringe"
TONE_HELP = "Tone for the journal entry"

class Focus(Enum):
    """Class representing the focus of the journal entry."""
    LANDMARKS = "landmarks"
    PARKS = "parks"
    BODIES_OF_WATER = "bodies_of_water"
    DISTANCE = "distance"
    TIME = "time"
    WEATHER = "weather"
    PLAYGROUNDS = "playgrounds"
    RESTAURANTS = "restaurants"
    COLORS = "colors"
FOCUS_HELP = "Focus for the journal entry"

class Length(Enum):
    """Class representing the length of the journal entry."""
    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"
LENGTH_HELP = "Length for the journal entry"

def get_journal_prompt(route_data, tone, focus, length):
    """Generate a journal prompt."""
    return f"""Summarize a walk as a {length} journal entry with a {tone} tone that followed these
GPS coordinates with timestamp: {str(route_data)} (don't report the coordinates or specific
timestamps back (start and end time okay). Try to focus on {focus} and otherwise identify one major
landmark, park, or body of water near each coordinate, and provide a fun fact about each (but don't
explicitly say fun fact each time). Comment on pace based on time and disctance covered. Incorpoate
the weather. Include a planned next walk based on the general area of this walk. Make the output
HTML formatted. Don't provide anything after the HTML, nor a blurb at start, just the journal
entry."""


def get_image_prompt(journal_entry):
    """Generate an image prompt based on the journal entry."""
    return f"""Generate a sketch-style image with no added text of one of the locations mentioned
in this journal entry: {journal_entry}"""


def parse_gpx(file_path):
    """
    Parses a GPX file and extracts relevant information as a text string.

    Args:
        file_path (str): The path to the GPX file.

    Returns:
        The gpx data. Returns None if the file cannot be opened or parsed.
    """
    try:
        with open(file_path, 'r') as gpx_file:
            return gpxpy.parse(gpx_file)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except gpxpy.gpx.GPXException as e:
        print(f"Error parsing GPX file: {e}")
        return None


def convert_gpx_to_text(gpx):
    """
    Parses a GPX file and extracts relevant information as a text string.

    Args:
        The gpx data.

    Returns:
        str: A text representation of the GPX data, including track points
             (latitude, longitude, elevation, time), waypoints, and route
             points. Returns None if the file cannot be opened or parsed.
    """

    output_text = "GPX Data:\n"

    # Process tracks
    if gpx.tracks:
        output_text += "\nTracks:\n"
        for track in gpx.tracks:
            output_text += f"  Name: {track.name}\n"
            for segment in track.segments:
                output_text += "    Segment Points:\n"
                for point in segment.points:
                    output_text += f"      Lat: {point.latitude}, Lon: {point.longitude}, "
                    if point.elevation is not None:
                        output_text += f"Elev: {point.elevation}, "
                    if point.time is not None:
                        output_text += f"Time: {point.time.isoformat()} UTC\n"

    # Process waypoints
    if gpx.waypoints:
        output_text += "\nWaypoints:\n"
        for waypoint in gpx.waypoints:
            output_text += f"  Name: {waypoint.name}, Lat: {waypoint.latitude}, Lon: {waypoint.longitude}\n"
            if waypoint.elevation is not None:
                output_text += f"    Elev: {waypoint.elevation}\n"
            if waypoint.time is not None:
                output_text += f"    Time: {waypoint.time.isoformat()} UTC\n"
            if waypoint.description:
                output_text += f"    Description: {waypoint.description}\n"

    # Process routes
    if gpx.routes:
        output_text += "\nRoutes:\n"
        for route in gpx.routes:
            output_text += f"  Name: {route.name}\n"
            output_text += "    Route Points:\n"
            for point in route.points:
                output_text += f"      Lat: {point.latitude}, Lon: {point.longitude}, "
                if point.elevation is not None:
                    output_text += f"Elev: {point.elevation}, "
                if point.time is not None:
                    output_text += f"Time: {point.time.isoformat()} UTC\n"
                if point.description:
                    output_text += f"      Description: {point.description}\n"

    return output_text


def generate_map(gpx_coordinates):
    """builds a map from the gpx coordinates"""
    coordinates = []
    for track in gpx_coordinates.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append((point.latitude, point.longitude, point.time))

    # Create a map centered around the first point
    output_map = folium.Map(location=(coordinates[0][0], coordinates[0][1]), zoom_start=14)

    start_coord = (coordinates[0][0], coordinates[0][1])
    end_coord = (coordinates[-1][0], coordinates[-1][1])
    is_loop = start_coord == end_coord

    for i, coord in enumerate(coordinates):
        color = 'blue'  # Default for non-start/end

        if i == 0:
            color = 'green'
        elif i == len(coordinates) - 1:
            color = 'purple' if is_loop else 'red'

        folium.Marker((coord[0], coord[1]), popup=f"Time: {coord[2]}",
                      icon=folium.Icon(color=color)).add_to(output_map)

    # Add a Polyline to connect the points
    folium.PolyLine([(coord[0], coord[1]) for coord in coordinates], color="blue",
                    weight=5).add_to(output_map)

    return output_map


def build_output_html(m, journal_entry, image):
    """Builds the HTML output with the map and journal, and image."""
    html_image = ""

    for part in image.candidates[0].content.parts:
        if part.inline_data is not None:
            image_result = Image.open(BytesIO((part.inline_data.data)))
            buffered = BytesIO()
            image_result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            html_image += f'<img src="data:image/png;base64,{img_str}" alt="Generated Image"><br><br>'
        else:
            print("No image data found in the response.")

    # Get the HTML representation of the map
    map_html = m.get_root().render()

    # Inject the AI summary
    journal_html = f"<div style='font-family: Arial; margin: 20px;'><h2>Walk Summary</h2><p>\
        {journal_entry.text}</p></div>"

    return map_html.replace("<body>", f"<body>{journal_html}{html_image}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate map, journal, and image from GPX data.")
    parser.add_argument("--gpx",
                        default="inputs/ottawa.gpx",
                        help="Path to the GPX file")
    parser.add_argument("--tone",
                        default=Tone.NEUTRAL.value,
                        choices=[e.value for e in Tone],
                        help=TONE_HELP)
    parser.add_argument("--focus",
                        default=Focus.LANDMARKS.value,
                        choices=[e.value for e in Focus],
                        help=FOCUS_HELP)
    parser.add_argument("--length",
                        default=Length.MEDIUM.value,
                        choices=[e.value for e in Length],
                        help=LENGTH_HELP)

    args = parser.parse_args()

    load_dotenv()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key is None:
        raise ValueError("GEMINI_API_KEY environment variable not set.")


    # Parse the GPX file and extract relevant data
    gpx_data = parse_gpx(args.gpx)
    if gpx_data is not None:
        parsed_route_data = convert_gpx_to_text(gpx_data)
        if parsed_route_data is None:
            raise ValueError("unable to retrieve gpx trip data.")
    else:
        raise ValueError(f"Unable to parse GPX data in '{args.gpx}'.")


    # Produce the journal entry using Gemini AI
    client = genai.Client(api_key=api_key)
    JOURNAL_ENTRY = client.models.generate_content(model="gemini-2.0-flash",
                                                contents=get_journal_prompt(parsed_route_data,
                                                                            args.tone,
                                                                            args.focus,
                                                                            args.length))


    # Produce image using Gemini AI
    image_response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=get_image_prompt(JOURNAL_ENTRY.text),
        config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image']
        )
    )


    # Generate the map using Folium
    m = generate_map(gpx_data)


    # Build the HTML output with the map, journal entry, and image
    OUTPUT_HTML = build_output_html(m, JOURNAL_ENTRY, image_response)


    # Save the HTML output to a file
    OUTPUT_FILEPATH = os.path.join(OUTPUT_DIR, f"trip_{uuid.uuid4().hex}.html")
    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as file:
        file.write(OUTPUT_HTML)

    print(f"Output saved to '{OUTPUT_FILEPATH}'")
