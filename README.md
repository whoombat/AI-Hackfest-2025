# Stroll Story

The purpose of Stroll Story is to generate a peronalized journal entry and image for a walk taken by the user. The user provides a .gpx file with the route taken (available from popular apps like Stava).

Stroll Story uses Gemini (API key required) to produce a journal entry and related image, which can make the walk more memorable. In addition, a map of the route taken is included.

To use stroll_story.py, set an environment variable `GEMINI_API_KEY `. Then see help

```
(.venv) PS AI Hackfest 2025> python .\stroll_story.py --help
usage: stroll_story.py [-h] [--gpx GPX] [--tone {fun,serious,neutral,poetic,technical,cringe}] [--focus {landmarks,parks,bodies_of_water,distance,time,weather,playgrounds,restaurants,colors}] [--length {short,medium,detailed}]

Generate map, journal, and image from GPX data.

options:
  -h, --help            show this help message and exit
  --gpx GPX             Path to the GPX file
  --tone {fun,serious,neutral,poetic,technical,cringe}
                        Tone for the journal entry
  --focus {landmarks,parks,bodies_of_water,distance,time,weather,playgrounds,restaurants,colors}
                        Focus for the journal entry
  --length {short,medium,detailed}
                        Length for the journal entry
```

Using one of the sample GPX files,

```
(.venv) PS AI Hackfest 2025> python .\stroll_story.py --gpx ".\inputs\toronto.gpx" --tone "fun" --focus "landmarks" --length "detailed"
Output saved to 'outputs\trip_3380f6bf42914675a82d8cfa1f6dcc98.html'
```

The `index.html` can be used to view the sample outputs, visible at https://whoombat.github.io/AI-Hackfest-2025/index.html

