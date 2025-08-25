// Debug frontend issues by simulating browser behavior
const http = require('http');
const { URL } = require('url');

async function debugFrontend() {
    console.log('🔍 WHIS FRONTEND DEBUG ANALYSIS');
    console.log('================================\n');
    
    // 1. Check if we can login and get session
    console.log('1. Testing Login Flow...');
    
    try {
        const loginResponse = await makeRequest('http://localhost:5000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'username=debuguser&password=debugpass'
        });
        
        console.log(`   Login POST response: ${loginResponse.status}`);
        
        if (loginResponse.status === 302) {
            console.log('   ✅ Login redirecting (expected)');
            
            // Extract session cookie if present
            const cookies = loginResponse.headers['set-cookie'];
            if (cookies) {
                console.log('   ✅ Session cookies set');
                
                // Now try to access dashboard with session
                const sessionCookie = cookies[0].split(';')[0];
                const dashboardResponse = await makeRequest('http://localhost:5000/', {
                    headers: { 'Cookie': sessionCookie }
                });
                
                console.log(`   Dashboard access: ${dashboardResponse.status}`);
                
                if (dashboardResponse.status === 200) {
                    console.log('   ✅ Can access dashboard with session');
                    
                    // Check for JavaScript initialization
                    const hasWhisJS = dashboardResponse.body.includes('WhisInterface.init()');
                    const hasSocketIO = dashboardResponse.body.includes('socket.io.js');
                    
                    console.log(`   WhisInterface init: ${hasWhisJS ? '✅' : '❌'}`);
                    console.log(`   Socket.IO loaded: ${hasSocketIO ? '✅' : '❌'}`);
                    
                } else {
                    console.log('   ❌ Cannot access dashboard');
                }
            } else {
                console.log('   ❌ No session cookies returned');
            }
        }
        
    } catch (error) {
        console.log(`   ❌ Login test failed: ${error.message}`);
    }
    
    // 2. Check API connectivity directly
    console.log('\n2. Testing API Connectivity...');
    
    try {
        const whisHealth = await makeRequest('http://localhost:8001/health');
        if (whisHealth.status === 200) {
            const health = JSON.parse(whisHealth.body);
            console.log('   ✅ Whis API reachable');
            console.log(`   Model loaded: ${health.model_loaded}`);
            console.log(`   Status: ${health.status}`);
        } else {
            console.log('   ❌ Whis API not healthy');
        }
    } catch (error) {
        console.log(`   ❌ Whis API error: ${error.message}`);
    }
    
    // 3. Test a real explain call
    console.log('\n3. Testing Whis Explain Endpoint...');
    
    try {
        const explainResponse = await makeRequest('http://localhost:8001/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_data: {
                    search_name: 'Frontend Debug Test',
                    host: 'debug-host',
                    description: 'Testing if Whis responds to frontend requests'
                }
            })
        });
        
        if (explainResponse.status === 200) {
            const result = JSON.parse(explainResponse.body);
            console.log('   ✅ Whis explain endpoint working');
            console.log(`   Response ID: ${result.response_id}`);
            console.log(`   Processing time: ${result.processing_time_ms}ms`);
        } else {
            console.log(`   ❌ Explain endpoint failed: ${explainResponse.status}`);
        }
        
    } catch (error) {
        console.log(`   ❌ Explain test failed: ${error.message}`);
    }
    
    // 4. Check if frontend can reach its own API endpoints
    console.log('\n4. Testing Frontend API Endpoints...');
    
    // We need a session for this, let's create one
    try {
        const loginResp = await makeRequest('http://localhost:5000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'username=apitest&password=apitest'
        });
        
        if (loginResp.headers['set-cookie']) {
            const sessionCookie = loginResp.headers['set-cookie'][0].split(';')[0];
            
            const apiStatus = await makeRequest('http://localhost:5000/api/status', {
                headers: { 'Cookie': sessionCookie }
            });
            
            console.log(`   Frontend /api/status: ${apiStatus.status}`);
            
            if (apiStatus.status === 200) {
                console.log('   ✅ Frontend API endpoints accessible');
                const status = JSON.parse(apiStatus.body);
                console.log(`   Whis API status: ${status.whis_api}`);
            }
        }
        
    } catch (error) {
        console.log(`   ❌ Frontend API test failed: ${error.message}`);
    }
    
    // 5. Diagnosis and recommendations
    console.log('\n🔧 DIAGNOSIS AND RECOMMENDATIONS');
    console.log('=================================');
    
    console.log('Based on the tests above:');
    console.log('1. If login/session works: Frontend Flask app is functional');
    console.log('2. If Whis API works: Backend AI is responsive');
    console.log('3. If frontend APIs work: Integration is properly configured');
    console.log('4. If any fail: Check the specific component');
    
    console.log('\n💡 Common Issues:');
    console.log('- Buttons not working: Usually JavaScript errors or missing event listeners');
    console.log('- Chat not responding: Usually WebSocket connection or API URL mismatch');
    console.log('- "Fake" scores: Dashboard shows placeholder data instead of real metrics');
    
    console.log('\n🔍 Next Steps:');
    console.log('1. Check browser console for JavaScript errors');
    console.log('2. Verify WebSocket connections are established');
    console.log('3. Test actual message sending through chat interface');
    console.log('4. Replace placeholder dashboard data with real API calls');
}

function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const req = http.request({
            hostname: parsedUrl.hostname,
            port: parsedUrl.port,
            path: parsedUrl.pathname + parsedUrl.search,
            method: options.method || 'GET',
            headers: options.headers || {}
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({
                status: res.statusCode,
                headers: res.headers,
                body: data
            }));
        });
        
        req.on('error', reject);
        if (options.body) req.write(options.body);
        req.end();
    });
}

debugFrontend();