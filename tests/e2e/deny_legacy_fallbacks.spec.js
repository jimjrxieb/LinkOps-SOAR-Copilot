// [TAG] DENY-LEGACY-FALLBACKS - Ensure no legacy boilerplate appears
import { test, expect } from '@playwright/test';

test.describe('Deny Legacy Fallbacks', () => {

  const DENIED_PHRASES = [
    "I'm not sure I have specific information",
    "Please provide more context",
    "Processing your security query",
    "I'd be happy to help",
    "Could you be more specific",
    "I can help you with",
    "topics I can help with"
  ];

  const TEST_QUERIES = [
    'what is kubernetes?',
    'what is nist?', 
    'what is limacharlie?',
    'unknown security term xyz123',
    'hello',
    'help me with incident response'
  ];

  TEST_QUERIES.forEach(query => {
    test(`deny legacy phrases in response to: "${query}"`, async ({ request }) => {
      const response = await request.post('http://localhost:8001/chat', {
        data: { message: query }
      });
      
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      
      // Check response doesn't contain any denied phrases
      const responseText = data.response.toLowerCase();
      
      for (const deniedPhrase of DENIED_PHRASES) {
        expect(responseText).not.toContain(deniedPhrase.toLowerCase());
      }
      
      // Response should not be blocked message (valid queries)
      if (['kubernetes', 'nist', 'limacharlie', 'hello'].some(term => query.includes(term))) {
        expect(data.response).not.toContain('[Response blocked by deny-list enforcement]');
      }
    });
  });

  test('health endpoint does not contain legacy phrases', async ({ request }) => {
    const response = await request.get('http://localhost:8001/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const healthText = JSON.stringify(data).toLowerCase();
    
    for (const deniedPhrase of DENIED_PHRASES) {
      expect(healthText).not.toContain(deniedPhrase.toLowerCase());
    }
  });

  test('metrics endpoint does not contain legacy phrases', async ({ request }) => {
    const response = await request.get('http://localhost:8001/metrics');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const metricsText = JSON.stringify(data).toLowerCase();
    
    for (const deniedPhrase of DENIED_PHRASES) {
      expect(metricsText).not.toContain(deniedPhrase.toLowerCase());
    }
  });

});