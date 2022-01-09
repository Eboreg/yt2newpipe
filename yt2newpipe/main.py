import os
import shelve
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery

# Set to correct path for OAuth 2.0 secret .json file
SECRET = Path(__file__).parent / \
    "../secrets/client_secret_191731902895-oghc41ooejvrp4kl92marot94ecec93n.apps.googleusercontent.com.json"

# Shelve DB where playlist data and google.oauth2.credentials.Credentials
# object will be stored
SHELF = Path(__file__).parent / "../credentials.shelf"

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def get_playlists(resource: discovery.Resource):
    next_page_token = None
    playlists = []
    while True:
        response = resource.playlists().list(
            part="snippet,contentDetails",
            maxResults=50,
            mine=True,
            pageToken=next_page_token
        ).execute()

        playlists.extend([{
            "id": item["id"],
            "title": item["snippet"]["title"],
            "items": []
        } for item in response["items"]])

        next_page_token = response.get("nextPageToken", None)

        if next_page_token is None:
            break

    return playlists


def get_playlist_items(resource: discovery.Resource, playlist_id: str):
    next_page_token = None
    items = []
    while True:
        response = resource.playlistItems().list(
            part="snippet,id",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        items.extend([{
            "id": item["id"],
            "publishedAt": item["snippet"]["publishedAt"],
            "videoId": item["snippet"]["resourceId"]["videoId"]
        } for item in response["items"]])

        next_page_token = response.get("nextPageToken", None)

        if next_page_token is None:
            break

    return items


def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES)

    with shelve.open(str(SHELF)) as db:
        try:
            credentials = db["credentials"]
        except KeyError:
            credentials = flow.run_console(access_type="offline")
            db["credentials"] = credentials

    resource = discovery.build("youtube", "v3", credentials=credentials)

    playlists = get_playlists(resource)

    for playlist in playlists:
        playlist["items"] = get_playlist_items(resource, playlist["id"])

    with shelve.open(str(SHELF)) as db:
        db["playlists"] = playlists

    print(playlists)


if __name__ == "__main__":
    main()
