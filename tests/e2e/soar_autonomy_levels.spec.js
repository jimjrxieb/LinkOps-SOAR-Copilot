/**
 * 🎭 WHIS SOAR E2E Tests - Autonomy Level Validation
 * =================================================
 * 
 * Tests all 4 autonomy levels (L0-L3) to ensure:
 * - Proper incident classification
 * - Correct runbook selection 
 * - Appropriate action execution based on level
 * - Safety gate enforcement
 * - Postcondition verification
 * 
 * This is the definitive test suite for SOAR deployment readiness.
 */

const { test, expect } = require('@playwright/test');

// Test Configuration
const BASE_URL = process.env.WHIS_API_URL || 'http://localhost:8001';
const UI_URL = process.env.WHIS_UI_URL || 'http://localhost:5000';

// Test Data - Realistic security incidents
const TEST_INCIDENTS = {
  powershell_malware: {
    search_name: "Suspicious PowerShell Execution",
    description: "Encoded PowerShell command detected on WORKSTATION-001",
    source_ip: "10.0.1.50",
    host: "WORKSTATION-001", 
    mitre_technique: "T1059.001",
    severity: "high",
    expected_runbook: "RB-301",
    expected_actions: ["isolate_host", "collect_artifacts", "block_hash"]
  },
  
  credential_attack: {
    search_name: "Brute Force Authentication",
    description: "Multiple failed login attempts from external IP",
    source_ip: "185.220.101.42",
    host: "DC-01",
    mitre_technique: "T1110",
    severity: "critical", 
    expected_runbook: "RB-201",
    expected_actions: ["block_ip", "reset_password", "enable_mfa"]
  },
  
  lateral_movement: {
    search_name: "Suspicious Network Activity",
    description: "Unusual SMB activity between internal hosts",
    source_ip: "10.0.1.25",
    host: "SERVER-WEB01",
    mitre_technique: "T1021.002",
    severity: "medium",
    expected_runbook: "RB-101", 
    expected_actions: ["gather_context", "monitor_traffic", "alert_soc"]
  }
};

