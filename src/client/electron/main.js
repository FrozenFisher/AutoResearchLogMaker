// Electron 主进程入口（开发模式使用 CommonJS）
const { app, BrowserWindow } = require('electron');
const path = require('path');
const http = require('http');

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
const VITE_DEV_SERVER_URL = 'http://localhost:5173';

// 等待 Vite 服务器启动
function waitForServer(url, maxAttempts = 30, delay = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const check = () => {
      attempts++;
      const urlObj = new URL(url);
      
      const req = http.get({
        hostname: urlObj.hostname,
        port: urlObj.port || 5173,
        path: '/',
        timeout: 1000
      }, (res) => {
        console.log(`✅ Vite 服务器已就绪 (${res.statusCode})`);
        resolve();
      });
      
      req.on('error', (err) => {
        if (attempts >= maxAttempts) {
          console.error(`❌ 等待 Vite 服务器超时: ${url}`);
          reject(new Error(`无法连接到 Vite 服务器: ${url}`));
        } else {
          console.log(`等待 Vite 服务器启动... (${attempts}/${maxAttempts})`);
          setTimeout(check, delay);
        }
      });
      
      req.on('timeout', () => {
        req.destroy();
        if (attempts >= maxAttempts) {
          reject(new Error(`连接 Vite 服务器超时: ${url}`));
        } else {
          setTimeout(check, delay);
        }
      });
    };
    
    check();
  });
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false, // 先不显示，等加载完成
  });

  // 监听加载完成
  mainWindow.webContents.once('did-finish-load', () => {
    mainWindow.show();
    console.log('✅ 应用加载完成');
  });

  // 监听加载失败
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`❌ 加载失败: ${errorCode} - ${errorDescription}`);
    mainWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>加载失败</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
          .error { color: #f56c6c; margin: 20px 0; }
          .info { color: #666; margin: 10px 0; }
          button { padding: 10px 20px; margin: 10px; cursor: pointer; }
        </style>
      </head>
      <body>
        <h1>无法连接到开发服务器</h1>
        <div class="error">错误: ${errorDescription}</div>
        <div class="info">
          <p>请确保 Vite 开发服务器已启动</p>
          <p>运行命令: <code>npm run dev</code></p>
        </div>
        <button onclick="location.reload()">重试</button>
      </body>
      </html>
    `));
    mainWindow.show();
  });

  if (isDev) {
    // 开发模式：等待 Vite 服务器启动
    waitForServer(VITE_DEV_SERVER_URL)
      .then(() => {
        console.log(`加载 URL: ${VITE_DEV_SERVER_URL}`);
        mainWindow.loadURL(VITE_DEV_SERVER_URL);
        mainWindow.webContents.openDevTools();
      })
      .catch((err) => {
        console.error(err.message);
        mainWindow.show();
      });
  } else {
    // 生产模式：加载本地文件
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
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
