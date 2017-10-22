# ga-dashlet
Simple Google Analytics API based live data dashlet

## Requirements

- Python2
- GTK 3.20+
- Composite support (for transparent window)
- Google API client

To install the Google API client run

    pip install --upgrade google-api-python-client

## Setup

The script requires Google Analytics API credentials and expects
those in a separate file named 'client_secrets.json' in the same
directory as the script.

You can produce a new secret using your Google API Console. Ensure
to enable the Google Analytics API and in the project create a
server secret in JSON format.

## Auto-Start

You probably want to automatically start the script on each login.
This can be done in many ways. One way is to add the following commands
to your ~/.xprofile

    (cd <INSTALL_PATH>/ga-dashlet && sleep 10 && ./ga-dashlet.py) &

Ensure to replace INSTALL_PATH with the correct installation directory!

Note that the sleep is there to ensure the composite manager has started.
