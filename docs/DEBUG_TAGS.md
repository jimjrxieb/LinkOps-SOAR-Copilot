# 🔧 Whis SOAR Debug Tags & Testing Guide

## Current Issues & Tags

### 🎯 **MAIN ISSUE**: Recent Activity Not Showing (#recent-activity-fix)
- **Location**: `templates/dashboard.html` lines 251-328
- **Problem**: Activity feed appears empty on dashboard
- **Debug Tags**: `#recent-activity-fix`, `#activity-feed`, `#dashboard-init`
- **Status**: Added extensive console logging to track execution

### 🛠️ **Testing Endpoints & Files**

#### **Main Debugging Tools**
1. **Activity Debug Page**: `http://localhost:5000/static/activity-debug.html`
   - **Tags**: `#activity-debug`, `#manual-testing`
   - **Purpose**: Isolated testing of Recent Activity functions
   - **Status**: ✅ Created, ready for testing

2. **General Test Page**: `http://localhost:5000/static/test.html`
   - **Tags**: `#api-connectivity-fix`, `#ui-testing`
   - **Purpose**: API connectivity and basic UI testing
   - **Status**: ✅ Fixed API connectivity issue

3. **SIEM Validation**: `siem-validation.py`
   - **Tags**: `#siem-validation`, `#battle-ready`
   - **Purpose**: Complete system validation
   - **Status**: ✅ 100% operational

#### **API Endpoints for Testing**
```
✅ /api/health - No auth required (JSON response)
✅ /api/status - Auth required (system status)
✅ /api/test-activity - Auth required (activity testing)
```

#### **Debug Console Tags**
Use these in browser console to track issues:
```javascript
// Filter console for Recent Activity issues
console.log messages containing: [RECENT-ACTIVITY]

// Filter console for Dashboard initialization
console.log messages containing: [DASHBOARD-INIT]
```

### 🎪 **Playwright Testing** (#playwright-testing)
- **Issue**: Missing system dependencies
- **Status**: ❌ Blocked (needs `sudo npx playwright install-deps`)
- **Workaround**: Manual testing with HTML pages

### 📊 **Monitoring & Observability** (#monitoring)
- **Manual Monitor**: `monitoring/manual-monitoring.py`
- **Status**: ✅ Running in background
- **Docker Stack**: ❌ Permission issues (needs elevated access)

## 🔍 **Search & Modify Commands**

```bash
# Find Recent Activity related code
grep -r "#recent-activity-fix" whis-frontend/

# Find dashboard initialization code  
grep -r "#dashboard-init" whis-frontend/

# Find all debug tags
grep -r "#debug-logs" whis-frontend/

# Find API connectivity fixes
grep -r "#api-connectivity-fix" whis-frontend/
```

## 🚀 **Quick Test Commands**

```bash
# Test Recent Activity debug page
curl -s http://localhost:5000/static/activity-debug.html | grep "Recent Activity"

# Test API health
curl -s http://localhost:5000/api/health | jq .

# Login and test authenticated endpoints
python3 -c "
import requests
s = requests.Session()
s.post('http://localhost:5000/login', data={'username': 'test', 'password': 'test'})
print(s.get('http://localhost:5000/api/status').json())
"
```

## 📋 **Current Status**
- ✅ **API Connectivity**: Fixed
- ✅ **SIEM Validation**: 100% operational  
- ✅ **Debug Infrastructure**: Tagged and organized
- 🔧 **Recent Activity**: Under investigation with logging
- ❌ **Playwright**: Blocked by dependencies
- ✅ **Manual Testing**: Multiple tools available

## 🎯 **Next Steps**
1. Test Recent Activity with new debug logs
2. Access browser console to check JavaScript execution
3. Use activity-debug.html for isolated testing
4. Fix any identified JavaScript errors