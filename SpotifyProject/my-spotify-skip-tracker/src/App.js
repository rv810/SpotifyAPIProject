import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(to right, #4f46e5, #8b5cf6)',
        margin: 0,
        padding: 0
      }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}