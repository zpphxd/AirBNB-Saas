import { test, expect, request } from '@playwright/test';
import { spawn } from 'child_process';
import path from 'path';

let server: any;

test.beforeAll(async () => {
  // Start FastAPI server for e2e tests
  const cwd = path.resolve(__dirname, '../..');
  server = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--port', '8005'], { cwd, stdio: 'inherit' });
  await new Promise((r) => setTimeout(r, 1500));
});

test.afterAll(async () => {
  if (server && server.pid) {
    try { process.kill(server.pid); } catch {}
  }
});

test('MVP API flow via Playwright request', async ({ request }) => {
  // Register host
  const hostReg = await request.post('/auth/register', { data: { email: 'phost@example.com', password: 'secret123', role: 'host', name: 'PH' } });
  expect(hostReg.ok()).toBeTruthy();
  const hostToken = (await hostReg.json()).token as string;

  // Register cleaner
  const cleanerReg = await request.post('/auth/register', { data: { email: 'pcleaner@example.com', password: 'secret123', role: 'cleaner', name: 'PC' } });
  expect(cleanerReg.ok()).toBeTruthy();
  const cleanerToken = (await cleanerReg.json()).token as string;

  // Create property
  const propRes = await request.post('/properties/', {
    data: { name: 'E2E Flat', address: '1 API St' },
    headers: { Authorization: `Bearer ${hostToken}` }
  });
  expect(propRes.ok()).toBeTruthy();
  const prop = await propRes.json();

  // Create job
  const start = new Date(Date.now() + 24*3600*1000).toISOString();
  const end = new Date(Date.now() + 27*3600*1000).toISOString();
  const jobRes = await request.post('/jobs/', {
    data: { property_id: prop.id, booking_start: start, booking_end: end, checklist: [{ text: 'Change linens' }] },
    headers: { Authorization: `Bearer ${hostToken}` }
  });
  expect(jobRes.ok()).toBeTruthy();
  const job = await jobRes.json();

  // List open and claim
  const openRes = await request.get('/jobs/open', { headers: { Authorization: `Bearer ${cleanerToken}` } });
  expect(openRes.ok()).toBeTruthy();
  const claimRes = await request.post(`/jobs/${job.id}/claim`, { headers: { Authorization: `Bearer ${cleanerToken}` } });
  expect(claimRes.ok()).toBeTruthy();

  // Tick checklist
  const itemIds = job.checklist_items.map((i: any) => i.id);
  const tickRes = await request.post(`/jobs/${job.id}/checklist/tick`, {
    data: { item_ids: itemIds }, headers: { Authorization: `Bearer ${cleanerToken}` }
  });
  expect(tickRes.ok()).toBeTruthy();

  // Complete
  const compRes = await request.post(`/jobs/${job.id}/complete`, { headers: { Authorization: `Bearer ${cleanerToken}` } });
  expect(compRes.ok()).toBeTruthy();

  // Rate
  const rateRes = await request.post(`/jobs/${job.id}/rating`, { data: { stars: 5, feedback: 'Great!' }, headers: { Authorization: `Bearer ${hostToken}` } });
  expect(rateRes.ok()).toBeTruthy();
});

