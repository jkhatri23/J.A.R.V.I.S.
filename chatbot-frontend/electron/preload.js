const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
    'electron',
    {
        invoke: (channel, data) => {
            // whitelist channels
            const validChannels = ['create-file', 'delete-file', 'open-file-dialog'];
            if (validChannels.includes(channel)) {
                return ipcRenderer.invoke(channel, data);
            }
            throw new Error(`Unauthorized IPC channel: ${channel}`);
        }
    }
); 