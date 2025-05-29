export const Dashboard = () => {
    return ( 
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <span style={{
            fontSize: '2rem',
            color: 'white',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            Spotify Track Skipper
          </span>
          <span style={{
            fontSize: '20px',
            color: 'white',
            textAlign: 'center',
            marginTop: '10px'
          }}>
            So that your playlists change as quickly as your taste
          </span>
        </div>
    )
}

export default Dashboard;