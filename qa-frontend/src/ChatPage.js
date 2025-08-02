import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, Send, LogOut, User, FileText, X, Menu } from 'lucide-react';
import './Chat.css';

// API base URL - adjust this to match your FastAPI server
const API_BASE = 'http://localhost:8000';

const ChatPage = ({ onLogout }) => {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const fileInputRef = useRef();

  // Check if user is logged in and fetch documents
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
      fetchDocuments();
    }
  }, []);

  // Fetch documents from API
  const fetchDocuments = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/documents`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const docs = await response.json();
        setDocuments(docs);
      }
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    onLogout(); // Call the logout handler from App.js
  }, [onLogout]);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage = { type: 'user', content: input, id: Date.now() };
    setMessages(prev => [...prev, userMessage]);
    
    const question = input;
    setInput('');
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question })
      });
      
      const data = await response.json();
      
      // Add bot response
      const botMessage = { type: 'bot', content: data.answer, id: Date.now() + 1 };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { type: 'bot', content: 'Sorry, something went wrong.', id: Date.now() + 1 };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [input]);

  const handleUpload = useCallback(async (file) => {
    if (!file) return;
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.ok) {
        const uploadMessage = { type: 'system', content: `File "${file.name}" uploaded successfully!`, id: Date.now() };
        setMessages(prev => [...prev, uploadMessage]);
        // Refresh documents list
        fetchDocuments();
      }
    } catch (error) {
      const errorMessage = { type: 'system', content: 'Upload failed. Please try again.', id: Date.now() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [fetchDocuments]);

  const handleDeleteDocument = useCallback(async (docId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        // Refresh documents list
        fetchDocuments();
        // Add system message
        const deleteMessage = { type: 'system', content: 'Document deleted successfully!', id: Date.now() };
        setMessages(prev => [...prev, deleteMessage]);
      }
    } catch (error) {
      const errorMessage = { type: 'system', content: 'Failed to delete document.', id: Date.now() };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [fetchDocuments]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="sidebar-toggle"
          >
            <Menu size={20} />
          </button>
          <h1 className="chat-title">QuestAI</h1>
        </div>
        <div className="user-info">
          <span className="user-email">
            <User className="user-icon" />
            {user?.email}
          </span>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut className="logout-icon" />
            Logout
          </button>
        </div>
      </div>

      <div className="chat-content">
        {/* Sidebar */}
        <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <div className="sidebar-header">
            <h3 className="sidebar-title">Your Documents</h3>
          </div>
          
          <div className="documents-list">
            {documents.length === 0 ? (
              <p className="no-documents">No documents uploaded yet</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="document-item">
                  <div className="document-info">
                    <FileText className="document-icon" />
                    <span className="document-name" title={doc.name}>{doc.name}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="delete-btn"
                    title="Delete document"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="main-chat">
          {/* Messages */}
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="empty-state">
                Start a conversation by typing below!
              </div>
            )}
            
            {messages.map(message => (
              <div 
                key={message.id}
                className={`message-wrapper ${message.type}`}
              >
                <div className={`message ${message.type}`}>
                  {message.content}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="message-wrapper bot">
                <div className="message bot">
                  Typing...
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={loading}
                className="message-input"
                dir="ltr"
              />
              
              <input
                ref={fileInputRef}
                type="file"
                onChange={(e) => handleUpload(e.target.files[0])}
                className="file-input"
                accept=".txt,.pdf,.doc,.docx"
              />
              
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="btn-icon upload"
              >
                <Upload size={20} />
              </button>
              
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="btn-icon send"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;