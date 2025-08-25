// WHIS Greeting Intent E2E Test
// Tests brevity requirements and conversation hygiene

import { test, expect } from '@playwright/test';

test.describe('WHIS Greeting Intent', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to WHIS dashboard
    await page.goto('http://localhost:8000');
    
    // Wait for UI to be ready
    await page.waitForSelector('[data-testid="chat-message-input"]');
    await page.waitForSelector('[data-testid="chat-send-button"]:not([disabled])');
  });

  test('responds to basic greeting with brevity', async ({ page }) => {
    const messageInput = page.locator('[data-testid="chat-message-input"]');
    const sendButton = page.locator('[data-testid="chat-send-button"]');
    const messagesContainer = page.locator('[data-testid="chat-messages-container"]');

    // Send greeting
    await messageInput.fill('Hi there!');
    await sendButton.click();

    // Wait for thinking indicator to appear and disappear
    await page.waitForSelector('[data-testid="chat-thinking-indicator"]');
    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    // Check response
    const whisResponse = page.locator('[data-testid="whis-message"]').last();
    await expect(whisResponse).toBeVisible();
    
    const responseText = await whisResponse.textContent();
    
    // Brevity requirement: ≤25 words
    const wordCount = responseText.trim().split(/\s+/).length;
    expect(wordCount).toBeLessThanOrEqual(25);
    
    // Must not contain capability marketing
    expect(responseText).not.toContain('I can help with');
    expect(responseText).not.toContain('Try asking me about');
    expect(responseText).not.toContain('My capabilities include');
    
    // Should be professional and security-focused
    expect(responseText).toMatch(/security|investigate|analyze|help/i);
    
    // High confidence response (should have checkmark emoji)
    const confidenceIndicator = page.locator('[data-testid="whis-confidence-emoji"]').last();
    await expect(confidenceIndicator).toContainText('✅');
  });

  test('handles different greeting variations', async ({ page }) => {
    const greetings = [
      'hello',
      'hey',
      'good morning',
      'hi whis'
    ];

    for (const greeting of greetings) {
      await page.locator('[data-testid="chat-message-input"]').fill(greeting);
      await page.locator('[data-testid="chat-send-button"]').click();
      
      // Wait for response
      await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });
      
      const response = await page.locator('[data-testid="whis-message"]').last().textContent();
      
      // Check brevity for all variations
      const wordCount = response.trim().split(/\s+/).length;
      expect(wordCount).toBeLessThanOrEqual(25);
      
      // Clear for next test
      await page.reload();
      await page.waitForSelector('[data-testid="chat-message-input"]');
    }
  });

  test('maintains conversation context in greeting responses', async ({ page }) => {
    // Test greeting with security context
    await page.locator('[data-testid="chat-message-input"]').fill('Hi, I need help with an incident');
    await page.locator('[data-testid="chat-send-button"]').click();
    
    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });
    
    const response = await page.locator('[data-testid="whis-message"]').last().textContent();
    
    // Should acknowledge the security context
    expect(response).toMatch(/incident|investigate|help/i);
    
    // Still maintain brevity
    const wordCount = response.trim().split(/\s+/).length;
    expect(wordCount).toBeLessThanOrEqual(25);
  });

  test('API contract compliance for greeting intent', async ({ page }) => {
    // Intercept the chat API call
    const apiResponsePromise = page.waitForResponse(response => 
      response.url().includes('/chat') && response.request().method() === 'POST'
    );

    await page.locator('[data-testid="chat-message-input"]').fill('hello');
    await page.locator('[data-testid="chat-send-button"]').click();

    const apiResponse = await apiResponsePromise;
    const responseData = await apiResponse.json();

    // Verify API contract
    expect(responseData).toHaveProperty('response');
    expect(responseData).toHaveProperty('confidence_score');
    expect(responseData).toHaveProperty('sources_used');
    expect(responseData).toHaveProperty('timestamp');
    expect(responseData).toHaveProperty('training_queued');
    
    // Greeting should have high confidence
    expect(responseData.confidence_score).toBeGreaterThan(0.8);
    
    // Should not be queued for training
    expect(responseData.training_queued).toBe(false);
    
    // Intent classification (if available)
    if (responseData.intent_classified) {
      expect(responseData.intent_classified).toBe('greeting');
    }
  });
});