const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;
let staticServer;

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
};

function resolveBackendDir() {
  const candidates = [];
  try {
    const cfgPath = path.join(__dirname, 'backend-path.json');
    if (fs.existsSync(cfgPath)) {
      const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
      if (cfg.backendDir) candidates.push(cfg.backendDir);
    }
  } catch (e) {}

  candidates.push(
    path.join(__dirname, 'backend'),
    path.join(os.homedir(), 'tradeverse', 'backend'),
    path.join(os.homedir(), 'Desktop', 'tradeverse', 'backend'),
    path.join(os.homedir(), '.gemini', 'antigravity', 'scratch', 'tradeverse', 'backend')
  );

  for (const dir of candidates) {
    if (dir && fs.existsSync(path.join(dir, 'main.py'))) {
      return dir;
    }
  }
  return null;
}

function checkPortAlive(port, timeout = 1000) {
  return new Promise((resolve) => {
    const req = http.get({ hostname: '127.0.0.1', port, path: '/', timeout }, (res) => {
      res.resume();
      resolve(true);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function ensureBackendRunning() {
  const isUp = await checkPortAlive(8000);
  if (isUp) return;

  const backendDir = resolveBackendDir();
  if (!backendDir) return;

  const venvPython = path.join(backendDir, '.venv', 'bin', 'python3');
  const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python3';

  const env = Object.assign({}, process.env, {
    PATH: `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${process.env.PATH || ''}`,
    PYTHONUNBUFFERED: '1'
  });

  backendProcess = spawn(pythonBin, ['main.py'], {
    cwd: backendDir,
    env,
    stdio: 'ignore',
    detached: false
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to spawn Tradeverse backend:', err);
  });
}

async function ensureFrontendServer() {
  const isViteUp = await checkPortAlive(5173);
  if (isViteUp) return;

  const distDir = path.join(__dirname, 'frontend', 'dist');

  return new Promise((resolve) => {
    staticServer = http.createServer((req, res) => {
      const urlPath = (req.url || '/').split('?')[0];

      // Proxy /api and /backend-status to local Python Backend on port 8000
      if (urlPath.startsWith('/api') || urlPath.startsWith('/backend-status')) {
        const targetPath = req.url.replace(/^\/backend-status/, '') || '/';
        const proxyReq = http.request(
          {
            hostname: '127.0.0.1',
            port: 8000,
            path: targetPath,
            method: req.method,
            headers: req.headers
          },
          (proxyRes) => {
            res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
            proxyRes.pipe(res, { end: true });
          }
        );
        proxyReq.on('error', () => {
          res.writeHead(502, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'starting', detail: 'Backend warming up...' }));
        });
        req.pipe(proxyReq, { end: true });
        return;
      }

      // Serve static files from frontend/dist
      let safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '');
      if (safePath === '/' || safePath === '') safePath = '/index.html';

      let filePath = path.join(distDir, safePath);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(distDir, 'index.html');
      }

      fs.readFile(filePath, (err, content) => {
        if (err) {
          res.writeHead(404);
          res.end('Not found');
          return;
        }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
        res.end(content);
      });
    });

    staticServer.on('error', () => resolve());
    staticServer.listen(5173, '127.0.0.1', () => resolve());
  });
}

async function createWindow() {
  await ensureBackendRunning();
  await ensureFrontendServer();

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1000,
    minHeight: 700,
    title: 'Tradeverse AI',
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0a0a14',
    icon: path.join(__dirname, 'build/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      devTools: true
    },
    show: false
  });

  mainWindow.loadURL('http://localhost:5173');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  const template = [
    {
      label: 'Tradeverse AI',
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.on('will-quit', () => {
  if (backendProcess) {
    try { backendProcess.kill(); } catch (e) {}
  }
  if (staticServer) {
    try { staticServer.close(); } catch (e) {}
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.whenReady().then(createWindow);
