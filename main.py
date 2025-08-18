from flask import Flask, request, redirect, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import time
import os
import threading
from dotenv import load_dotenv
from flask_cors import CORS
from edit_tables import *
import sqlite3

load_dotenv()
app = Flask(__name__)
CORS(app)
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
    current_artist_name = None
    
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
                # if previous track changed before it should have ended
                if current_track_id and current_track_start_time:
                    elapsed_time = time.time() - current_track_start_time
                    if elapsed_time < (current_track_duration / 1000) - 10:  # 10 sec buffer
                        # Song was skipped
                        print(f"Skipped detected: {current_track_name}")
                        add_skip_with_artist(current_track_id, current_track_name, current_artist_name)
                
                # Update current track info
                current_track_id = new_track_id
                current_track_name = track['name']
                current_track_duration = track['duration_ms']
                current_track_start_time = time.time() - (playback['progress_ms'] / 1000)
                current_artist_name = track['artists'][0]['name'] if track['artists'] else None

                print(f"Now playing: {current_track_name} by {current_artist_name}")
            
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

@app.route('/playlists')
def playlists():
    print("received request for /playlists")
    token_info = session.get('token_info', {})

    if not token_info:
        return {"error": "Not authenticated"}
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    print(playlists)
    return json.dumps(playlists, indent=2)

@app.route('/api/analytics')
def get_analytics():
    """Get analytics data with optional filtering"""
    playlist_id = request.args.get('playlist', 'all')
    timeframe = request.args.get('timeframe', 'all')
    
    try:
        # Get total skips with filters
        total_skips = get_total_skips(playlist_id, timeframe)
        
        # Get skip trends (you might want to implement this in edit_tables.py)
        skip_trends = get_skip_trends(playlist_id, timeframe)
        
        return {
            'total_skips': total_skips,
            'skip_trends': skip_trends
        }
    except Exception as e:
        return {'error': str(e)}, 500
    
@app.route('/api/skipped-songs')
def get_skipped_songs():
    """Get list of skipped songs with optional filtering"""
    playlist_id = request.args.get('playlist', 'all')
    timeframe = request.args.get('timeframe', 'all')
    
    try:
        # Get skipped songs with filters (implement in edit_tables.py)
        songs = get_skipped_songs_with_filters(playlist_id, timeframe)
        return songs
    except Exception as e:
        return {'error': str(e)}, 500
    
@app.route('/api/delete-songs', methods=['POST'])
def delete_songs():
    """Delete songs from playlists"""
    token_info = session.get('token_info', {})
    if not token_info:
        return {'error': 'Not authenticated'}, 401
    
    data = request.get_json()
    song_ids = data.get('songIds', [])
    
    if not song_ids:
        return {'error': 'No songs provided'}, 400
    
    try:
        # Check token expiration and refresh if needed
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
            
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Get user's playlists to find songs and remove them
        playlists = sp.current_user_playlists()
        removed_count = 0
        
        for playlist in playlists['items']:
            # Skip if playlist is not owned by user
            if playlist['owner']['id'] != sp.current_user()['id']:
                continue
                
            try:
                # Get playlist tracks
                results = sp.playlist_tracks(playlist['id'])
                tracks_to_remove = []
                
                for item in results['items']:
                    if item['track'] and item['track']['id'] in song_ids:
                        tracks_to_remove.append(item['track']['uri'])
                
                # Remove tracks from playlist
                if tracks_to_remove:
                    sp.playlist_remove_all_occurrences_of_items(playlist['id'], tracks_to_remove)
                    removed_count += len(tracks_to_remove)
                    print(f"Removed {len(tracks_to_remove)} songs from playlist: {playlist['name']}")
                    
            except Exception as playlist_error:
                print(f"Error processing playlist {playlist['name']}: {playlist_error}")
                continue

        # Also remove from skip tracking database
        remove_songs_from_tracking(song_ids)
        
        return {'message': f'Removed {removed_count} song instances from playlists', 'removed_count': removed_count}
        
    except Exception as e:
        return {'error': str(e)}, 500
    
@app.route('/api/database-stats')
def get_database_stats():
    """Get basic database statistics"""
    try:
        connection = sqlite3.connect('SpotifyProject/Spotify.db')
        cursor = connection.cursor()
        
        # Total songs tracked
        cursor.execute('SELECT COUNT(*) FROM skips')
        total_songs = cursor.fetchone()[0]
        
        # Total skips
        cursor.execute('SELECT SUM(SkipCount) FROM skips')
        total_skips = cursor.fetchone()[0] or 0
        
        # Most skipped song
        cursor.execute('SELECT SongName, SkipCount FROM skips ORDER BY SkipCount DESC LIMIT 1')
        most_skipped = cursor.fetchone()
        
        connection.close()
        
        return {
            'total_songs': total_songs,
            'total_skips': total_skips,
            'most_skipped_song': {
                'name': most_skipped[0] if most_skipped else 'None',
                'skips': most_skipped[1] if most_skipped else 0
            }
        }
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    initialize_database()
    app.run(port=8888)