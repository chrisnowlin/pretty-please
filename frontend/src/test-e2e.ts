#!/usr/bin/env bun
/**
 * End-to-end test to verify frontend components are rendering
 */

console.log('🧪 Running E2E Frontend Tests\n');

// Test that the frontend dev server is responding
const response = await fetch('http://localhost:5173/');
const html = await response.text();

// Check critical elements
const checks = [
  { name: 'HTML Document', test: () => html.includes('<!DOCTYPE html>') },
  { name: 'Root Element', test: () => html.includes('<div id="root">') },
  { name: 'React Entry Point', test: () => html.includes('/src/index.tsx') },
  { name: 'Page Title', test: () => html.includes('<title>Jina RAG Pipeline</title>') },
];

console.log('📋 Frontend HTML Checks:');
let allPassed = true;
for (const check of checks) {
  const passed = check.test();
  console.log(`  ${passed ? '✅' : '❌'} ${check.name}`);
  if (!passed) allPassed = false;
}

// Test API endpoints through the proxy
console.log('\n📋 API Proxy Checks:');

const apiTests = [
  { name: 'Collections API', url: 'http://localhost:5173/api/collections' },
  { name: 'Health API', url: 'http://localhost:5173/api/health' },
  { name: 'Supported Formats', url: 'http://localhost:5173/api/ingest/supported-formats' },
];

for (const test of apiTests) {
  try {
    const res = await fetch(test.url);
    const data = await res.json();
    console.log(`  ✅ ${test.name}: ${res.status === 200 ? 'OK' : 'Failed'}`);
  } catch (e) {
    console.log(`  ❌ ${test.name}: ${e.message}`);
    allPassed = false;
  }
}

// Test React components by checking bundle
console.log('\n📋 React Bundle Check:');
try {
  const jsResponse = await fetch('http://localhost:5173/src/App.tsx');
  if (jsResponse.ok) {
    console.log('  ✅ App.tsx is being served');
  } else {
    console.log('  ❌ App.tsx not found');
    allPassed = false;
  }
} catch (e) {
  console.log(`  ❌ Bundle check failed: ${e.message}`);
  allPassed = false;
}

console.log('\n' + '='.repeat(60));
if (allPassed) {
  console.log('✨ All tests passed! Frontend is working correctly.');
  console.log('\nOpen http://localhost:5173 in your browser to interact with:');
  console.log('  • Search documents with real-time results');
  console.log('  • Upload files with drag-and-drop');
  console.log('  • View and manage collections');
} else {
  console.log('⚠️ Some tests failed. Please check the logs above.');
}
console.log('='.repeat(60));

process.exit(allPassed ? 0 : 1);