// [TAG] CHAT-KB - Test chat returns knowledge base answers with citations
import { test, expect } from '@playwright/test';

test.describe('Chat Knowledge Base', () => {

  test('asks "what is kubernetes?" returns content with citations', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is kubernetes?' }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Should be definition intent
    expect(data.intent).toBe('definition');
    expect(data.confidence_score).toBeGreaterThan(0.8);
    
    // Response should contain Kubernetes definition
    expect(data.response).toContain('KUBERNETES');
    expect(data.response).toContain('container orchestration');
    
    // Must have citations from core_glossary
    expect(data.citations).toBeInstanceOf(Array);
    expect(data.citations.length).toBeGreaterThan(0);
    expect(data.citations[0]).toMatch(/core_glossary\/kubernetes|documentation\/k8s_security/);
    
    // Should use FAISS index
    expect(data.debug.index_count).toBe(1973);
  });

  test('asks "what is nist?" returns framework info', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is nist?' }
    });
    
    const data = await response.json();
    
    expect(data.intent).toBe('definition');
    expect(data.response).toContain('NIST');
    expect(data.response).toContain('Cybersecurity Framework');
    expect(data.citations.length).toBeGreaterThan(0);
  });

  test('asks "what is limacharlie?" returns EDR info', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is limacharlie?' }
    });
    
    const data = await response.json();
    
    expect(data.intent).toBe('definition');
    expect(data.response).toContain('LIMACHARLIE');
    expect(data.response).toMatch(/EDR|endpoint detection/i);
    expect(data.citations.length).toBeGreaterThan(0);
  });

  test('knowledge gap query gets queued for training', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is AcmeSecure QuantumShield?' }
    });
    
    const data = await response.json();
    
    // Should detect knowledge gap
    expect(data.response).toContain('Knowledge Gap Detected');
    expect(data.response).toContain('Queued for training');
    expect(data.citations.length).toBe(0);
  });

});