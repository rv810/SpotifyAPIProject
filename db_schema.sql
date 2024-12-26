import sqlite3

connection = sqlite3.connect('Spotify.db')

cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS skips (
        SongID TEXT PRIMARY,
        SongName TEXT NOT NULL,
        SkipCount INTEGER AUTOINCREMENT DEFAULT 0,
        PlaylistName TEXT,
    )
''')

connection.commit()

connection.close()