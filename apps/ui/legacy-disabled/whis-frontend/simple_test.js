// Simple UI diagnostic test without browser dependencies
const http = require('http');
const { URL } = require('url');

class WhisUITester {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
    }

    async makeRequest(path, options = {}) {
        const url = new URL(path, this.baseUrl);
        
        return new Promise((resolve, reject) => {
            const req = http.request(url, {
                method: options.method || 'GET',
                headers: {
                    'User-Agent': 'WhisUITester/1.0',
                    'Accept': 'text/html,application/json',
                    ...options.headers
                }
            }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    body: data,
                    redirected: res.statusCode >= 300 && res.statusCode < 400
                }));
            });
            
            req.on('error', reject);
            if (options.body) req.write(options.body);
            req.end();
        });
    }

    async testBasicConnectivity() {
        console.log('🔍 Testing Basic Connectivity...');
        
        try {
            const response = await this.makeRequest('/');
            console.log(`✅ GET / -> ${response.status}`);
            
            if (response.redirected) {
                console.log('📍 Redirected (expected for login)');
            }
            
            return response.status < 500;
        } catch (error) {
            console.log(`❌ Connection failed: ${error.message}`);
            return false;
        }
    }

    async testLoginPage() {
        console.log('\n🔍 Testing Login Page...');
        
        try {
            const response = await this.makeRequest('/login');
            console.log(`✅ GET /login -> ${response.status}`);
            
            // Check for required form elements
            const hasUsername = response.body.includes('name="username"');
            const hasPassword = response.body.includes('name="password"');
            const hasSubmit = response.body.includes('type="submit"');
            
            console.log(`📝 Form Elements: username=${hasUsername}, password=${hasPassword}, submit=${hasSubmit}`);
            
            return response.status === 200 && hasUsername && hasPassword && hasSubmit;
        } catch (error) {
            console.log(`❌ Login page test failed: ${error.message}`);
            return false;
        }
    }

    async testStaticAssets() {
        console.log('\n🔍 Testing Static Assets...');
        
        const assets = [
            '/static/css/style.css',
            '/static/js/whis.js'
        ];
        
        for (const asset of assets) {
            try {
                const response = await this.makeRequest(asset);
                console.log(`${response.status === 200 ? '✅' : '❌'} ${asset} -> ${response.status}`);
            } catch (error) {
                console.log(`❌ ${asset} -> Error: ${error.message}`);
            }
        }
    }

    async testAPIEndpoints() {
        console.log('\n🔍 Testing API Endpoints...');
        
        // These should require auth, so expect 401 or redirect
        const endpoints = [
            '/api/status',
            '/health'  // Try this too
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await this.makeRequest(endpoint);
                console.log(`${response.status < 500 ? '✅' : '❌'} ${endpoint} -> ${response.status}`);
            } catch (error) {
                console.log(`❌ ${endpoint} -> Error: ${error.message}`);
            }
        }
    }

    async testWhisAPIConnectivity() {
        console.log('\n🔍 Testing Whis API Connectivity...');
        
        try {
            const whisUrl = 'http://localhost:8001';
            const healthReq = http.request(new URL('/health', whisUrl), (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    console.log(`✅ Whis API /health -> ${res.statusCode}`);
                    try {
                        const health = JSON.parse(data);
                        console.log(`📊 Model loaded: ${health.model_loaded}`);
                        console.log(`📊 Status: ${health.status}`);
                    } catch (e) {
                        console.log('📊 Health response:', data.substring(0, 100));
                    }
                });
            });
            
            healthReq.on('error', (error) => {
                console.log(`❌ Whis API unreachable: ${error.message}`);
            });
            
            healthReq.end();
        } catch (error) {
            console.log(`❌ Whis API test failed: ${error.message}`);
        }
    }

    async runAllTests() {
        console.log('🚀 Starting Whis UI Diagnostic Tests\n');
        
        const tests = [
            { name: 'Basic Connectivity', fn: this.testBasicConnectivity.bind(this) },
            { name: 'Login Page', fn: this.testLoginPage.bind(this) },
            { name: 'Static Assets', fn: this.testStaticAssets.bind(this) },
            { name: 'API Endpoints', fn: this.testAPIEndpoints.bind(this) },
            { name: 'Whis API', fn: this.testWhisAPIConnectivity.bind(this) }
        ];
        
        const results = [];
        
        for (const test of tests) {
            try {
                const result = await test.fn();
                results.push({ name: test.name, passed: result });
            } catch (error) {
                console.log(`❌ ${test.name} failed with error: ${error.message}`);
                results.push({ name: test.name, passed: false, error: error.message });
            }
        }
        
        console.log('\n📊 TEST SUMMARY');
        console.log('================');
        
        results.forEach(result => {
            const status = result.passed ? '✅ PASS' : '❌ FAIL';
            console.log(`${status} ${result.name}`);
            if (result.error) {
                console.log(`    Error: ${result.error}`);
            }
        });
        
        const passedTests = results.filter(r => r.passed).length;
        const totalTests = results.length;
        
        console.log(`\n🎯 OVERALL: ${passedTests}/${totalTests} tests passed`);
        
        if (passedTests < totalTests) {
            console.log('\n🔧 RECOMMENDATIONS:');
            results.filter(r => !r.passed).forEach(result => {
                console.log(`  - Fix ${result.name}`);
            });
        }
        
        return passedTests === totalTests;
    }
}

// Run the tests
const tester = new WhisUITester();
tester.runAllTests().then(success => {
    process.exit(success ? 0 : 1);
});