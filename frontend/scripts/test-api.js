// API Testing Utility for SchemaSage
// Run with: node scripts/test-api.js

import fetch from 'node-fetch';

const API_BASE_URL = 'http://localhost:8000';
const ENDPOINTS = [
  '/health',
  '/api/health',
  '/api/schema/validate-api-key',
  // Add more endpoints as needed
];

async function testEndpoint(endpoint) {
  try {
    console.log(`Testing ${endpoint}...`);
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    const data = await response.json();
    
    if (response.ok) {
      console.log(`\x1b[32m✓\x1b[0m ${endpoint}: ${response.status}`);
      console.log(`  Response: ${JSON.stringify(data).substring(0, 100)}${JSON.stringify(data).length > 100 ? '...' : ''}`);
    } else {
      console.log(`\x1b[31m✗\x1b[0m ${endpoint}: ${response.status} - ${data.error?.message || JSON.stringify(data)}`);
    }
    return { success: response.ok, endpoint };
  } catch (error) {
    console.log(`\x1b[31m✗\x1b[0m ${endpoint}: Connection failed - ${error.message}`);
    return { success: false, endpoint, error: error.message };
  }
}

async function main() {
  console.log('\x1b[34m=== Testing SchemaSage API Endpoints ===\x1b[0m');
  console.log(`Base URL: ${API_BASE_URL}`);
  console.log('');
  
  const results = [];
  
  for (const endpoint of ENDPOINTS) {
    const result = await testEndpoint(endpoint);
    results.push(result);
  }
  
  console.log('');
  console.log('\x1b[34m=== Summary ===\x1b[0m');
  const successful = results.filter(r => r.success).length;
  console.log(`${successful}/${results.length} endpoints available`);
  
  if (successful === 0) {
    console.log('\x1b[31mIs your backend server running?\x1b[0m');
  } else if (successful < results.length) {
    console.log('\x1b[33mSome endpoints are not available. Check your backend implementation.\x1b[0m');
  } else {
    console.log('\x1b[32mAll endpoints are working correctly!\x1b[0m');
  }
}

main().catch(console.error);