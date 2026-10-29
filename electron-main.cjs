const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;
let frontendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
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

  // Load local Vite dev server if running, otherwise load bundled production dist
  const http = require('http');
  const req = http.get('http://localhost:5173', (res) => {
    mainWindow.loadURL('http://localhost:5173');
  });
  req.on('error', () => {
    mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
  });
  req.setTimeout(1200, () => {
    req.destroy();
    mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
  });

  // Smooth fade-in once content is ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create a minimal menu
  const template = [
    {
      label: 'Tradeverse',
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

// Ensure all sub-processes are killed on exit
app.on('will-quit', () => {
  if (backendProcess) backendProcess.kill();
  if (frontendProcess) frontendProcess.kill();
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

// Main initialization
app.whenReady().then(createWindow);
