/**
 * 🎭 Playwright Configuration for WHIS SOAR E2E Tests
 * ==================================================
 * 
 * Configured for testing all autonomy levels with proper timeouts
 * and error handling for production-ready deployment validation.
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  
  use: {
    baseURL: process.env.WHIS_API_URL || 'http://localhost:8001',
    
    // Tracing for debugging failures
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // SOAR-specific timeouts (some operations take time)
    actionTimeout: 10000,
    navigationTimeout: 15000,
  },

  projects: [
    {
      name: 'soar-api-tests',
      testMatch: '**/soar_autonomy_levels.spec.js',
      use: {
        ...devices['Desktop Chrome'],
        // API testing doesn't need browser
        headless: true,
      },
    },
    
    {
      name: 'soar-ui-chrome',
      testMatch: '**/soar_autonomy_levels.spec.js',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.WHIS_UI_URL || 'http://localhost:5000',
      },
    },
    
    {
      name: 'soar-ui-firefox',
      testMatch: '**/soar_autonomy_levels.spec.js', 
      use: {
        ...devices['Desktop Firefox'],
        baseURL: process.env.WHIS_UI_URL || 'http://localhost:5000',
      },
    },
  ],

  // Web server for local development
  webServer: [
    {
      command: 'python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8001',
      port: 8001,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
    {
      command: 'python -m http.server 5000 -d apps/ui',
      port: 5000, 
      reuseExistingServer: !process.env.CI,
      timeout: 15000,
    }
  ],
});