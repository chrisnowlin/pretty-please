import { copyFileSync, readdirSync } from 'fs';
import { join } from 'path';

const result = await Bun.build({
  entrypoints: ['./src/index.tsx'],
  outdir: './dist',
  target: 'browser',
  format: 'esm',
  splitting: true,
  minify: true,
  sourcemap: 'linked',
  naming: {
    entry: '[dir]/[name].[hash].[ext]',
    chunk: '[name].[hash].[ext]',
    asset: 'assets/[name].[hash].[ext]'
  },
  define: {
    'process.env.NODE_ENV': '"production"'
  }
});

if (!result.success) {
  console.error('Build failed');
  for (const message of result.logs) {
    console.error(message);
  }
  process.exit(1);
}

console.log('Build completed successfully');
for (const output of result.outputs) {
  console.log(`  ${output.path}`);
}

const entryFile = result.outputs.find(o => o.kind === 'entry-point');
const entryFileName = entryFile ? entryFile.path.split('/').pop() : 'index.js';

const htmlContent = await Bun.file('./public/index.html').text();
const updatedHtml = htmlContent
  .replace('/src/index.tsx', `/${entryFileName}`)
  .replace('src="/src/index.tsx"', `src="/${entryFileName}"`);
await Bun.write('./dist/index.html', updatedHtml);

console.log('  ./dist/index.html');
