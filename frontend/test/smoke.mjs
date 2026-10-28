import { readFileSync, existsSync } from 'node:fs';
if (!existsSync('src/App.tsx')) throw new Error('App.tsx missing');
const app=readFileSync('src/App.tsx','utf8');
for (const term of ['Company Copilot','Authorization','budget_after','sources']) if(!app.includes(term)) throw new Error(`Missing frontend flow: ${term}`);
console.log('Frontend source smoke tests passed (4 assertions). Run npm run build for TypeScript/Vite validation.');
