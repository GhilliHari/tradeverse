const { app, BrowserWindow, Menu, ipcMain, Notification, shell } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;

const FRONTEND_URL = 'http://localhost:5173';
const ICON_PATH = path.join(__dirname, '../../icon.png');

function isPortOpen(port) {
  return new Promise((resolve) => {
    const req = http.get('http://localhost:' + port + '/docs', (res) => {
      resolve(res.statusCode === 200 || res.statusCode === 404);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function ensureBackendRunning() {
  const isRunning = await isPortOpen(8000);
  if (!isRunning) {
    console.log('🚀 Spawning Tradeverse FastAPI Backend Process...');
    const backendDir = path.join(__dirname, '../../backend');
    const venvPython = path.join(backendDir, '.venv/bin/python3');
    const mainPy = path.join(backendDir, 'main.py');
    
    backendProcess = spawn(venvPython, [mainPy], {
      cwd: backendDir,
      stdio: 'ignore',
      detached: true
    });
    backendProcess.unref();
  } else {
    console.log('✅ Tradeverse Backend is online on port 8000');
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1200,
    minHeight: 750,
    title: 'Tradeverse Desktop - Algorithmic Trading & Market Observatory',
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0b0f19',
    icon: ICON_PATH,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    }
  });

  mainWindow.loadURL(FRONTEND_URL).catch(() => {
    console.log('Vite dev server not found, loading static dist build...');
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createMenu() {
  const template = [
    {
      label: 'Tradeverse',
      submenu: [
        { role: 'about', label: 'About Tradeverse Desktop' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit', label: 'Quit Tradeverse' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload', accelerator: 'CmdOrCtrl+R' },
        { role: 'forceReload', accelerator: 'CmdOrCtrl+Shift+R' },
        { role: 'toggleDevTools', accelerator: 'Alt+CmdOrCtrl+I' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen', accelerator: 'F11' }
      ]
    },
    {
      label: 'Trading Systems',
      submenu: [
        {
          label: 'Open Web API Docs (Swagger)',
          click: () => shell.openExternal('http://localhost:8000/docs')
        },
        {
          label: 'Refresh Intelligence Data',
          click: () => {
            if (mainWindow) mainWindow.webContents.reload();
          }
        }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'front' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(async () => {
  await ensureBackendRunning();
  createMenu();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.on('notify', (event, { title, body }) => {
  if (Notification.isSupported()) {
    new Notification({ title, body, icon: ICON_PATH }).show();
  }
});

ipcMain.on('toggle-devtools', () => {
  if (mainWindow) {
    mainWindow.webContents.toggleDevTools();
  }
});
