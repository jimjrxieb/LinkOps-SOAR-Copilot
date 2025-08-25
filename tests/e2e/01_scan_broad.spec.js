// WHIS Broad Scan Intent E2E Test  
// Tests clarification behavior and two-option rule

import { test, expect } from '@playwright/test';

test.describe('WHIS Broad Scan Intent', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await page.waitForSelector('[data-testid="chat-message-input"]');
    await page.waitForSelector('[data-testid="chat-send-button"]:not([disabled])');
  });

  test('responds to "show me everything" with two specific options', async ({ page }) => {
    await page.locator('[data-testid="chat-message-input"]').fill('show me everything');
    await page.locator('[data-testid="chat-send-button"]').click();

    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    const response = await page.locator('[data-testid="whis-message"]').last().textContent();

    // Should offer exactly 2 options
    const optionCount = (response.match(/\bor\b/gi) || []).length;
    expect(optionCount).toBe(1); // "option1 or option2" = 1 "or"

    // Should contain clarifying question structure
    expect(response).toMatch(/can.*analyze.*or.*which.*investigate/i);

    // Must not contain generic capability lists
    expect(response).not.toContain('I can help with');
    expect(response).not.toMatch(/[•-]\s/); // No bullet points
  });

  test('adapts options based on system context', async ({ page }) => {
    const broadQueries = [
      'what should I look at',
      'give me a summary', 
      'analyze the situation',
      'what\'s happening'
    ];

    for (const query of broadQueries) {
      await page.locator('[data-testid="chat-message-input"]').fill(query);
      await page.locator('[data-testid="chat-send-button"]').click();
      
      await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });
      
      const response = await page.locator('[data-testid="whis-message"]').last().textContent();
      
      // Should provide specific actionable options
      expect(response).toMatch(/\b(incident|alert|threat|hunt|analyze)\b/i);
      
      // Should end with clarifying question
      expect(response).toMatch(/which.*\?$/i);
      
      // Clear for next test
      await page.reload();
      await page.waitForSelector('[data-testid="chat-message-input"]');
    }
  });

  test('prioritizes active incidents in options', async ({ page }) => {
    // This would require mocking active incidents, but demonstrates the test structure
    await page.locator('[data-testid="chat-message-input"]').fill('overview');
    await page.locator('[data-testid="chat-send-button"]').click();

    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    const response = await page.locator('[data-testid="whis-message"]').last().textContent();

    // When incidents are active, should be option 1
    if (response.includes('incident')) {
      const incidentPosition = response.toLowerCase().indexOf('incident');
      const orPosition = response.toLowerCase().indexOf(' or ');
      
      // Incident should come before "or" (first option)
      expect(incidentPosition).toBeLessThan(orPosition);
    }
  });

  test('maintains security focus in clarification options', async ({ page }) => {
    await page.locator('[data-testid="chat-message-input"]').fill('status');
    await page.locator('[data-testid="chat-send-button"]').click();

    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    const response = await page.locator('[data-testid="whis-message"]').last().textContent();

    // Options should be security-relevant
    const securityTerms = ['incident', 'alert', 'threat', 'hunt', 'security', 'analyze', 'investigate'];
    const hasSecurityFocus = securityTerms.some(term => 
      response.toLowerCase().includes(term)
    );
    
    expect(hasSecurityFocus).toBe(true);
  });

  test('API response includes appropriate confidence for broad scan', async ({ page }) => {
    const apiResponsePromise = page.waitForResponse(response => 
      response.url().includes('/chat') && response.request().method() === 'POST'
    );

    await page.locator('[data-testid="chat-message-input"]').fill('show me everything');
    await page.locator('[data-testid="chat-send-button"]').click();

    const apiResponse = await apiResponsePromise;
    const responseData = await apiResponse.json();

    // Broad scan should have medium confidence (needs clarification)
    expect(responseData.confidence_score).toBeGreaterThan(0.5);
    expect(responseData.confidence_score).toBeLessThan(0.9);

    // Should not be training queued (we can handle broad scans)
    expect(responseData.training_queued).toBe(false);
  });

  test('follows up appropriately when user provides clarification', async ({ page }) => {
    // First query: broad scan
    await page.locator('[data-testid="chat-message-input"]').fill('what should I look at');
    await page.locator('[data-testid="chat-send-button"]').click();
    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    const firstResponse = await page.locator('[data-testid="whis-message"]').last().textContent();
    
    // Extract one of the offered options (simplified for demo)
    let followUpQuery = 'incidents';
    if (firstResponse.includes('threat')) {
      followUpQuery = 'threat hunting';
    }

    // Second query: specific follow-up
    await page.locator('[data-testid="chat-message-input"]').fill(followUpQuery);
    await page.locator('[data-testid="chat-send-button"]').click();
    await page.waitForSelector('[data-testid="chat-thinking-indicator"]', { state: 'hidden' });

    const followUpResponse = await page.locator('[data-testid="whis-message"]').last().textContent();

    // Follow-up should be more specific and actionable
    expect(followUpResponse).not.toMatch(/which.*\?$/); // Not another clarification
    expect(followUpResponse.length).toBeGreaterThan(firstResponse.length); // More detailed
  });
});