// [TAG] GAP-TRIAGE - Test knowledge gap detection and queuing
import { test, expect } from '@playwright/test';

test.describe('Knowledge Gap Triage', () => {

  test('nonsense query triggers gap detection', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is AcmeSecure QuantumShield?' }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Should detect knowledge gap
    expect(data.response).toContain('Knowledge Gap Detected');
    expect(data.response).toContain('Queued for training');
    
    // Should have no citations
    expect(data.citations).toBeInstanceOf(Array);
    expect(data.citations.length).toBe(0);
    
    // Intent should be generic since no match
    expect(['generic_unclear', 'unknown']).toContain(data.intent);
  });

  test('fictional security product triggers gap', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'how does CyberShield Pro detect ransomware?' }
    });
    
    const data = await response.json();
    
    // Should queue for training
    expect(data.response).toContain('Knowledge Gap');
    expect(data.citations.length).toBe(0);
  });

  test('unknown vendor question gets queued', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is SecureMax Enterprise?' }
    });
    
    const data = await response.json();
    
    // Should be handled as knowledge gap
    expect(data.response).toContain('Queued for training');
    expect(data.citations.length).toBe(0);
    
    // Response should not contain legacy boilerplate
    expect(data.response).not.toContain('I\'m not sure I have specific information');
    expect(data.response).not.toContain('Please provide more context');
  });

  test('partial match still provides answer', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'kubernetes security best practices' }
    });
    
    const data = await response.json();
    
    // Should still find kubernetes definition
    expect(data.intent).toBe('definition');
    expect(data.response).toContain('KUBERNETES');
    expect(data.citations.length).toBeGreaterThan(0);
    
    // Should not be treated as gap
    expect(data.response).not.toContain('Knowledge Gap');
  });

  test('empty query handled gracefully', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: '' }
    });
    
    const data = await response.json();
    
    // Should have some response, not crash
    expect(data.response).toBeDefined();
    expect(data.response.length).toBeGreaterThan(0);
  });

});