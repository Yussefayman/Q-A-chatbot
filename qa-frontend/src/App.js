import React, { useState, useEffect } from 'react';
import LoginPage from './LoginPage';
import ChatPage from './ChatPage';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check authentication status on app start
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
    
    setLoading(false);
  }, []);

  // Handle successful login
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
  };

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
      </div>
    );
  }

  // Render appropriate page based on authentication status
  if (isAuthenticated) {
    return <ChatPage onLogout={handleLogout} />;
  } else {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }
};

export default App;