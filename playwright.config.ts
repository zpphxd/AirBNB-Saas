import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 60_000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8005',
  },
  reporter: [['list']]
});

