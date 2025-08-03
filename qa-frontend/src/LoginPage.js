<<<<<<< HEAD
import React, { useState } from 'react';
import { Lock, Mail } from 'lucide-react';
import './Login.css';

// API base URL - adjust this to match your FastAPI server
const API_BASE = 'http://localhost:8000';

// Login Component
const LoginForm = ({ onLogin, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const onSubmit = (e) => {
    e.preventDefault();
    onLogin(email, password);
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2 className="auth-title">QuestAI</h2>
          <p className="auth-subtitle">Intelligent answers at your fingertips</p>
        </div>
        
        <form onSubmit={onSubmit} className="form">
          <div className="form-group">
            <label className="form-label">
              <Mail className="form-icon" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              required
              autoFocus
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <button type="submit" className="btn btn-primary">
            Sign In
          </button>
        </form>
        
        <div className="auth-footer">
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="auth-link"
          >
            Don't have an account? Register here
          </button>
        </div>
      </div>
    </div>
  );
};

// Register Component
const RegisterForm = ({ onRegister, onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const onSubmit = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    onRegister(email, password);
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2 className="auth-title">QuestAI</h2>
          <p className="auth-subtitle">Create your account to get started</p>
        </div>
        
        <form onSubmit={onSubmit} className="form">
          <div className="form-group">
            <label className="form-label">
              <Mail className="form-icon" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              required
              autoFocus
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <button type="submit" className="btn btn-success">
            Register
          </button>
        </form>
        
        <div className="auth-footer">
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="auth-link"
          >
            Already have an account? Sign in here
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Auth App Component
const LoginPage = ({ onLoginSuccess }) => {
  const [currentView, setCurrentView] = useState('login'); // 'login' or 'register'

  const handleLogin = async (email, password) => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify({ email }));
      
      // Call success handler to update App.js state
      onLoginSuccess();
      
    } catch (error) {
      alert('Login failed: ' + error.message);
    }
  };

  const handleRegister = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) throw new Error('Registration failed');
      
      alert('Registration successful! Please login.');
      setCurrentView('login');
    } catch (error) {
      alert('Registration failed: ' + error.message);
    }
  };

  if (currentView === 'login') {
    return (
      <LoginForm 
        onLogin={handleLogin}
        onSwitchToRegister={() => setCurrentView('register')}
      />
    );
  } else {
    return (
      <RegisterForm 
        onRegister={handleRegister}
        onSwitchToLogin={() => setCurrentView('login')}
      />
    );
  }
};

=======
import React, { useState } from 'react';
import { Lock, Mail } from 'lucide-react';
import './Login.css';

// API base URL - adjust this to match your FastAPI server
const API_BASE = 'http://localhost:8000';

// Login Component
const LoginForm = ({ onLogin, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const onSubmit = (e) => {
    e.preventDefault();
    onLogin(email, password);
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2 className="auth-title">QuestAI</h2>
          <p className="auth-subtitle">Intelligent answers at your fingertips</p>
        </div>
        
        <form onSubmit={onSubmit} className="form">
          <div className="form-group">
            <label className="form-label">
              <Mail className="form-icon" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              required
              autoFocus
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <button type="submit" className="btn btn-primary">
            Sign In
          </button>
        </form>
        
        <div className="auth-footer">
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="auth-link"
          >
            Don't have an account? Register here
          </button>
        </div>
      </div>
    </div>
  );
};

// Register Component
const RegisterForm = ({ onRegister, onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const onSubmit = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    onRegister(email, password);
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2 className="auth-title">QuestAI</h2>
          <p className="auth-subtitle">Create your account to get started</p>
        </div>
        
        <form onSubmit={onSubmit} className="form">
          <div className="form-group">
            <label className="form-label">
              <Mail className="form-icon" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              required
              autoFocus
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">
              <Lock className="form-icon" />
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="form-input"
              required
              dir="ltr"
            />
          </div>
          
          <button type="submit" className="btn btn-success">
            Register
          </button>
        </form>
        
        <div className="auth-footer">
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="auth-link"
          >
            Already have an account? Sign in here
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Auth App Component
const LoginPage = ({ onLoginSuccess }) => {
  const [currentView, setCurrentView] = useState('login'); // 'login' or 'register'

  const handleLogin = async (email, password) => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify({ email }));
      
      // Call success handler to update App.js state
      onLoginSuccess();
      
    } catch (error) {
      alert('Login failed: ' + error.message);
    }
  };

  const handleRegister = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) throw new Error('Registration failed');
      
      alert('Registration successful! Please login.');
      setCurrentView('login');
    } catch (error) {
      alert('Registration failed: ' + error.message);
    }
  };

  if (currentView === 'login') {
    return (
      <LoginForm 
        onLogin={handleLogin}
        onSwitchToRegister={() => setCurrentView('register')}
      />
    );
  } else {
    return (
      <RegisterForm 
        onRegister={handleRegister}
        onSwitchToLogin={() => setCurrentView('login')}
      />
    );
  }
};

>>>>>>> 8418618627f42de55bd38fc34e29bb43be2edf37
export default LoginPage;