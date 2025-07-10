import { execSync } from 'child_process';
import { findAllMatchingFiles } from './noframework/typescript/tech-writer';

const homeDir = process.env.HOME || '.';
const dir = homeDir + '/.cache/github/axios/axios';

// Get git files
const gitFiles = execSync('git ls-files', { cwd: dir })
  .toString()
  .trim()
  .split('\n');

// Get TypeScript files
const tsFiles = findAllMatchingFiles(dir, '*', true, false, true);
const tsRelFiles = tsFiles.map(f => f.replace(dir + '/', ''));

console.log(`Git: ${gitFiles.length} files`);
console.log(`TypeScript: ${tsFiles.length} files`);

// Find missing
const gitSet = new Set(gitFiles);
const tsSet = new Set(tsRelFiles);

const missing = [...gitSet].filter(f => !tsSet.has(f));
console.log(`\nMissing files: ${missing.length}`);
missing.forEach(f => console.log(`  - ${f}`));