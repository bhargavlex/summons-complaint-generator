/**
 * Minimal production server: static files + proxy /api and /health to backend.
 * Used when nginx cannot be pulled (e.g. registry/proxy issues).
 */
const http = require('http');
const url = require('url');
const path = require('path');
const fs = require('fs');

const BACKEND = process.env.BACKEND_URL || 'http://backend:8000';
const PORT = parseInt(process.env.PORT || '80', 10);
const STATIC_ROOT = path.join(__dirname, 'dist');

function serveStatic(req, res, filePath) {
  const ext = path.extname(filePath);
  const types = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
  };
  const ct = types[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.setHeader('Content-Type', ct);
    res.end(data);
  });
}

function proxy(req, res, targetPath) {
  const opts = url.parse(BACKEND + targetPath);
  opts.method = req.method;
  opts.headers = { ...req.headers, host: opts.host };
  const proxyReq = http.request(opts, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });
  proxyReq.on('error', (e) => {
    res.writeHead(502);
    res.end('Bad Gateway: ' + e.message);
  });
  req.pipe(proxyReq);
}

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  const p = parsed.pathname || '/';

  if (p.startsWith('/api') || p === '/health') {
    proxy(req, res, req.url);
    return;
  }

  let filePath = path.join(STATIC_ROOT, p === '/' ? 'index.html' : p);
  if (!path.relative(STATIC_ROOT, filePath).startsWith('..') && fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    serveStatic(req, res, filePath);
    return;
  }
  serveStatic(req, res, path.join(STATIC_ROOT, 'index.html'));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('Serving on port ' + PORT + ', forwarding /api and /health to ' + BACKEND);
});
