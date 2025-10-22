import { join } from 'path';

const server = Bun.serve({
  port: 5173,
  idleTimeout: 255, // Maximum timeout allowed by Bun (4.25 minutes) for large file uploads
  async fetch(req) {
    const url = new URL(req.url);

    // Proxy API requests (but not WebSocket)
    if (url.pathname.startsWith('/api/')) {
      try {
        const backendUrl = `http://localhost:8000${url.pathname}${url.search}`;

        // Clone headers but remove host header to avoid conflicts
        const headers = new Headers(req.headers);
        headers.delete('host');

        const response = await fetch(backendUrl, {
          method: req.method,
          headers: headers,
          body: req.method !== 'GET' && req.method !== 'HEAD' ? req.body : undefined,
        });

        return response;
      } catch (error) {
        console.error('Proxy error:', error);
        return new Response(JSON.stringify({ error: 'Proxy failed', details: error.message }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

    // WebSocket connections should connect directly to backend (handled in websocket.ts)
    if (url.pathname.startsWith('/ws/')) {
      return new Response('WebSocket connections go directly to port 8000', {
        status: 400,
        headers: { 'Content-Type': 'text/plain' }
      });
    }
    
    // Handle /app.js as entry point
    if (url.pathname === '/app.js') {
      const file = Bun.file(join(process.cwd(), 'src/index.tsx'));
      
      if (await file.exists()) {
        const transpiler = new Bun.Transpiler({
          loader: 'tsx',
          tsconfig: {
            compilerOptions: {
              jsx: 'react-jsx',
              jsxImportSource: 'react'
            }
          }
        });
        
        const content = await file.text();
        const result = transpiler.transformSync(content, 'tsx');
        
        // Fix import paths and add JSX runtime import if needed
        let fixed = result
          .replace(/from ['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g, (match, path) => {
            const cleanPath = path.replace('./', '/src/');
            return `from "${cleanPath}.js"`;
          })
          .replace(/import ([^'"]+) from ['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g, (match, name, path) => {
            const cleanPath = path.replace('./', '/src/');
            return `import ${name} from "${cleanPath}.js"`;
          })
          .replace(/from ['"]react['"]/g, 'from "https://esm.sh/react@18"')
          .replace(/from ['"]react-dom\/client['"]/g, 'from "https://esm.sh/react-dom@18/client"')
          .replace(/from ['"]@tanstack\/react-query['"]/g, 'from "https://esm.sh/@tanstack/react-query@5?deps=react@18"')
          .replace(/from ['"]react-markdown['"]/g, 'from "https://esm.sh/react-markdown@10?deps=react@18"');
        
        // Remove type-only imports (those with "type" keyword)
        fixed = fixed.replace(/^import\s+type\s+\{[^}]*\}\s*from\s*['"][^'"]+['"];?\s*\n/gm, '');
        fixed = fixed.replace(/^import\s*\{([^}]*)\}\s*from\s*(['"][^'"]+['"]);?\s*\n/gm, (match, imports, path) => {
          // Keep imports from external packages
          if (path.includes('react') || path.includes('@tanstack') || path.includes('http')) {
            return match;
          }
          
          // Only filter out imports with explicit "type" modifier
          const importList = imports.split(',').map(i => i.trim());
          const runtimeImports = importList.filter(imp => {
            // Remove imports like "type Foo" but keep "Foo" and "useFoo"
            return !imp.trim().startsWith('type ');
          });
          
          if (runtimeImports.length === 0) {
            return ''; // Remove entirely if no runtime imports
          }
          
          if (runtimeImports.length !== importList.length) {
            // Rebuild import statement with only runtime imports
            return `import { ${runtimeImports.join(', ')} } from ${path};\n`;
          }
          
          return match; // Keep as-is if all are runtime
        });
        
        // Add JSX runtime import if JSX functions are used
        if (fixed.includes('jsxDEV') || fixed.includes('jsx(')) {
          fixed = `import { jsxDEV as jsxDEV_7x81h0kn } from "https://esm.sh/react@18/jsx-dev-runtime";\n` + fixed;
        }
        
        return new Response(fixed, {
          headers: {
            'Content-Type': 'application/javascript',
            'Cache-Control': 'no-cache'
          }
        });
      }
    }
    
    // Handle module imports
    if (url.pathname.startsWith('/src/')) {
      // Try with .tsx/.ts extension if .js is requested
      let filePath = url.pathname.slice(1);
      if (filePath.endsWith('.js')) {
        const tsxPath = filePath.replace(/\.js$/, '.tsx');
        const tsPath = filePath.replace(/\.js$/, '.ts');
        
        if (await Bun.file(join(process.cwd(), tsxPath)).exists()) {
          filePath = tsxPath;
        } else if (await Bun.file(join(process.cwd(), tsPath)).exists()) {
          filePath = tsPath;
        }
      }
      
      const file = Bun.file(join(process.cwd(), filePath));
      
      if (await file.exists()) {
        const transpiler = new Bun.Transpiler({
          loader: 'tsx',
          tsconfig: {
            compilerOptions: {
              jsx: 'react-jsx',
              jsxImportSource: 'react'
            }
          }
        });
        
        const content = await file.text();
        const result = transpiler.transformSync(content, 'tsx');
        
        // Fix import paths and add JSX runtime import if needed
        let fixed = result
          .replace(/from ['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g, (match, path) => {
            return `from "${path}.js"`;
          })
          .replace(/import ([^'"]+) from ['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g, (match, name, path) => {
            return `import ${name} from "${path}.js"`;
          })
          .replace(/from ['"]react['"]/g, 'from "https://esm.sh/react@18"')
          .replace(/from ['"]react-dom\/client['"]/g, 'from "https://esm.sh/react-dom@18/client"')
          .replace(/from ['"]@tanstack\/react-query['"]/g, 'from "https://esm.sh/@tanstack/react-query@5?deps=react@18"')
          .replace(/from ['"]react-markdown['"]/g, 'from "https://esm.sh/react-markdown@10?deps=react@18"');
        
        // Remove type-only imports (those with "type" keyword)
        fixed = fixed.replace(/^import\s+type\s+\{[^}]*\}\s*from\s*['"][^'"]+['"];?\s*\n/gm, '');
        fixed = fixed.replace(/^import\s*\{([^}]*)\}\s*from\s*(['"][^'"]+['"]);?\s*\n/gm, (match, imports, path) => {
          // Keep imports from external packages
          if (path.includes('react') || path.includes('@tanstack') || path.includes('http')) {
            return match;
          }
          
          // Only filter out imports with explicit "type" modifier
          const importList = imports.split(',').map(i => i.trim());
          const runtimeImports = importList.filter(imp => {
            // Remove imports like "type Foo" but keep "Foo" and "useFoo"
            return !imp.trim().startsWith('type ');
          });
          
          if (runtimeImports.length === 0) {
            return ''; // Remove entirely if no runtime imports
          }
          
          if (runtimeImports.length !== importList.length) {
            // Rebuild import statement with only runtime imports
            return `import { ${runtimeImports.join(', ')} } from ${path};\n`;
          }
          
          return match; // Keep as-is if all are runtime
        });
        
        // Add JSX runtime import if JSX functions are used
        if (fixed.includes('jsxDEV') || fixed.includes('jsx(')) {
          fixed = `import { jsxDEV as jsxDEV_7x81h0kn } from "https://esm.sh/react@18/jsx-dev-runtime";\n` + fixed;
        }
        
        return new Response(fixed, {
          headers: {
            'Content-Type': 'application/javascript',
            'Cache-Control': 'no-cache'
          }
        });
      }
    }
    
    // Handle directory imports (e.g., /src/components/chat.js -> /src/components/chat/index.js)
    if (url.pathname.endsWith('.js') && url.pathname.startsWith('/src/')) {
      const potentialDir = url.pathname.replace(/\.js$/, '');
      const indexPath = `${potentialDir}/index.js`;
      
      // Check if it's a directory with an index file
      const dirPath = potentialDir.slice(1); // Remove leading slash
      const indexFilePath = join(process.cwd(), dirPath, 'index.ts');
      
      if (await Bun.file(indexFilePath).exists()) {
        // Redirect to the index.js version
        return Response.redirect(url.origin + indexPath, 301);
      }
    }
    
    // Handle paths without extension as potential modules
    if (url.pathname.startsWith('/src/') && !url.pathname.includes('.')) {
      // Redirect to .js version
      return Response.redirect(url.origin + url.pathname + '.js', 301);
    }
    
    // Serve index.html
    if (url.pathname === '/' || !url.pathname.includes('.')) {
      return new Response(Bun.file('./public/index.html'), {
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    return new Response('Not found', { status: 404 });
  }
});

console.log(`Development server running at http://localhost:${server.port}`);