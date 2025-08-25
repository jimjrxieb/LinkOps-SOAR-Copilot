// [TAG] DEMO-INCIDENT-SHADOW - Test demo incident creates shadow mode
import { test, expect } from '@playwright/test';

test.describe('Demo Incident Shadow Mode', () => {

  test('demo incident runs in shadow mode with decision graph', async ({ request }) => {
    const response = await request.post('http://localhost:8001/api/harness/demo/incident', {
      data: {}
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Verify harness creates demo scenario
    expect(data.harness_id).toMatch(/^DEMO-\d+$/);
    expect(data.scenario).toBe('Brute Force Attack Simulation');
    
    // Incident should be created
    expect(data.incident).toBeDefined();
    expect(data.incident.id).toBe('INC-DEMO-001');
    expect(data.incident.severity).toBe('high');
    
    // Should assign runbook RB-101
    expect(data.incident.runbook).toBe('RB-101');
    
    // Decision graph should show progress 
    expect(data.incident.decision_graph_progress).toBeInstanceOf(Array);
    expect(data.incident.decision_graph_progress).toContain('intake');
    expect(data.incident.decision_graph_progress).toContain('classify');
    
    // Should map to MITRE techniques
    expect(data.incident.mitre_techniques).toBeInstanceOf(Array);
    expect(data.incident.mitre_techniques.length).toBeGreaterThan(0);
    
    // Actions should be planned but not executed (shadow mode)
    expect(data.incident.actions_planned).toBeInstanceOf(Array);
    expect(data.incident.actions_planned.length).toBeGreaterThan(0);
    
    // Should include containment actions
    const actions = data.incident.actions_planned.join(' ').toLowerCase();
    expect(actions).toMatch(/block|disable|collect/);
  });

  test('demo incident timeline and duration', async ({ request }) => {
    const response = await request.post('http://localhost:8001/api/harness/demo/incident', {
      data: {}
    });
    
    const data = await response.json();
    
    // Should have realistic timeline
    expect(data.feed_rate).toBe('real-time');
    expect(data.duration_seconds).toBe(300); // 5 minutes
    
    // Source should be realistic internal IP → DC
    expect(data.incident.source).toMatch(/10\.\d+\.\d+\.\d+ → DC\d+\.corp\.local/);
  });

  test('multiple demo incidents get unique IDs', async ({ request }) => {
    const response1 = await request.post('http://localhost:8001/api/harness/demo/incident', {
      data: {}
    });
    const data1 = await response1.json();
    
    const response2 = await request.post('http://localhost:8001/api/harness/demo/incident', {
      data: {}
    });
    const data2 = await response2.json();
    
    // Different harness IDs
    expect(data1.harness_id).not.toBe(data2.harness_id);
    
    // But same demo incident ID (template)
    expect(data1.incident.id).toBe(data2.incident.id);
    expect(data1.incident.id).toBe('INC-DEMO-001');
  });

});