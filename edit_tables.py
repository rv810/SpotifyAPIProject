import sqlite3

def add_skip(song_id, song_name):
    connection = sqlite3.connect('SpotifyProject/Spotify.db')
    cursor = connection.cursor()

    # Check if the song exists
    cursor.execute('SELECT SkipCount FROM skips WHERE SongName = ?', (song_name,))
    result = cursor.fetchone()

    if result:
        cursor.execute('UPDATE skips SET SkipCount = SkipCount + 1 WHERE SongName = ?', (song_name,))

    else:
        cursor.execute('INSERT INTO skips (SongID, SongName, SkipCount) VALUES (?)', (song_id, song_name, 1))

    connection.commit()
    connection.close()