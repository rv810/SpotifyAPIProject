from flask import Flask, request, redirect, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import time
import os
from dotenv import load_dotenv

from edit_tables import *

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("CLIENT_SECRET")
app.config['SESSION_COOKIE_NAME'] = 'spotify-session'

# Spotify API credentials
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-read-playback-state user-modify-playback-state playlist-read-private"
)

@app.route('/')
def index():
    return redirect(sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('track_skip'))

skipped_songs = {}

@app.route('/track-skip')
def track_skip():
    token_info = session.get('token_info', {})
    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_track = sp.current_playback()
    if not current_track or not current_track['is_playing']:
        return "No song is playing"

    track_id = current_track['item']['id']
    track_name = current_track['item']['name']
    start_time = time.time()

    # Simulate skip detection (log if track changes within 10 seconds)
    time.sleep(10)
    new_track = sp.current_playback()['item']['id']
    if new_track != track_id:
        skipped_songs[track_id] = track_name
        add_skip(track_id, track_name)

    return f"Logged skipped song: {track_name}"

@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info', {})
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    return json.dumps(playlists, indent=2)

if __name__ == '__main__':
    app.run(port=8888)