// Test Groups by Autonomy Level
test.describe('🎯 SOAR Autonomy Level Tests', () => {
  
  // L0: Shadow Mode - No Actions, Only Recommendations
  test.describe('L0 - Shadow Mode (Zero Risk)', () => {
    
    test('L0.1 - Processes incidents without execution', async ({ request }) => {
      // Send incident to SOAR engine
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.powershell_malware,
          autonomy_level: "L0"
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const result = await response.json();
      
      // Should classify correctly
      expect(result.action_schema.runbook_id).toBe("RB-301");
      expect(result.action_schema.classification).toBe("malware_execution");
      
      // Should provide recommendations but NO execution
      expect(result.action_schema.recommendations).toHaveLength(3);
      expect(result.action_schema.actions_executed).toHaveLength(0);
      expect(result.action_schema.execution_mode).toBe("shadow");
    });
    
    test('L0.2 - UI shows recommendations only', async ({ page }) => {
      await page.goto(`${UI_URL}`);
      
      // Set to L0 mode
      await page.selectOption('#autonomy-level', 'L0');
      expect(await page.textContent('#current-autonomy')).toBe('L0');
      
      // Simulate incident
      await page.click('button:has-text("Demo Incident")');
      
      // Should show incident analysis but no action execution
      await expect(page.locator('#current-incident')).toBeVisible();
      await expect(page.locator('#runbook-panel')).toBeVisible();
      await expect(page.locator('#action-panel .actions-list')).toContainText('ready to proceed');
      
      // Verify no actual actions were taken
      await expect(page.locator('.action-executed')).toHaveCount(0);
    });
    
    test('L0.3 - All incident types get classified', async ({ request }) => {
      for (const [incidentType, incident] of Object.entries(TEST_INCIDENTS)) {
        const response = await request.post(`${BASE_URL}/explain`, {
          data: {
            event_data: incident,
            autonomy_level: "L0"
          }
        });
        
        expect(response.ok()).toBeTruthy();
        const result = await response.json();
        
        // Every incident should get proper classification
        expect(result.action_schema.runbook_id).toBe(incident.expected_runbook);
        expect(result.action_schema.confidence).toBeGreaterThan(0.8);
        expect(result.action_schema.actions_executed).toHaveLength(0);
      }
    });
  });
  
  // L1: Read-Only - Information Gathering Only
  test.describe('L1 - Read-Only Mode (Information Gathering)', () => {
    
    test('L1.1 - Executes SIEM searches and context gathering', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.lateral_movement,
          autonomy_level: "L1"
        }
      });
      
      expect(response.ok()).toBeTruthy();
      const result = await response.json();
      
      // Should execute read-only actions
      expect(result.action_schema.actions_executed).toContain("gather_context");
      expect(result.action_schema.actions_executed).toContain("siem_search");
      
      // Should NOT execute modification actions
      expect(result.action_schema.actions_executed).not.toContain("isolate_host");
      expect(result.action_schema.actions_executed).not.toContain("block_ip");
      
      // Should have gathered additional context
      expect(result.action_schema.context_data).toBeDefined();
      expect(result.action_schema.context_data.siem_results).toBeDefined();
    });
    
    test('L1.2 - UI shows read-only actions executed', async ({ page }) => {
      await page.goto(`${UI_URL}`);
      
      await page.selectOption('#autonomy-level', 'L1');
      await page.click('button:has-text("Demo Incident")');
      
      // Should show information gathering actions
      await expect(page.locator('#actions-list')).toContainText('Gathering context');
      await expect(page.locator('#actions-list')).toContainText('Searching SIEM');
      
      // Should not show destructive actions
      await expect(page.locator('#actions-list')).not.toContainText('Isolating host');
      await expect(page.locator('#actions-list')).not.toContainText('Blocking IP');
    });
    
    test('L1.3 - Safety gates prevent write operations', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.credential_attack,
          autonomy_level: "L1"  
        }
      });
      
      const result = await response.json();
      
      // Even critical incidents should not execute write actions in L1
      expect(result.action_schema.actions_blocked).toContain("block_ip");
      expect(result.action_schema.actions_blocked).toContain("reset_password");
      expect(result.action_schema.safety_gates.autonomy_level_gate).toBe("blocked_write_operations");
    });
  });
  
  // L2: Conditional - Limited Actions with Safety Gates
  test.describe('L2 - Conditional Mode (Limited Actions)', () => {
    
    test('L2.1 - Executes safe actions, blocks risky ones', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.powershell_malware,
          autonomy_level: "L2"
        }
      });
      
      const result = await response.json();
      
      // Should execute workstation actions (low risk)
      expect(result.action_schema.actions_executed).toContain("isolate_host");
      expect(result.action_schema.actions_executed).toContain("block_hash");
      
      // Should block if critical asset (domain controller, etc.)
      if (result.action_schema.target_asset_class === "critical") {
        expect(result.action_schema.actions_blocked).toContain("isolate_host");
        expect(result.action_schema.safety_gates.asset_class_gate).toBe("blocked_critical_asset");
      }
    });
    
    test('L2.2 - Respects blast radius limits', async ({ request }) => {
      // Simulate incident affecting many hosts
      const multiHostIncident = {
        ...TEST_INCIDENTS.powershell_malware,
        description: "Malware detected on 15 workstations",
        affected_hosts: Array.from({length: 15}, (_, i) => `WORKSTATION-${i+1}`)
      };
      
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: multiHostIncident,
          autonomy_level: "L2"
        }
      });
      
      const result = await response.json();
      
      // Should limit blast radius to max 10 hosts
      expect(result.action_schema.actions_blocked).toContain("isolate_host");
      expect(result.action_schema.safety_gates.blast_radius_gate).toBe("exceeded_max_hosts");
      expect(result.action_schema.approval_required).toBe(true);
    });
    
    test('L2.3 - Enforces cooldown periods', async ({ request }) => {
      const incident = TEST_INCIDENTS.credential_attack;
      
      // First request should succeed
      let response = await request.post(`${BASE_URL}/explain`, {
        data: { event_data: incident, autonomy_level: "L2" }
      });
      let result = await response.json();
      
      // Assuming external IP blocking is allowed in L2
      expect(result.action_schema.actions_executed).toContain("block_ip");
      
      // Second identical request within cooldown should be blocked
      response = await request.post(`${BASE_URL}/explain`, {
        data: { event_data: incident, autonomy_level: "L2" }
      });
      result = await response.json();
      
      expect(result.action_schema.actions_blocked).toContain("block_ip");
      expect(result.action_schema.safety_gates.cooldown_gate).toBe("blocked_recent_action");
    });
  });
  
  // L3: Manual Approval - All Actions Require Human Authorization
  test.describe('L3 - Manual Approval Mode (Human-in-Loop)', () => {
    
    test('L3.1 - All actions require approval', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.credential_attack,
          autonomy_level: "L3"
        }
      });
      
      const result = await response.json();
      
      // Should classify and plan but not execute
      expect(result.action_schema.runbook_id).toBe("RB-201");
      expect(result.action_schema.actions_planned).toHaveLength(3);
      expect(result.action_schema.actions_executed).toHaveLength(0);
      
      // Should require approval for all actions
      expect(result.action_schema.approval_required).toBe(true);
      expect(result.action_schema.approval_requests).toHaveLength(3);
      
      // Each approval should have proper metadata
      result.action_schema.approval_requests.forEach(approval => {
        expect(approval.action_type).toBeDefined();
        expect(approval.risk_level).toBeDefined();
        expect(approval.approvers_required).toBeGreaterThanOrEqual(1);
      });
    });
    
    test('L3.2 - Critical actions require two approvers', async ({ request }) => {
      const criticalIncident = {
        ...TEST_INCIDENTS.credential_attack,
        host: "DC-01",  // Domain controller
        severity: "critical"
      };
      
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: criticalIncident,
          autonomy_level: "L3"
        }
      });
      
      const result = await response.json();
      
      // Critical asset actions should require 2 approvers
      const resetPasswordApproval = result.action_schema.approval_requests
        .find(a => a.action_type === "reset_password");
      
      expect(resetPasswordApproval.approvers_required).toBe(2);
      expect(resetPasswordApproval.required_roles).toContain("security_lead");
      expect(resetPasswordApproval.required_roles).toContain("infrastructure_lead");
    });
    
    test('L3.3 - UI shows approval workflow', async ({ page }) => {
      await page.goto(`${UI_URL}`);
      
      await page.selectOption('#autonomy-level', 'L3');
      await page.click('button:has-text("Demo Incident")');
      
      // Should show approval required state
      await expect(page.locator('#actions-list')).toContainText('Approval required');
      await expect(page.locator('.approval-button')).toBeVisible();
      
      // Should show risk assessment
      await expect(page.locator('#runbook-panel')).toContainText('Risk Level');
      await expect(page.locator('#runbook-panel')).toContainText('Approvers Required');
    });
  });
  
  // Cross-Level Integration Tests
  test.describe('🔗 Integration & Safety Tests', () => {
    
    test('INT.1 - Emergency stop reverts to L0', async ({ page }) => {
      await page.goto(`${UI_URL}`);
      
      // Start at L2
      await page.selectOption('#autonomy-level', 'L2');
      expect(await page.textContent('#current-autonomy')).toBe('L2');
      
      // Trigger emergency stop
      await page.click('#kill-switch');
      await page.click('button:has-text("OK")'); // Confirm dialog
      
      // Should revert to L0
      expect(await page.textContent('#current-autonomy')).toBe('L0');
      await expect(page.locator('#main-status')).toContainText('EMERGENCY MODE');
    });
    
    test('INT.2 - Postcondition verification works', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.credential_attack,
          autonomy_level: "L2",
          verify_actions: true
        }
      });
      
      const result = await response.json();
      
      if (result.action_schema.actions_executed.length > 0) {
        // Should have verification results
        expect(result.action_schema.verification_results).toBeDefined();
        
        result.action_schema.actions_executed.forEach(action => {
          const verification = result.action_schema.verification_results[action];
          expect(verification.verified).toBeDefined();
          expect(verification.timestamp).toBeDefined();
          
          if (!verification.verified) {
            expect(verification.rollback_initiated).toBe(true);
          }
        });
      }
    });
    
    test('INT.3 - Audit trail captures all decisions', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.lateral_movement,
          autonomy_level: "L2"
        }
      });
      
      const result = await response.json();
      
      // Should have complete audit trail
      expect(result.action_schema.audit_trail).toBeDefined();
      expect(result.action_schema.audit_trail.incident_hash).toBeDefined();
      expect(result.action_schema.audit_trail.decision_graph_path).toBeDefined();
      expect(result.action_schema.audit_trail.safety_gates_evaluated).toBeDefined();
      expect(result.action_schema.audit_trail.timestamp).toBeDefined();
      expect(result.action_schema.audit_trail.correlation_id).toBeDefined();
    });
    
    test('INT.4 - System health endpoints work', async ({ request }) => {
      const health = await request.get(`${BASE_URL}/health`);
      expect(health.ok()).toBeTruthy();
      
      const healthData = await health.json();
      expect(healthData.status).toBe("healthy");
      expect(healthData.dependencies.rag.status).toBe("healthy");
      expect(healthData.dependencies.llm.status).toBe("healthy");
      expect(healthData.model_bom.whis_model).toBeDefined();
    });
    
    test('INT.5 - Handles malformed incidents gracefully', async ({ request }) => {
      const malformedIncident = {
        // Missing required fields
        description: null,
        source_ip: "not-an-ip",
        severity: "invalid-level"
      };
      
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: malformedIncident,
          autonomy_level: "L0"
        }
      });
      
      // Should handle gracefully, not crash
      if (response.ok()) {
        const result = await response.json();
        expect(result.action_schema.error_handled).toBe(true);
      } else {
        expect(response.status()).toBe(400); // Bad request
      }
    });
  });
  
  // Performance & Load Tests
  test.describe('⚡ Performance Tests', () => {
    
    test('PERF.1 - Response time under 2 seconds', async ({ request }) => {
      const startTime = Date.now();
      
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: TEST_INCIDENTS.powershell_malware,
          autonomy_level: "L1"
        }
      });
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      expect(response.ok()).toBeTruthy();
      expect(responseTime).toBeLessThan(2000); // Under 2 seconds
      
      const result = await response.json();
      expect(result.processing_time_ms).toBeLessThan(1500);
    });
    
    test('PERF.2 - Concurrent incident handling', async ({ request }) => {
      const concurrentRequests = Object.values(TEST_INCIDENTS).map(incident =>
        request.post(`${BASE_URL}/explain`, {
          data: {
            event_data: incident,
            autonomy_level: "L0"
          }
        })
      );
      
      const responses = await Promise.all(concurrentRequests);
      
      // All should succeed
      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });
      
      // Verify correlation IDs are unique
      const results = await Promise.all(responses.map(r => r.json()));
      const correlationIds = results.map(r => r.correlation_id);
      const uniqueIds = new Set(correlationIds);
      
      expect(uniqueIds.size).toBe(correlationIds.length);
    });
  });
});

