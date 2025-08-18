import sqlite3
from datetime import datetime, timedelta

def add_skip_with_artist(song_id, song_name, artist_name=None):
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()

    # Check if the song exists
    cursor.execute('SELECT SkipCount FROM skips WHERE SongID = ?', (song_id,))
    result = cursor.fetchone()

    if result:
        cursor.execute('''UPDATE skips 
                         SET SkipCount = SkipCount + 1, 
                             LastSkipped = ?,
                             ArtistName = COALESCE(ArtistName, ?)
                         WHERE SongID = ?''', 
                      (datetime.now().isoformat(), artist_name, song_id))
    else:
        cursor.execute('''INSERT INTO skips 
                         (SongID, SongName, SkipCount, LastSkipped, ArtistName) 
                         VALUES (?, ?, ?, ?, ?)''', 
                      (song_id, song_name, 1, datetime.now().isoformat(), artist_name))

    connection.commit()
    connection.close()

def get_total_skips(playlist_id='all', timeframe='all'):
    """Get total number of skips with optional filtering"""
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()
    
    query = "SELECT SUM(SkipCount) FROM skips"
    params = []
    conditions = []
    
    # Add timeframe filter if specified
    if timeframe != 'all':
        date_filter = get_date_filter(timeframe)
        conditions.append("LastSkipped >= ?")
        params.append(date_filter.isoformat())
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    connection.close()
    
    return result[0] if result[0] else 0

def get_skipped_songs_with_filters(playlist_id='all', timeframe='all'):
    """Get skipped songs with filtering options"""
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()
    
    query = """
    SELECT SongID, SongName, SkipCount, LastSkipped
    FROM skips
    """
    params = []
    conditions = []
    
    # Add timeframe filter if specified
    if timeframe != 'all':
        date_filter = get_date_filter(timeframe)
        conditions.append("LastSkipped >= ?")
        params.append(date_filter.isoformat())
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY SkipCount DESC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    
    # Convert to list of dictionaries for JSON response
    songs = []
    for row in results:
        songs.append({
            'track_id': row[0],
            'track_name': row[1],
            'artist_name': 'Unknown',  # You might want to add this to your schema later
            'skip_count': row[2],
            'last_skipped': row[3]
        })
    
    return songs

def get_skip_trends(playlist_id='all', timeframe='all'):
    """Get skip trends over time - basic implementation"""
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()
    
    # Simple trend data - you can enhance this later
    query = """
    SELECT DATE(LastSkipped) as skip_date, SUM(SkipCount) as daily_skips
    FROM skips
    WHERE LastSkipped IS NOT NULL
    """
    params = []
    
    if timeframe != 'all':
        date_filter = get_date_filter(timeframe)
        query += " AND LastSkipped >= ?"
        params.append(date_filter.isoformat())
    
    query += " GROUP BY DATE(LastSkipped) ORDER BY skip_date DESC LIMIT 30"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    
    trends = []
    for row in results:
        trends.append({
            'date': row[0],
            'skips': row[1]
        })
    
    return trends

def get_date_filter(timeframe):
    """Convert timeframe to date filter"""
    now = datetime.now()
    
    if timeframe == 'week':
        return now - timedelta(weeks=1)
    elif timeframe == 'month':
        return now - timedelta(days=30)
    elif timeframe == 'year':
        return now - timedelta(days=365)
    else:
        return datetime.min  # Return all time

def remove_songs_from_tracking(song_ids):
    """Remove songs from skip tracking database"""
    if not song_ids:
        return
        
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()
    
    # Create placeholders for the IN clause
    placeholders = ','.join(['?' for _ in song_ids])
    query = f"DELETE FROM skips WHERE SongID IN ({placeholders})"
    
    cursor.execute(query, song_ids)
    connection.commit()
    connection.close()

def initialize_database():
    """Initialize the database with the updated schema"""
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()
    
    # Create the skips table with LastSkipped column if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skips (
        SongID TEXT PRIMARY KEY,
        SongName TEXT NOT NULL,
        SkipCount INTEGER NOT NULL DEFAULT 1,
        LastSkipped TEXT
    )
    ''')
    
    # Add LastSkipped column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE skips ADD COLUMN LastSkipped TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    connection.commit()
    connection.close()

# Helper function to get song details from Spotify API
def get_song_details_from_spotify(sp, track_id):
    """Get additional song details from Spotify API"""
    try:
        track = sp.track(track_id)
        return {
            'artist_name': track['artists'][0]['name'] if track['artists'] else 'Unknown',
            'album_name': track['album']['name'],
            'duration': track['duration_ms']
        }
    except:
        return {
            'artist_name': 'Unknown',
            'album_name': 'Unknown',
            'duration': 0
        }