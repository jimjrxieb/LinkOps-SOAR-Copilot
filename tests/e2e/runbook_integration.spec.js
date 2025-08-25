// [TAG] RUNBOOK-INTEGRATION - Test runbook selection and execution
import { test, expect } from '@playwright/test';

test.describe('Runbook Integration', () => {

  test('Splunk alert triggers runbook RB-101', async ({ request }) => {
    const alertResponse = await request.post('http://localhost:8001/connectors/splunk/_simulate');
    const alert = await alertResponse.json();
    
    // Alert should assign RB-101 for auth attacks
    expect(alert.runbook_assigned).toBe('RB-101');
    expect(alert.type).toBe('Failed Authentication Spike');
    expect(alert.l0_dry_run).toBe(true);
    
    // Execute the assigned runbook
    const runbookResponse = await request.post(`http://localhost:8001/runbook/RB-101?incident_id=${alert.id}`);
    const runbook = await runbookResponse.json();
    
    expect(runbook.runbook_id).toBe('RB-101');
    expect(runbook.name).toBe('Authentication Attack Response');
    expect(runbook.status).toBe('dry_run_complete');
    expect(runbook.l0_mode).toBe(true);
    
    // Should have planned actions but no live actions in L0
    expect(runbook.actions_planned).toBeInstanceOf(Array);
    expect(runbook.actions_planned.length).toBeGreaterThan(0);
    expect(runbook.actions_taken).toEqual([]);
    
    // Should include auth-specific steps
    const steps = runbook.actions_planned.join(' ').toLowerCase();
    expect(steps).toMatch(/verify|account|ip|block|reset/);
  });

  test('LimaCharlie alert triggers runbook RB-301', async ({ request }) => {
    const alertResponse = await request.post('http://localhost:8001/connectors/limacharlie/_simulate');
    const alert = await alertResponse.json();
    
    // Alert should assign RB-301 for malware
    expect(alert.runbook_assigned).toBe('RB-301');
    expect(alert.type).toBe('Suspicious PowerShell Execution');
    expect(alert.severity).toBe('high');
    
    // Execute malware containment runbook
    const runbookResponse = await request.post(`http://localhost:8001/runbook/RB-301?incident_id=${alert.id}`);
    const runbook = await runbookResponse.json();
    
    expect(runbook.name).toBe('Malware Containment');
    expect(runbook.l0_mode).toBe(true);
    
    // Should have containment-specific actions
    const actions = runbook.actions_planned.join(' ').toLowerCase();
    expect(actions).toMatch(/isolate|forensic|malware|clean|patch/);
  });

  test('Root cause analysis triggers runbook RB-201', async ({ request }) => {
    const chatResponse = await request.post('http://localhost:8001/chat', {
      data: { message: 'why did the server crash?' }
    });
    const chat = await chatResponse.json();
    
    // Should detect RCA intent
    expect(chat.intent).toBe('root_cause_analysis');
    expect(chat.response).toContain('Think Deeper');
    
    // Should offer runbook handoff
    expect(chat.citations).toContain('methodologies/root_cause_analysis.md');
    
    // Execute RCA runbook
    const runbookResponse = await request.post('http://localhost:8001/runbook/RB-201?incident_id=INC-RCA-001');
    const runbook = await runbookResponse.json();
    
    expect(runbook.runbook_id).toBe('RB-201');
    expect(runbook.name).toBe('Root Cause Stabilization');
    
    // Should have 5 Whys methodology
    const steps = runbook.actions_planned.join(' ').toLowerCase();
    expect(steps).toMatch(/symptoms|whys|factors|immediate|prevention/);
  });

  test('unknown runbook ID returns error', async ({ request }) => {
    const response = await request.post('http://localhost:8001/runbook/RB-999?incident_id=INC-TEST-001');
    const data = await response.json();
    
    expect(data.error).toBe('Runbook not found');
  });

  test('runbook execution estimates duration', async ({ request }) => {
    const response = await request.post('http://localhost:8001/runbook/RB-101?incident_id=INC-TIMING-001');
    const data = await response.json();
    
    // Should estimate based on step count
    expect(data.estimated_duration).toMatch(/\d+ minutes/);
    
    // RB-101 has 5 steps, should be ~25 minutes
    const duration = parseInt(data.estimated_duration.match(/(\d+)/)[1]);
    expect(duration).toBeGreaterThan(20);
    expect(duration).toBeLessThan(30);
  });

  test('decision graph tracks runbook progress', async ({ request }) => {
    const alertResponse = await request.post('http://localhost:8001/connectors/splunk/_simulate');
    const alert = await alertResponse.json();
    
    // Should show decision graph progression
    expect(alert.decision_graph_progress).toBeInstanceOf(Array);
    expect(alert.decision_graph_progress).toContain('intake');
    expect(alert.decision_graph_progress).toContain('classify');
    expect(alert.decision_graph_progress).toContain('runbook_select');
    
    // Should be in correct order
    const progress = alert.decision_graph_progress;
    expect(progress.indexOf('intake')).toBeLessThan(progress.indexOf('classify'));
    expect(progress.indexOf('classify')).toBeLessThan(progress.indexOf('runbook_select'));
  });

});