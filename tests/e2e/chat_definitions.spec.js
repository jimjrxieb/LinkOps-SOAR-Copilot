// [TAG] CHAT-DEFINITIONS - Test definition responses with citations
import { test, expect } from '@playwright/test';

test.describe('Chat Definitions', () => {
  
  test('kubernetes definition with citations', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is kubernetes?' }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Verify intent classification
    expect(data.intent).toBe('definition');
    expect(data.confidence_score).toBeGreaterThan(0.8);
    
    // Verify response content (≤60 words, no legacy boilerplate)
    const wordCount = data.response.split(/\s+/).length;
    expect(wordCount).toBeLessThanOrEqual(60);
    
    // Deny legacy boilerplate
    expect(data.response).not.toContain("I'm not sure I have specific information");
    expect(data.response).not.toContain("Please provide more context");
    expect(data.response).not.toContain("Processing your security query");
    
    // Must have citations
    expect(data.citations).toHaveLength.toBeGreaterThan(0);
    expect(data.sources).toBeGreaterThan(0);
    
    // Should mention Kubernetes/K8s
    expect(data.response.toLowerCase()).toMatch(/kubernetes|k8s/);
  });

  test('nist definition with citations', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is NIST?' }
    });
    
    const data = await response.json();
    
    expect(data.intent).toBe('definition');
    expect(data.confidence_score).toBeGreaterThan(0.8);
    
    // Verify citations required
    expect(data.citations).toHaveLength.toBeGreaterThan(0);
    
    // Should mention NIST/CSF/framework
    expect(data.response.toLowerCase()).toMatch(/nist|csf|framework/);
  });

  test('limacharlie definition with citations', async ({ request }) => {
    const response = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is limacharlie?' }
    });
    
    const data = await response.json();
    
    expect(data.intent).toBe('definition');
    expect(data.confidence_score).toBeGreaterThan(0.8);
    
    // Verify citations and EDR content
    expect(data.citations).toHaveLength.toBeGreaterThan(0);
    expect(data.response.toLowerCase()).toMatch(/limacharlie|edr|endpoint/);
  });

  test('rag pointer version consistency', async ({ request }) => {
    // Ask same question twice
    const response1 = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is kubernetes?' }
    });
    const data1 = await response1.json();
    
    const response2 = await request.post('http://localhost:8001/chat', {
      data: { message: 'what is kubernetes?' }
    });
    const data2 = await response2.json();
    
    // Same pointer version for consistency
    expect(data1.headers['x-whis-pointer-version']).toBe(data2.headers['x-whis-pointer-version']);
    expect(data1.debug.index_count).toBe(1924);
    expect(data2.debug.index_count).toBe(1924);
  });

});