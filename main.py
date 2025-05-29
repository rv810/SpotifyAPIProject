from flask import Flask, request, redirect, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import time
import os
import threading
from dotenv import load_dotenv
from flask_cors import CORS
CORS(app)

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
    
    # Start monitoring thread after authentication
    start_monitoring(token_info)
    
    return "Successfully authenticated! Skip tracking has started in the background."

# Global variable to control the monitoring thread
monitoring_active = False
monitor_thread = None

def monitor_playback(token_info):
    global monitoring_active
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    current_track_id = None
    current_track_start_time = None
    current_track_name = None
    current_track_duration = None
    
    while monitoring_active:
        try:
            # Check token expiration and refresh if needed
            if sp_oauth.is_token_expired(token_info):
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                sp = spotipy.Spotify(auth=token_info['access_token'])
            
            # Get current playback state
            playback = sp.current_playback()
            
            if not playback or not playback['is_playing']:
                time.sleep(5)  # Wait a bit if nothing is playing
                continue
                
            track = playback['item']
            new_track_id = track['id']
            
            # If this is a new track
            if new_track_id != current_track_id:
                # If we had a previous track and it changed before it should have ended
                if current_track_id and current_track_start_time:
                    elapsed_time = time.time() - current_track_start_time
                    if elapsed_time < (current_track_duration / 1000) - 10:  # 10 sec buffer
                        # Song was skipped
                        print(f"Skipped detected: {current_track_name}")
                        add_skip(current_track_id, current_track_name)
                
                # Update current track info
                current_track_id = new_track_id
                current_track_name = track['name']
                current_track_duration = track['duration_ms']
                current_track_start_time = time.time() - (playback['progress_ms'] / 1000)
                
                print(f"Now playing: {current_track_name}")
            
            # Sleep for a short time before checking again
            time.sleep(3)
            
        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            time.sleep(5)  # Wait a bit before retrying

def start_monitoring(token_info):
    global monitoring_active, monitor_thread
    
    # Stop existing thread if it's running
    if monitoring_active and monitor_thread and monitor_thread.is_alive():
        monitoring_active = False
        monitor_thread.join(timeout=1)
    
    # Start new monitoring thread
    monitoring_active = True
    monitor_thread = threading.Thread(target=monitor_playback, args=(token_info,))
    monitor_thread.daemon = True  # Thread will exit when main program exits
    monitor_thread.start()
    
    return "Monitoring started"

@app.route('/stop-monitoring')
def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    return "Monitoring stopped"

@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info', {})
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    return json.dumps(playlists, indent=2)

if __name__ == '__main__':
    app.run(port=8888)