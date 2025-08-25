#!/usr/bin/env python3
"""
Whis Frontend - Comprehensive Web Interface
Features: Chat with Whis, Action Approvals, SIEM Integration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import json
import uuid
import logging
from datetime import datetime, timedelta
import os
from functools import wraps
import sqlite3
import hashlib
import secrets

# Initialize Flask app with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WHIS_API_URL = os.environ.get('WHIS_API_URL', 'http://localhost:8003')
LIMACHARLIE_API_KEY = os.environ.get('LIMACHARLIE_API_KEY', '')
LIMACHARLIE_ORG = os.environ.get('LIMACHARLIE_ORG', '')
SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '')
SPLUNK_USERNAME = os.environ.get('SPLUNK_USERNAME', '')
SPLUNK_PASSWORD = os.environ.get('SPLUNK_PASSWORD', '')

# Database initialization
def init_db():
    """Initialize SQLite database for conversations and approvals"""
    conn = sqlite3.connect('whis_frontend.db')
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message TEXT NOT NULL,
            response TEXT,
            response_time REAL,
            session_id TEXT
        )
    ''')
    
    # Action approvals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_approvals (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            action_type TEXT NOT NULL,
            action_data TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME,
            approved_by TEXT,
            executed_at DATETIME,
            execution_result TEXT
        )
    ''')
    
    # User sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class WhisInterface:
    def __init__(self):
        self.whis_api_url = WHIS_API_URL
        
    def query_whis(self, message, user_id, conversation_id):
        """Send query to Whis API and return response"""
        try:
            payload = {
                "event_data": {
                    "search_name": f"Web Interface Query - {user_id}",
                    "host": "whis-frontend",
                    "severity": "medium",
                    "description": message,
                    "user": user_id,
                    "conversation_id": conversation_id
                }
            }
            
            start_time = datetime.now()
            response = requests.post(
                f"{self.whis_api_url}/explain",
                json=payload,
                timeout=120
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                result['response_time'] = response_time
                return result
            else:
                return {
                    "error": f"Whis API returned status {response.status_code}",
                    "response_time": response_time
                }
                
        except Exception as e:
            return {
                "error": f"Failed to contact Whis: {str(e)}",
                "response_time": 0
            }

class LimaCharlieInterface:
    def __init__(self):
        self.api_key = LIMACHARLIE_API_KEY
        self.org = LIMACHARLIE_ORG
        self.base_url = "https://api.limacharlie.io"
        
    def get_recent_detections(self, hours=24, limit=100):
        """Get recent LimaCharlie detections"""
        if not self.api_key or not self.org:
            return {"error": "LimaCharlie credentials not configured"}
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            params = {
                "start": int(start_time.timestamp()),
                "end": int(end_time.timestamp()),
                "limit": limit
            }
            
            response = requests.get(
                f"{self.base_url}/v1/{self.org}/detections",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"LimaCharlie API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"LimaCharlie connection failed: {str(e)}"}
    
    def get_sensor_data(self, sensor_id, hours=1):
        """Get sensor telemetry data"""
        if not self.api_key or not self.org:
            return {"error": "LimaCharlie credentials not configured"}
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/{self.org}/sensors/{sensor_id}/timeline",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Sensor data error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Sensor data failed: {str(e)}"}

class SplunkInterface:
    def __init__(self):
        self.host = SPLUNK_HOST
        self.username = SPLUNK_USERNAME
        self.password = SPLUNK_PASSWORD
        self.session_key = None
        
    def authenticate(self):
        """Authenticate with Splunk and get session key"""
        if not all([self.host, self.username, self.password]):
            return False
            
        try:
            auth_url = f"https://{self.host}:8089/services/auth/login"
            auth_data = {
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(
                auth_url,
                data=auth_data,
                verify=True,  # SSL verification enabled for security
                timeout=30
            )
            
            if response.status_code == 200:
                # Extract session key from XML response - using defusedxml for security
                try:
                    from defusedxml import ElementTree as ET
                except ImportError:
                    import xml.etree.ElementTree as ET
                    logger.warning("defusedxml not available, using standard ElementTree")
                root = ET.fromstring(response.content)
                session_key = root.find('.//sessionKey').text
                self.session_key = session_key
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Splunk authentication failed: {e}")
            return False
    
    def search(self, query, earliest_time="-24h", latest_time="now", count=100):
        """Execute Splunk search and return results"""
        if not self.session_key and not self.authenticate():
            return {"error": "Splunk authentication failed"}
            
        try:
            search_url = f"https://{self.host}:8089/services/search/jobs/oneshot"
            
            headers = {
                'Authorization': f'Splunk {self.session_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            search_data = {
                'search': query,
                'earliest_time': earliest_time,
                'latest_time': latest_time,
                'count': count,
                'output_mode': 'json'
            }
            
            response = requests.post(
                search_url,
                headers=headers,
                data=search_data,
                verify=True,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Splunk search error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Splunk search failed: {str(e)}"}

# Initialize interfaces
whis_interface = WhisInterface()
lc_interface = LimaCharlieInterface()
splunk_interface = SplunkInterface()

# Routes
@app.route('/')
@require_auth
def dashboard():
    """Main dashboard with overview"""
    return render_template('dashboard.html', user_id=session['user_id'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login - in production, integrate with your SSO"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication - replace with your auth system
        if username and password:  # Add proper validation here
            session['user_id'] = username
            session['session_id'] = str(uuid.uuid4())
            
            # Store session in database
            conn = sqlite3.connect('whis_frontend.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_sessions (session_id, user_id, metadata)
                VALUES (?, ?, ?)
            ''', (session['session_id'], username, json.dumps({'login_method': 'form'})))
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat')
@require_auth
def chat():
    """Whis chat interface"""
    return render_template('chat.html', user_id=session['user_id'])

@app.route('/approvals')
@require_auth
def approvals():
    """Action approval interface"""
    # Get pending approvals
    conn = sqlite3.connect('whis_frontend.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, action_type, action_data, created_at, conversation_id
        FROM action_approvals
        WHERE status = 'pending'
        ORDER BY created_at DESC
    ''')
    pending_approvals = cursor.fetchall()
    conn.close()
    
    return render_template('approvals.html', 
                         approvals=pending_approvals,
                         user_id=session['user_id'])

@app.route('/logs')
@require_auth
def logs():
    """SIEM logs viewer"""
    return render_template('logs.html', user_id=session['user_id'])

@app.route('/test')
def test_page():
    """Diagnostic test page - no auth required"""
    return render_template_string(open('static/test.html').read())

@app.route('/api/conversation', methods=['POST'])
@require_auth
def api_conversation():
    """API endpoint for Whis conversations"""
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Generate conversation ID
    conversation_id = str(uuid.uuid4())
    user_id = session['user_id']
    
    # Query Whis
    response = whis_interface.query_whis(message, user_id, conversation_id)
    
    # Store conversation in database
    conn = sqlite3.connect('whis_frontend.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (id, user_id, message, response, response_time, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (conversation_id, user_id, message, json.dumps(response), 
          response.get('response_time', 0), session.get('session_id')))
    
    # Check if response contains actions that need approval
    if 'artifacts' in response or 'how' in response:
        approval_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO action_approvals (id, conversation_id, action_type, action_data)
            VALUES (?, ?, ?, ?)
        ''', (approval_id, conversation_id, 'whis_actions', json.dumps(response)))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "conversation_id": conversation_id,
        "response": response
    })

@app.route('/api/approve_action', methods=['POST'])
@require_auth
def api_approve_action():
    """Approve an action for execution"""
    data = request.get_json()
    approval_id = data.get('approval_id')
    action = data.get('action')  # 'approve' or 'reject'
    
    if not approval_id or action not in ['approve', 'reject']:
        return jsonify({"error": "Invalid request"}), 400
    
    conn = sqlite3.connect('whis_frontend.db')
    cursor = conn.cursor()
    
    # Update approval status
    cursor.execute('''
        UPDATE action_approvals 
        SET status = ?, approved_at = ?, approved_by = ?
        WHERE id = ?
    ''', (action + 'd', datetime.now(), session['user_id'], approval_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "action": action})

@app.route('/api/health')
def api_health():
    """Simple health check (no auth required)"""
    return jsonify({
        "status": "healthy",
        "service": "whis-frontend", 
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/test-activity')
@require_auth
def test_activity():
    """Test endpoint to manually trigger activity loading"""
    return jsonify({
        "message": "Activity test endpoint working",
        "timestamp": datetime.now().isoformat(),
        "user": session.get('user_id', 'unknown')
    })

@app.route('/api/status')
@require_auth
def api_status():
    """Get system status"""
    status = {
        "whis_api": "online" if whis_interface.whis_api_url else "offline",
        "limacharlie": "configured" if LIMACHARLIE_API_KEY else "not_configured", 
        "splunk": "configured" if SPLUNK_HOST else "not_configured",
        "database": "online",
        "overall": "operational"
    }
    return jsonify(status)

@app.route('/api/limacharlie/detections')
@require_auth
def api_lc_detections():
    """Get recent LimaCharlie detections"""
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    detections = lc_interface.get_recent_detections(hours, limit)
    return jsonify(detections)

@app.route('/api/limacharlie/sensor/<sensor_id>')
@require_auth
def api_lc_sensor(sensor_id):
    """Get LimaCharlie sensor data"""
    hours = request.args.get('hours', 1, type=int)
    
    sensor_data = lc_interface.get_sensor_data(sensor_id, hours)
    return jsonify(sensor_data)

@app.route('/api/splunk/search', methods=['POST'])
@require_auth
def api_splunk_search():
    """Execute Splunk search"""
    data = request.get_json()
    query = data.get('query', '')
    earliest = data.get('earliest_time', '-24h')
    latest = data.get('latest_time', 'now')
    count = data.get('count', 100)
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    results = splunk_interface.search(query, earliest, latest, count)
    return jsonify(results)

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'user_id' in session:
        join_room(session['user_id'])
        emit('status', {'message': 'Connected to Whis interface'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if 'user_id' in session:
        leave_room(session['user_id'])

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat messages"""
    if 'user_id' not in session:
        return
    
    message = data.get('message', '')
    if not message:
        return
    
    # Process message through Whis
    conversation_id = str(uuid.uuid4())
    user_id = session['user_id']
    
    # Emit thinking status
    emit('whis_thinking', {'conversation_id': conversation_id})
    
    # Query Whis
    response = whis_interface.query_whis(message, user_id, conversation_id)
    
    # Store in database
    conn = sqlite3.connect('whis_frontend.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (id, user_id, message, response, response_time, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (conversation_id, user_id, message, json.dumps(response),
          response.get('response_time', 0), session.get('session_id')))
    conn.commit()
    conn.close()
    
    # Emit response
    emit('whis_response', {
        'conversation_id': conversation_id,
        'message': message,
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start the application
    print("🚀 Starting Whis Frontend Interface...")
    print(f"📡 Whis API: {WHIS_API_URL}")
    print(f"🔍 LimaCharlie: {'✅ Configured' if LIMACHARLIE_API_KEY else '❌ Not configured'}")
    print(f"📊 Splunk: {'✅ Configured' if SPLUNK_HOST else '❌ Not configured'}")
    print("🌐 Access at: http://localhost:5000")
    
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=5000, debug=debug_mode)