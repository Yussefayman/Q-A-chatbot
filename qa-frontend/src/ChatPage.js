<<<<<<< HEAD
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, Send, LogOut, User, FileText, X, Menu, Trash2 } from 'lucide-react';
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
  const [deletingDocs, setDeletingDocs] = useState(new Set()); // Track which docs are being deleted
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
        console.log('Documents fetched:', docs);
      } else {
        console.error('Failed to fetch documents:', response.status);
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
      
      if (response.ok) {
        // Add bot response
        const botMessage = { 
          type: 'bot', 
          content: data.answer, 
          id: Date.now() + 1,
          sources: data.sources || [],
          confidence: data.confidence_score || 0
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const errorMessage = { 
          type: 'bot', 
          content: data.detail || 'Sorry, something went wrong.', 
          id: Date.now() + 1 
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error asking question:', error);
      const errorMessage = { 
        type: 'bot', 
        content: 'Sorry, something went wrong. Please try again.', 
        id: Date.now() + 1 
      };
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
      
      const data = await response.json();
      
      if (response.ok) {
        const uploadMessage = { 
          type: 'system', 
          content: `File "${file.name}" uploaded successfully! Created ${data.chunks_created} chunks.`, 
          id: Date.now() 
        };
        setMessages(prev => [...prev, uploadMessage]);
        // Refresh documents list
        await fetchDocuments();
      } else {
        const errorMessage = { 
          type: 'system', 
          content: `Upload failed: ${data.detail || 'Unknown error'}`, 
          id: Date.now() 
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = { 
        type: 'system', 
        content: 'Upload failed. Please try again.', 
        id: Date.now() 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [fetchDocuments]);

  const handleDeleteDocument = useCallback(async (docId, docName) => {
    // Confirm deletion
    if (!window.confirm(`Are you sure you want to delete "${docName}"? This will remove it from your knowledge base permanently.`)) {
      return;
    }

    // Add to deleting set to show loading state
    setDeletingDocs(prev => new Set(prev).add(docId));
    
    try {
      const token = localStorage.getItem('token');
      console.log(`Deleting document ${docId} (${docName})`);
      
      const response = await fetch(`${API_BASE}/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log('Delete response:', data);
        
        // Immediately remove from local state for better UX
        setDocuments(prev => prev.filter(doc => doc.id !== docId));
        
        // Add system message with details
        const deleteMessage = { 
          type: 'system', 
          content: `Document "${docName}" deleted successfully! Removed ${data.vector_chunks_deleted || 0} chunks from knowledge base.`, 
          id: Date.now() 
        };
        setMessages(prev => [...prev, deleteMessage]);
        
        // Refresh documents list to ensure consistency
        setTimeout(() => fetchDocuments(), 500);
        
      } else {
        console.error('Delete failed:', response.status, data);
        const errorMessage = { 
          type: 'system', 
          content: `Failed to delete document: ${data.detail || 'Unknown error'}`, 
          id: Date.now() 
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Delete error:', error);
      const errorMessage = { 
        type: 'system', 
        content: 'Failed to delete document. Please try again.', 
        id: Date.now() 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // Remove from deleting set
      setDeletingDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
    }
  }, [fetchDocuments]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="chat-container">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h3>Your Documents</h3>
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <Menu size={20} />
          </button>
        </div>
        
        <div className="documents-list">
          {documents.length === 0 ? (
            <div className="no-documents">
              <FileText size={48} className="text-gray-400" />
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            documents.map((doc) => (
              <div key={doc.id} className={`document-item ${deletingDocs.has(doc.id) ? 'deleting' : ''}`}>
                <div className="document-info">
                  <FileText size={16} />
                  <div className="document-details">
                    <div className="document-name" title={doc.filename}>
                      {doc.filename}
                    </div>
                    <div className="document-meta">
                      {formatFileSize(doc.file_size)} • {doc.chunks_count} chunks
                    </div>
                    <div className="document-date">
                      {new Date(doc.upload_time).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                  className="delete-btn"
                  title="Delete document"
                  disabled={deletingDocs.has(doc.id)}
                >
                  {deletingDocs.has(doc.id) ? (
                    <div className="spinner" />
                  ) : (
                    <X size={16} />
                  )}
                </button>
              </div>
            ))
          )}
        </div>

        {/* Upload button */}
        <div className="upload-section">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleUpload(e.target.files[0])}
            accept=".txt,.pdf"
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="upload-btn"
            disabled={loading}
          >
            <Upload size={16} />
            {loading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>
      </div>

      {/* Main chat area */}
      <div className="chat-main">
        {/* Header */}
        <div className="chat-header">
          <div className="header-left">
            <h1>QuestAI</h1>
            {/* Show current document count in header */}
            {documents.length > 0 && (
              <span className="document-count">
                {documents.length} document{documents.length !== 1 ? 's' : ''} loaded
              </span>
            )}
          </div>
          
          <div className="header-right">
            <span className="user-info">
              <User size={16} />
              {user?.email}
            </span>
            <button onClick={handleLogout} className="logout-btn">
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Welcome to QuestAI!</h2>
              <p>Upload documents and ask questions to get AI-powered answers.</p>
              {documents.length === 0 ? (
                <p>Start by uploading a document using the sidebar.</p>
              ) : (
                <p>You have {documents.length} document{documents.length !== 1 ? 's' : ''} ready. Ask me anything!</p>
              )}
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-content">
                  {message.content}
                  {message.sources && message.sources.length > 0 && (
                    <div className="message-sources">
                      <small>Sources: {message.sources.join(', ')}</small>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="message bot">
              <div className="message-content typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="input-container">
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
              placeholder={documents.length > 0 ? "Ask me anything about your documents..." : "Upload a document first, then ask questions..."}
              disabled={loading}
              className="message-input"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim() || documents.length === 0}
              className="send-btn"
              title={documents.length === 0 ? "Upload a document first" : "Send message"}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

=======
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

>>>>>>> 8418618627f42de55bd38fc34e29bb43be2edf37
export default ChatPage;