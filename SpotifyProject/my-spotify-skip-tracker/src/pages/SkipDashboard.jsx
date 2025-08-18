import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Trash2, SkipForward, TrendingUp, Music, Filter, List } from 'lucide-react';
import './SkipDashboard.css';

const SkipDashboard = () => {
  const [skippedSongs, setSkippedSongs] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [selectedPlaylist, setSelectedPlaylist] = useState('all');
  const [timeFilter, setTimeFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedSongs, setSelectedSongs] = useState(new Set());
  const [playlists, setPlaylists] = useState([]);

  // Fetch data from your backend
  useEffect(() => {
    fetchData();
  }, [selectedPlaylist, timeFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch analytics data
      const analyticsRes = await fetch(`/api/analytics?playlist=${selectedPlaylist}&timeframe=${timeFilter}`);
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);

      // Fetch skipped songs
      const songsRes = await fetch(`/api/skipped-songs?playlist=${selectedPlaylist}&timeframe=${timeFilter}`);
      const songsData = await songsRes.json();
      setSkippedSongs(songsData);

      // Fetch playlists
      const playlistsRes = await fetch('/playlists');
      const playlistsData = await playlistsRes.json();
      setPlaylists(playlistsData.items || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSongs = async () => {
    if (selectedSongs.size === 0) return;
    
    try {
      const response = await fetch('/api/delete-songs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ songIds: Array.from(selectedSongs) })
      });
      
      if (response.ok) {
        setSelectedSongs(new Set());
        fetchData();
        alert('Songs deleted successfully!');
      }
    } catch (error) {
      console.error('Error deleting songs:', error);
      alert('Error deleting songs');
    }
  };

  const toggleSongSelection = (songId) => {
    const newSelected = new Set(selectedSongs);
    if (newSelected.has(songId)) {
      newSelected.delete(songId);
    } else {
      newSelected.add(songId);
    }
    setSelectedSongs(newSelected);
  };

  const selectAllHighSkips = () => {
    const highSkipSongs = skippedSongs
      .filter(song => song.skip_count >= 3)
      .map(song => song.track_id);
    setSelectedSongs(new Set(highSkipSongs));
  };

  // Prepare chart data
  const chartData = skippedSongs.slice(0, 10).map(song => ({
    name: song.track_name.length > 20 ? song.track_name.substring(0, 20) + '...' : song.track_name,
    skips: song.skip_count
  }));

  const skipDistribution = [
    { name: '1-2 Skips', value: skippedSongs.filter(s => s.skip_count <= 2).length, color: '#10b981' },
    { name: '3-5 Skips', value: skippedSongs.filter(s => s.skip_count >= 3 && s.skip_count <= 5).length, color: '#f59e0b' },
    { name: '6+ Skips', value: skippedSongs.filter(s => s.skip_count > 5).length, color: '#ef4444' }
  ];

  if (loading) {
    return (
      <div className="skip-dashboard">
        <div className="dashboard-container">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white text-xl">Loading your skip analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="skip-dashboard">
      <div className="dashboard-container">
        {/* Header */}
        <div className="dashboard-header">
          <h1 className="dashboard-title">
            <span style={{ fontSize: '2rem' }}>♫</span>
            Spotify Skip Analytics
          </h1>
          <p className="dashboard-subtitle">Discover your listening patterns and clean up your playlists</p>
        </div>

        {/* Filters */}
        <div className="filter-container">
          <select 
            value={selectedPlaylist}
            onChange={(e) => setSelectedPlaylist(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Playlists</option>
            {playlists.map(playlist => (
              <option key={playlist.id} value={playlist.id}>{playlist.name}</option>
            ))}
          </select>
          
          <select 
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Time</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-info">
                <h3>Total Skips</h3>
                <div className="stat-value">{analytics.total_skips || 0}</div>
              </div>
              <SkipForward className="stat-icon" />
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-info">
                <h3>Songs Tracked</h3>
                <div className="stat-value">{skippedSongs.length}</div>
              </div>
              <Music className="stat-icon" />
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-info">
                <h3>Avg Skips/Song</h3>
                <div className="stat-value">
                  {skippedSongs.length > 0 ? (analytics.total_skips / skippedSongs.length).toFixed(1) : '0.0'}
                </div>
              </div>
              <TrendingUp className="stat-icon" />
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-info">
                <h3>High Skip Songs</h3>
                <div className="stat-value">
                  {skippedSongs.filter(s => s.skip_count >= 3).length}
                </div>
              </div>
              <Filter className="stat-icon" />
            </div>
          </div>
        </div>

        {/* Top Skipped Songs Section */}
        <div className="top-skipped-section">
          <h3 className="top-skipped-title">Top 10 Most Skipped Songs</h3>
          <div className="songs-list-container">
            {skippedSongs.length > 0 ? (
              <div className="w-full">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis 
                      dataKey="name" 
                      stroke="#4a5568" 
                      fontSize={12} 
                      angle={-45} 
                      textAnchor="end" 
                      height={80} 
                    />
                    <YAxis stroke="#4a5568" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#ffffff', 
                        border: '1px solid #e2e8f0', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                      }}
                      labelStyle={{ color: '#1a1a1a' }}
                    />
                    <Bar dataKey="skips" fill="#667eea" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                <List className="empty-state-icon mx-auto" />
                <p>No skipped songs found for the selected filters.</p>
              </div>
            )}
          </div>
        </div>

        {/* Additional Charts Section (Hidden by default but available) */}
        {skippedSongs.length > 0 && (
          <div className="top-skipped-section mt-8">
            <h3 className="top-skipped-title">Skip Distribution</h3>
            <div className="songs-list-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={skipDistribution}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {skipDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Songs Table (Hidden by default but available) */}
        {skippedSongs.length > 0 && (
          <div className="top-skipped-section mt-8">
            <div className="flex justify-between items-center mb-6">
              <h3 className="top-skipped-title mb-0">Skipped Songs</h3>
              <div className="flex gap-3">
                <button 
                  onClick={selectAllHighSkips}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm transition-colors"
                >
                  Select High Skips (3+)
                </button>
                <button 
                  onClick={handleDeleteSongs}
                  disabled={selectedSongs.size === 0}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg flex items-center gap-2 text-sm transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Selected ({selectedSongs.size})
                </button>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-300">
                    <th className="pb-3 text-gray-600 font-medium">
                      <input 
                        type="checkbox" 
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedSongs(new Set(skippedSongs.map(s => s.track_id)));
                          } else {
                            setSelectedSongs(new Set());
                          }
                        }}
                        className="mr-2"
                      />
                      Select
                    </th>
                    <th className="pb-3 text-gray-600 font-medium">Song</th>
                    <th className="pb-3 text-gray-600 font-medium">Artist</th>
                    <th className="pb-3 text-gray-600 font-medium">Skips</th>
                    <th className="pb-3 text-gray-600 font-medium">Last Skipped</th>
                  </tr>
                </thead>
                <tbody>
                  {skippedSongs.map((song, index) => (
                    <tr key={song.track_id} className={`border-b border-gray-200 ${index % 2 === 0 ? 'bg-gray-50' : ''}`}>
                      <td className="py-3">
                        <input 
                          type="checkbox"
                          checked={selectedSongs.has(song.track_id)}
                          onChange={() => toggleSongSelection(song.track_id)}
                          className="mr-2"
                        />
                      </td>
                      <td className="py-3 text-gray-900 font-medium">{song.track_name}</td>
                      <td className="py-3 text-gray-600">{song.artist_name || 'Unknown'}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          song.skip_count >= 6 ? 'bg-red-100 text-red-800' :
                          song.skip_count >= 3 ? 'bg-orange-100 text-orange-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {song.skip_count}
                        </span>
                      </td>
                      <td className="py-3 text-gray-500 text-sm">
                        {song.last_skipped ? new Date(song.last_skipped).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkipDashboard;