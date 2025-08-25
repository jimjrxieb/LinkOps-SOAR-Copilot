# Whis Frontend - AI Security Copilot Web Interface

A comprehensive web interface for the Whis AI Security Copilot, providing real-time chat interaction, action approval workflows, and SIEM log integration.

## Features

### 🤖 Chat with Whis
- Real-time conversation with the Whis AI
- WebSocket-based communication for instant responses
- Conversation history and context preservation
- Artifact download and action execution

### ✅ Action Approval System
- Review and approve/reject Whis-recommended actions
- Risk assessment and impact analysis
- Audit trail for all approval decisions
- Bulk approval operations

### 📊 SIEM Integration
- **LimaCharlie**: Real-time detection and sensor data
- **Splunk**: Log search and analysis
- Unified log viewer with filtering and search
- Direct log analysis with Whis

### 🔐 Security Features
- User authentication and session management
- Secure API endpoints with authorization
- Audit logging for all user actions
- Rate limiting and input validation

## Quick Start

### Prerequisites
- Python 3.8+
- Running Whis API instance (default: `http://localhost:8003`)
- Optional: LimaCharlie and Splunk credentials for SIEM integration

### Installation & Running

1. **Clone and Navigate**
   ```bash
   cd whis-frontend
   ```

2. **Run with Auto-Setup**
   ```bash
   ./run.sh
   ```
   This will automatically:
   - Create virtual environment
   - Install dependencies
   - Initialize database
   - Start the development server

3. **Access the Interface**
   - Open: http://localhost:5000
   - Login with any username/password (development mode)

### Production Deployment
```bash
./run.sh prod
```

## Configuration

### Environment Variables
```bash
# Core Configuration
export WHIS_API_URL="http://localhost:8003"
export FLASK_SECRET_KEY="your-secret-key"

# LimaCharlie Integration (Optional)
export LIMACHARLIE_API_KEY="your-api-key"
export LIMACHARLIE_ORG="your-org-id"

# Splunk Integration (Optional)  
export SPLUNK_HOST="your-splunk-host"
export SPLUNK_USERNAME="your-username"
export SPLUNK_PASSWORD="your-password"
```

### Database
- Uses SQLite by default (`whis_frontend.db`)
- Automatically initialized on first run
- Stores conversations, approvals, and user sessions

## API Endpoints

### Chat & Conversations
- `POST /api/conversation` - Send message to Whis
- `GET /api/conversation/{id}` - Get conversation details

### Approval System
- `POST /api/approve_action` - Approve/reject actions
- `GET /api/approvals` - List pending approvals

### SIEM Integration
- `GET /api/limacharlie/detections` - Get LimaCharlie detections
- `GET /api/limacharlie/sensor/{id}` - Get sensor data
- `POST /api/splunk/search` - Execute Splunk searches

### System Status
- `GET /api/status` - Get system health status

## Architecture

### Frontend Stack
- **Flask** - Web framework with Jinja2 templating
- **Flask-SocketIO** - Real-time WebSocket communication
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - Icon library
- **SQLite** - Local database for persistence

### Key Components
- `app.py` - Main Flask application with API routes
- `templates/` - HTML templates for all pages
- `static/css/style.css` - Custom styling and themes
- `static/js/whis.js` - Core JavaScript functionality

### Real-time Communication
- WebSocket connection for instant Whis responses
- Live status updates and notifications
- Real-time approval notifications
- System health monitoring

## Usage Guide

### 1. Dashboard
- Overview of security metrics and recent activity
- Quick access to all major functions
- System status indicators
- Threat intelligence summary

### 2. Chat Interface
- Type messages to interact with Whis
- View conversation history
- Download generated artifacts
- Request action approvals

### 3. Approval Workflow
- Review pending actions with risk assessment
- Approve or reject with justification
- Track execution status
- View approval history

### 4. SIEM Logs
- Toggle between LimaCharlie and Splunk sources
- Search and filter logs
- Analyze logs directly with Whis
- Export log data

## Security Considerations

### Authentication
- Currently uses simple form-based auth for development
- Replace with your organization's SSO in production
- Session management with secure cookies
- CSRF protection enabled

### API Security
- All endpoints require authentication
- Input validation and sanitization
- Rate limiting on API calls
- Audit logging for sensitive operations

### Data Protection
- Sensitive data encryption at rest
- Secure WebSocket connections
- No credential storage in browser
- Automatic session timeout

## Development

### Project Structure
```
whis-frontend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── run.sh                # Deployment script
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── dashboard.html    # Dashboard page
│   ├── chat.html         # Chat interface
│   ├── approvals.html    # Approval system
│   ├── logs.html         # SIEM logs
│   └── login.html        # Login page
└── static/              # Static assets
    ├── css/style.css    # Custom styles
    └── js/whis.js       # Core JavaScript
```

### Adding New Features
1. Add route handler in `app.py`
2. Create template in `templates/`
3. Add JavaScript functionality to `whis.js`
4. Update navigation in `base.html`

### WebSocket Events
- `connect/disconnect` - Connection management
- `chat_message` - Send message to Whis
- `whis_thinking` - Show thinking indicator
- `whis_response` - Receive Whis response
- `new_alert` - System alerts
- `approval_update` - Approval status changes

## Troubleshooting

### Common Issues

**Whis API Connection Failed**
- Check `WHIS_API_URL` environment variable
- Ensure Whis API is running and accessible
- Verify network connectivity

**LimaCharlie/Splunk Integration Not Working**
- Verify API credentials are set correctly
- Check network access to SIEM platforms
- Review authentication settings

**WebSocket Connection Issues**
- Check browser console for errors
- Verify Flask-SocketIO is installed
- Ensure no firewall blocking WebSocket connections

### Debug Mode
```bash
export FLASK_DEBUG=1
./run.sh
```

### Logging
- Application logs printed to console
- Set `logging.basicConfig(level=logging.DEBUG)` for verbose logging
- Check browser developer tools for frontend errors

## Integration with Whis API

### Expected API Format
The frontend expects the Whis API to accept:
```json
{
    "event_data": {
        "search_name": "Web Interface Query - user123",
        "host": "whis-frontend", 
        "severity": "medium",
        "description": "User message content",
        "user": "user123",
        "conversation_id": "uuid-here"
    }
}
```

### Response Format
Expected response from Whis:
```json
{
    "explanation": "Analysis results...",
    "artifacts": [...],
    "how": [...],
    "response_time": 1.23
}
```

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review application logs
3. Create detailed issue reports
4. Include environment configuration details

---

**🔐 Security Notice**: This interface provides direct access to security systems. Ensure proper authentication and authorization before production deployment.