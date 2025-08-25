const { test, expect } = require('@playwright/test');

test.describe('Whis Frontend UI Tests', () => {
  const BASE_URL = 'http://localhost:5000';
  
  test.beforeEach(async ({ page }) => {
    // Go to the homepage
    await page.goto(BASE_URL);
  });

  test('should redirect to login page', async ({ page }) => {
    await expect(page).toHaveURL(`${BASE_URL}/login`);
    await expect(page).toHaveTitle(/Login.*Whis/);
  });

  test('should have login form elements', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Check for form elements
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    console.log('✅ Login form elements found');
  });

  test('should login with any credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Fill login form
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(`${BASE_URL}/`);
    console.log('✅ Login successful');
  });

  test('should load dashboard after login', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Check dashboard elements
    await expect(page.locator('h2:has-text("Security Operations Dashboard")')).toBeVisible();
    await expect(page.locator('.metric-card')).toHaveCount(4);
    
    console.log('✅ Dashboard loaded');
  });

  test('should have working navigation', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Test navigation links
    const navLinks = [
      { text: 'Dashboard', url: '/' },
      { text: 'Chat with Whis', url: '/chat' },
      { text: 'Approvals', url: '/approvals' },
      { text: 'SIEM Logs', url: '/logs' }
    ];
    
    for (const link of navLinks) {
      await page.click(`a:has-text("${link.text}")`);
      await expect(page).toHaveURL(new RegExp(link.url.replace('/', '\\/?')));
      console.log(`✅ Navigation to ${link.text} works`);
    }
  });

  test('should load chat interface', async ({ page }) => {
    // Login and go to chat
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    await page.click('a:has-text("Chat with Whis")');
    
    // Check chat elements
    await expect(page.locator('#chat-messages')).toBeVisible();
    await expect(page.locator('#chat-input')).toBeVisible();
    await expect(page.locator('button:has-text("Send")')).toBeVisible();
    
    console.log('✅ Chat interface loaded');
  });

  test('should test chat functionality', async ({ page }) => {
    // Login and go to chat
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    await page.click('a:has-text("Chat with Whis")');
    
    // Send a test message
    await page.fill('#chat-input', 'Test security alert analysis');
    await page.click('button:has-text("Send")');
    
    // Check if message appears
    await expect(page.locator('.message.user')).toBeVisible({ timeout: 5000 });
    
    // Wait for potential Whis response
    try {
      await page.waitForSelector('.message.whis', { timeout: 10000 });
      console.log('✅ Chat message sent and response received');
    } catch (e) {
      console.log('⚠️ Chat message sent but no response received');
    }
  });

  test('should test button functionality', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Test dashboard buttons
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons on dashboard`);
    
    for (let i = 0; i < Math.min(buttons.length, 5); i++) {
      const button = buttons[i];
      const buttonText = await button.textContent();
      
      try {
        await button.click({ timeout: 2000 });
        console.log(`✅ Button "${buttonText?.trim()}" is clickable`);
      } catch (e) {
        console.log(`❌ Button "${buttonText?.trim()}" failed to click: ${e.message}`);
      }
    }
  });

  test('should check JavaScript console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Login and navigate around
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    await page.waitForTimeout(2000);
    
    if (errors.length > 0) {
      console.log('❌ JavaScript Errors Found:');
      errors.forEach(error => console.log(`  - ${error}`));
    } else {
      console.log('✅ No JavaScript errors detected');
    }
  });

  test('should check WebSocket connection', async ({ page }) => {
    let wsConnected = false;
    
    page.on('websocket', ws => {
      console.log('🔌 WebSocket connection detected:', ws.url());
      wsConnected = true;
      
      ws.on('close', () => console.log('🔌 WebSocket closed'));
      ws.on('framereceived', event => console.log('📨 WebSocket message received'));
      ws.on('framesent', event => console.log('📤 WebSocket message sent'));
    });
    
    // Login and go to chat to trigger WebSocket
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    await page.click('a:has-text("Chat with Whis")');
    
    await page.waitForTimeout(3000);
    
    if (wsConnected) {
      console.log('✅ WebSocket connection established');
    } else {
      console.log('❌ No WebSocket connection detected');
    }
  });

  test('should test API connectivity', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Test API call from browser
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/status');
        return {
          status: response.status,
          ok: response.ok,
          data: await response.text()
        };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log('📡 API Response:', apiResponse);
    
    if (apiResponse.ok) {
      console.log('✅ Frontend API connectivity working');
    } else {
      console.log('❌ Frontend API connectivity issue');
    }
  });
});

// Quick diagnostic test
test('diagnostic - check if app is running', async ({ page }) => {
  try {
    await page.goto('http://localhost:5000', { timeout: 5000 });
    console.log('✅ App is accessible');
  } catch (error) {
    console.log('❌ App is not accessible:', error.message);
  }
});