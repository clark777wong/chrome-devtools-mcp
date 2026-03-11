#!/usr/bin/env node
import { execSync, spawn } from 'child_process';
import { existsSync, readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, relative } from 'path';

const PROJECT_ROOT = process.cwd();
const UPSTREAM_REMOTE = 'upstream';
const ORIGIN_REMOTE = 'origin';

function run(command, options = {}) {
  try {
    return execSync(command, { encoding: 'utf8', stdio: 'pipe', ...options });
  } catch (error) {
    if (options.silent) return null;
    console.error(`❌ Command failed: ${command}`);
    if (error.message) console.error(error.message);
    throw error;
  }
}

function hasUpstreamRemote() {
  const remotes = run('git remote -v');
  return remotes.includes(UPSTREAM_REMOTE);
}

function setupUpstreamRemote() {
  console.log('🔗 Setting up upstream remote...');
  run(`git remote add ${UPSTREAM_REMOTE} https://github.com/ChromeDevTools/chrome-devtools-mcp.git`);
  console.log('✅ Upstream remote added\n');
}

function checkForSensitiveFiles() {
  const sensitivePatterns = [
    'password', 'secret', 'token', 'apiKey', 'apikey',
    'private', 'credential', '.env'
  ];

  const sensitiveExtensions = ['.key', '.pem', '.cert'];

  const sensitiveFiles = [];
  const dirsToCheck = ['src', 'scripts', 'config', 'lib'];

  function checkDir(dir) {
    if (!existsSync(dir)) return;
    const items = readdirSync(dir);
    for (const item of items) {
      const fullPath = join(dir, item);
      const stat = statSync(fullPath);
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        checkDir(fullPath);
      } else if (stat.isFile()) {
        const lowerName = item.toLowerCase();
        if (sensitivePatterns.some(p => lowerName.includes(p))) {
          sensitiveFiles.push(fullPath);
        }
        if (sensitiveExtensions.some(ext => item.endsWith(ext))) {
          sensitiveFiles.push(fullPath);
        }
      }
    }
  }

  for (const dir of dirsToCheck) {
    checkDir(dir);
  }

  return sensitiveFiles;
}

function syncFromUpstream() {
  console.log('📦 Syncing from upstream...\n');

  console.log('1️⃣  Fetching upstream changes...');
  run(`git fetch ${UPSTREAM_REMOTE}`);

  console.log('2️⃣  Stashing local changes...');
  const hasChanges = run('git status --porcelain').trim().length > 0;
  if (hasChanges) {
    run('git stash push -m "Local changes before sync"');
  }

  console.log('3️⃣  Checking for sensitive files in your project...');
  const sensitiveFiles = checkForSensitiveFiles();
  if (sensitiveFiles.length > 0) {
    console.log('\n⚠️  WARNING: Potential sensitive files detected:');
    for (const file of sensitiveFiles) {
      console.log(`   - ${file}`);
    }
    console.log('\n💡 Make sure these files are in .gitignore or not committed!\n');
  }

  console.log('4️⃣  Merging upstream main branch...');
  try {
    run(`git merge ${UPSTREAM_REMOTE}/main --no-edit`);
    console.log('✅ Merge successful!\n');
  } catch (error) {
    console.log('⚠️  Merge conflict detected!');
    console.log('💡 Please resolve conflicts manually, then run:');
    console.log('   git add .');
    console.log('   git commit');
    console.log('');
    if (hasChanges) {
      console.log('   To restore your stashed changes:');
      console.log('   git stash pop');
    }
    return false;
  }

  if (hasChanges) {
    console.log('5️⃣  Restoring local changes...');
    run('git stash pop');
  }

  return true;
}

function runNpmAudit() {
  console.log('🔍 Running npm audit...\n');
  try {
    run('npm audit');
  } catch (error) {
    console.log('\n💡 To fix vulnerabilities, run: npm audit fix');
  }
}

function installDependencies() {
  console.log('📥 Installing dependencies...\n');
  run('npm install');
  console.log('✅ Dependencies installed!\n');
}

function runTests() {
  console.log('🧪 Running tests...\n');
  try {
    run('npm test');
    console.log('✅ All tests passed!\n');
  } catch (error) {
    console.log('❌ Some tests failed. Please check the output above.\n');
  }
}

function main() {
  console.log('='.repeat(60));
  console.log('🔄 Chrome DevTools MCP - Sync & Security Check Script');
  console.log('='.repeat(60));
  console.log('');

  if (!hasUpstreamRemote()) {
    setupUpstreamRemote();
  }

  const syncSuccess = syncFromUpstream();

  if (!syncSuccess) {
    console.log('\n❌ Sync incomplete. Please resolve conflicts first.');
    process.exit(1);
  }

  console.log('6️⃣  Updating npm dependencies...');
  installDependencies();

  runNpmAudit();

  console.log('='.repeat(60));
  console.log('🎉 Sync complete!');
  console.log('='.repeat(60));
  console.log('');
  console.log('Summary:');
  console.log('  ✅ Upstream changes merged');
  console.log('  ✅ Dependencies updated');
  console.log('  ✅ Security audit completed');
  console.log('');
  console.log('Next steps:');
  console.log('  - Review any changes');
  console.log('  - Run tests: npm test');
  console.log('  - Build: npm run build');
  console.log('');
}

main();
