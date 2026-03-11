#!/usr/bin/env node
import { execSync } from 'child_process';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const AUDIT_THRESHOLDS = {
  critical: 0,
  high: 0,
  moderate: 0,
  low: 0
};

function runAudit() {
  console.log('🔍 Running npm audit...\n');
  try {
    const output = execSync('npm audit --json', { encoding: 'utf8' });
    const result = JSON.parse(output);
    return result;
  } catch (error) {
    if (error.stdout) {
      return JSON.parse(error.stdout);
    }
    throw error;
  }
}

function checkVulnerabilities() {
  const result = runAudit();
  const vulnerabilities = result.vulnerabilities || {};
  const metadata = result.metadata?.vulnerabilities || {};

  const counts = {
    critical: metadata.critical || 0,
    high: metadata.high || 0,
    moderate: metadata.moderate || 0,
    low: metadata.low || 0,
    total: metadata.total || 0
  };

  console.log('📊 Vulnerability Summary:');
  console.log(`   Critical: ${counts.critical}`);
  console.log(`   High:     ${counts.high}`);
  console.log(`   Moderate: ${counts.moderate}`);
  console.log(`   Low:      ${counts.low}`);
  console.log(`   Total:    ${counts.total}\n`);

  if (counts.total > 0) {
    console.log('⚠️  Vulnerabilities found!\n');
    console.log('📝 Vulnerability Details:');

    for (const [pkg, details] of Object.entries(vulnerabilities)) {
      console.log(`\n   Package: ${pkg}`);
      console.log(`   Severity: ${details.severity}`);
      console.log(`   Title: ${details.title || 'N/A'}`);
      if (details.url) {
        console.log(`   URL: ${details.url}`);
      }
      if (details.fixAvailable) {
        console.log(`   Fix available: YES`);
      }
    }

    console.log('\n💡 Run "npm audit fix" to fix vulnerabilities\n');
    process.exit(1);
  } else {
    console.log('✅ No vulnerabilities found!\n');
    process.exit(0);
  }
}

checkVulnerabilities();
