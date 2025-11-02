import { contextBridge, ipcRenderer } from 'electron';

// 暴露受保护的方法给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 截图功能（后续实现）
  captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
  
  // 其他 Electron API 可以在这里添加
});
