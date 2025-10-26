const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const axios = require('axios');
const path = require('path');

// Keep a global reference of the window object
let mainWindow;

// Ollama configuration
const OLLAMA_BASE_URL = 'http://localhost:11434';

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'assets', 'athena-icon.png'),
    titleBarStyle: 'hiddenInset',
    show: false
  });

  // Load the HTML file
  mainWindow.loadFile('index.html');

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Load available models on startup
    loadModels();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create menu
  createMenu();
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'Athena',
      submenu: [
        {
          label: 'About Athena',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Athena Desktop',
              message: 'Athena Desktop UI',
              detail: 'Custom desktop interface for Ollama with Athena capabilities'
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
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
    },
    {
      label: 'Models',
      submenu: [
        {
          label: 'Refresh Models',
          click: () => {
            loadModels();
          }
        },
        {
          label: 'Manage Models',
          click: () => {
            mainWindow.webContents.send('show-model-manager');
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Keyboard Shortcuts',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Keyboard Shortcuts',
              message: 'Athena Desktop Shortcuts',
              detail: 'Cmd/Ctrl+Enter: Send message\nCmd/Ctrl+N: New chat\nCmd/Ctrl+S: Save chat\nCmd/Ctrl+R: Refresh models'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Load available models from Ollama
async function loadModels() {
  try {
    const response = await axios.get(`${OLLAMA_BASE_URL}/api/tags`);
    const models = response.data.models || [];
    
    if (mainWindow) {
      mainWindow.webContents.send('models-loaded', models);
    }
  } catch (error) {
    console.error('Failed to load models:', error);
    if (mainWindow) {
      mainWindow.webContents.send('models-error', error.message);
    }
  }
}

// Send message to Ollama
async function sendMessage(model, message, systemPrompt = '') {
  try {
    const response = await axios.post(`${OLLAMA_BASE_URL}/api/generate`, {
      model: model,
      prompt: message,
      system: systemPrompt,
      stream: false
    });

    return response.data.response;
  } catch (error) {
    console.error('Failed to send message:', error);
    throw error;
  }
}

// IPC handlers
ipcMain.handle('send-message', async (event, { model, message, systemPrompt }) => {
  try {
    const response = await sendMessage(model, message, systemPrompt);
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('load-models', async () => {
  try {
    const response = await axios.get(`${OLLAMA_BASE_URL}/api/tags`);
    return { success: true, models: response.data.models || [] };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('pull-model', async (event, modelName) => {
  try {
    const response = await axios.post(`${OLLAMA_BASE_URL}/api/pull`, {
      name: modelName,
      stream: false
    });
    return { success: true, response };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle app protocol for deep linking
app.setAsDefaultProtocolClient('athena');
