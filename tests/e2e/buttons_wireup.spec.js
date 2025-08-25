// [TAG] BUTTONS-WIREUP - Test all button endpoints return expected data
import { test, expect } from '@playwright/test';

test.describe('Button Wireup', () => {

  test('threat hunt button endpoint', async ({ request }) => {
    const response = await request.post('http://localhost:8001/api/plan/threat-hunt', {
      data: {}
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Verify expected response structure
    expect(data).toHaveProperty('hunt_id');
    expect(data.status).toBe('planned');
    expect(data.mode).toBe('dry-run'); // L0 mode
    
    expect(data.plan).toHaveProperty('title');
    expect(data.plan.title).toContain('Credential Abuse Hunt');
    
    expect(data.plan.queries).toBeInstanceOf(Array);
    expect(data.plan.queries.length).toBeGreaterThan(0);
    
    // Should have platforms and queries
    const platforms = data.plan.queries.map(q => q.platform);
    expect(platforms).toContain('Splunk');
    expect(platforms).toContain('LimaCharlie');
  });

  test('create incident button endpoint', async ({ request }) => {
    const response = await request.post('http://localhost:8001/api/incidents', {
      data: { 
        title: 'Test Incident',
        severity: 'high'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(data).toHaveProperty('incident_id');
    expect(data.status).toBe('shadow'); // L0 mode
    expect(data.title).toBe('Test Incident');
    expect(data.severity).toBe('high');
    expect(data.runbook).toBe('RB-101');
    
    // Decision graph should be present
    expect(data.decision_graph).toHaveProperty('current_node');
    expect(data.decision_graph.nodes_completed).toBeInstanceOf(Array);
    
    // Actions should be dry-run in L0
    expect(data.actions).toBeInstanceOf(Array);
    data.actions.forEach(action => {
      expect(action.mode).toBe('dry-run');
    });
  });

  test('demo incident button endpoint', async ({ request }) => {
    const response = await request.post('http://localhost:8001/api/harness/demo/incident', {
      data: {}
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(data).toHaveProperty('harness_id');
    expect(data.scenario).toBe('Brute Force Attack Simulation');
    
    expect(data.incident).toHaveProperty('id');
    expect(data.incident.id).toBe('INC-DEMO-001');
    expect(data.incident.runbook).toBe('RB-101');
    
    // Should have MITRE techniques
    expect(data.incident.mitre_techniques).toBeInstanceOf(Array);
    expect(data.incident.mitre_techniques).toContain('T1110.001');
  });

  test('docs kb button endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8001/api/docs/kb');
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    expect(data).toHaveProperty('shards');
    expect(data.shards).toBeInstanceOf(Array);
    expect(data.shards.length).toBeGreaterThan(0);
    
    // Should have our required knowledge base entries
    const titles = data.shards.map(s => s.title);
    expect(titles).toContain('Kubernetes Security');
    expect(titles).toContain('NIST Cybersecurity Framework');
    expect(titles).toContain('LimaCharlie Basics');
    
    // Each shard should have required fields
    data.shards.forEach(shard => {
      expect(shard).toHaveProperty('title');
      expect(shard).toHaveProperty('path');
      expect(shard).toHaveProperty('topics');
      expect(shard).toHaveProperty('summary');
    });
  });

  test('metrics button endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8001/metrics');
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    
    // Should have all required metric counters
    expect(data).toHaveProperty('incidents_total');
    expect(data).toHaveProperty('runbook_selected_total');
    expect(data).toHaveProperty('actions_live_total');
    expect(data).toHaveProperty('postcondition_failure_total');
    expect(data).toHaveProperty('time_to_first_action_seconds');
    
    expect(typeof data.incidents_total).toBe('number');
    expect(typeof data.time_to_first_action_seconds).toBe('number');
  });

});