// Deployment Readiness Checks
test.describe('🚀 Deployment Readiness', () => {
  
  test('DEPLOY.1 - All runbooks accessible', async ({ request }) => {
    const runbooks = ['RB-101', 'RB-201', 'RB-301', 'RB-401', 'RB-501'];
    
    for (const runbookId of runbooks) {
      const response = await request.get(`${BASE_URL}/runbook/${runbookId}`);
      expect(response.ok()).toBeTruthy();
      
      const runbook = await response.json();
      expect(runbook.id).toBe(runbookId);
      expect(runbook.actions).toBeDefined();
      expect(runbook.preconditions).toBeDefined();
      expect(runbook.postconditions).toBeDefined();
    }
  });
  
  test('DEPLOY.2 - UI loads without errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    
    await page.goto(`${UI_URL}`);
    
    // UI elements should be present
    await expect(page.locator('h1')).toContainText('WHIS');
    await expect(page.locator('#autonomy-level')).toBeVisible();
    await expect(page.locator('#kill-switch')).toBeVisible();
    
    // No JavaScript errors
    expect(errors).toHaveLength(0);
  });
  
  test('DEPLOY.3 - Shadow mode produces zero false positives', async ({ request }) => {
    // Run through all test incidents in L0 mode
    let falsePositives = 0;
    
    for (const [incidentType, incident] of Object.entries(TEST_INCIDENTS)) {
      const response = await request.post(`${BASE_URL}/explain`, {
        data: {
          event_data: incident,
          autonomy_level: "L0"
        }
      });
      
      const result = await response.json();
      
      // Verify correct classification
      if (result.action_schema.runbook_id !== incident.expected_runbook) {
        falsePositives++;
      }
      
      // Verify confidence is reasonable
      expect(result.action_schema.confidence).toBeGreaterThan(0.7);
    }
    
    // Zero false positives required for deployment
    expect(falsePositives).toBe(0);
  });
});