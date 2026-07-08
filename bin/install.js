#!/usr/bin/env node
/**
 * One-command install for agent-harness:
 *
 *   npx github:jajupmochi/agent-harness
 *
 * Clones the lib to ~/.claude/agent-harness and symlinks the
 * `init-agent-config` skill into ~/.claude/skills/ so that
 * `/init-agent-config` is available in any Claude Code project.
 */

const { execSync } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

const REPO = 'https://github.com/jajupmochi/agent-harness.git';
const TARGET = path.join(os.homedir(), '.claude', 'agent-harness');
const SKILLS_DIR = path.join(os.homedir(), '.claude', 'skills');
const SKILL_NAME = 'init-agent-config';

function run(cmd) {
  return execSync(cmd, { stdio: 'inherit' });
}

function main() {
  console.log(`📦 Installing agent-harness to ${TARGET}...\n`);

  // 1. Make sure ~/.claude exists
  fs.mkdirSync(path.join(os.homedir(), '.claude'), { recursive: true });

  // 2. Clone or report already-installed
  if (fs.existsSync(TARGET)) {
    console.log(`✓ Already installed at ${TARGET}`);
    console.log(`  To update: cd ${TARGET} && git pull origin main\n`);
  } else {
    try {
      run(`git clone --depth 1 ${REPO} "${TARGET}"`);
      console.log(`\n✓ Installed to ${TARGET}\n`);
    } catch (e) {
      console.error('\n❌ Clone failed.');
      console.error('  - Verify git is installed: which git');
      console.error('  - Verify network: curl -I https://github.com');
      console.error('  - Or use the manual clone command (see README.md):');
      console.error(`    git clone ${REPO} ${TARGET}`);
      process.exit(1);
    }
  }

  // 3. Symlink the init skill into ~/.claude/skills/ for slash-command discovery
  const skillSrc = path.join(TARGET, 'setup', SKILL_NAME);
  const skillDst = path.join(SKILLS_DIR, SKILL_NAME);

  if (fs.existsSync(skillSrc)) {
    fs.mkdirSync(SKILLS_DIR, { recursive: true });
    if (!fs.existsSync(skillDst)) {
      try {
        fs.symlinkSync(skillSrc, skillDst, 'dir');
        console.log(`✓ Symlinked /${SKILL_NAME} skill into ~/.claude/skills/\n`);
      } catch (e) {
        console.warn(`⚠ Could not symlink (probably Windows without admin or restricted FS).`);
        console.warn(`  Manual fallback:`);
        console.warn(`    ln -s ${skillSrc} ${skillDst}\n`);
      }
    } else {
      console.log(`✓ /${SKILL_NAME} skill symlink already in place\n`);
    }
  }

  // 4. Print next steps
  const sep = '━'.repeat(50);
  console.log(sep);
  console.log('Next steps:');
  console.log(`  1. cd to your project directory`);
  console.log(`  2. Open Claude Code: claude`);
  console.log(`  3. Run the scaffold skill: /${SKILL_NAME}`);
  console.log(sep);
  console.log(`\nDocs:         https://github.com/jajupmochi/agent-harness`);
  console.log(`Walkthroughs: https://github.com/jajupmochi/agent-harness/blob/main/USAGE.md\n`);
}

main();
