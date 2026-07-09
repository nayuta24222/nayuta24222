/* Delete Me Not. — Electron デスクトップ版エントリ
   ゲーム本体（../index.html 一式）を app/ にコピーした上で起動する。
   ビルド前に scripts/sync-app 相当の処理（README参照）で app/ を同期すること。 */
'use strict';
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

function resolveIndex() {
  // パッケージ時は app/ 配下、開発時（npm start）はリポジトリ直下を参照
  const packaged = path.join(__dirname, 'app', 'index.html');
  if (fs.existsSync(packaged)) return packaged;
  return path.join(__dirname, '..', 'index.html');
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 960,
    minHeight: 540,
    backgroundColor: '#05060a',
    autoHideMenuBar: true,
    title: 'Delete Me Not.',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  Menu.setApplicationMenu(null);
  win.setAspectRatio(16 / 9);
  win.loadFile(resolveIndex());
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
