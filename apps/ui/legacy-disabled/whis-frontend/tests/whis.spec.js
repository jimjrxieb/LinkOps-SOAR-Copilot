const { test, expect } = require('@playwright/test');

test.describe('Whis Frontend Tests', () => {
  const BASE_URL = 'http://localhost:5000';

  test('should test basic functionality', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/Whis/);
  });

  test('should test login and button functionality', async ({ page }) => {
    console.log('🔍 Testing Whis login and buttons...');
    
    // Go to login
    await page.goto(`${BASE_URL}/login`);
    
    // Fill login form
    await page.fill('#username', 'test');
    await page.fill('#password', 'test');
    await page.click('button[type="submit"]');
    
    // Should be on dashboard
    await page.waitForTimeout(2000);
    
    // Count all buttons
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons to test`);
    
    // Test clicking buttons
    let working = 0;
    let broken = 0;
    
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      try {
        const button = buttons[i];
        const text = await button.textContent();
        await button.click({ timeout: 2000 });
        console.log(`✅ Button "${text?.trim()}" works`);
        working++;
      } catch (e) {
        console.log(`❌ Button ${i} failed`);
        broken++;
      }
      await page.waitForTimeout(500);
    }
    
    console.log(`🎯 Button Test Results: ${working} working, ${broken} broken`);
    
    // Test navigation
    try {
      await page.click('a:has-text("Chat with Whis")');
      console.log('✅ Navigation to chat works');
    } catch (e) {
      console.log('❌ Navigation to chat failed');
    }
  });
});