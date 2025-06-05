import Button from '@mui/material/Button';
import { useNavigate } from 'react-router-dom'

export const Dashboard = () => {
  const navigate = useNavigate()

    return ( 
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
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
          <Button variant="contained" style={{
            marginTop: "20px",
            background: "white",
            color: "purple",
            fontFamily: "sans-serif",
            fontWeight: "bold",
          }} onClick={() => navigate("/overview")}>
            View Report
          </Button>
        </div>
    )
}

export default Dashboard;