const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Create the main application window
let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,  // Disable nodeIntegration for security
            contextIsolation: true,  // Enable context isolation
            preload: path.join(__dirname, 'chatbot-frontend/electron/preload.js')  // Use preload script
        },
    });

    // Load your React frontend (index.html or index.tsx depending on your build process)
    mainWindow.loadURL('http://localhost:3000'); // For local development with React

    // When the window is closed, clean up
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
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

// Get user's home directory and handle paths based on OS
const homeDir = os.homedir();
const isWindows = process.platform === 'win32';

// Function to get the correct path for a directory
function getDirectoryPath(dirName) {
    if (isWindows) {
        // For Windows, use the correct path format
        const userProfile = process.env.USERPROFILE;
        const oneDrivePath = path.join(userProfile, 'OneDrive');
        
        switch (dirName) {
            case 'Documents':
                // Check if OneDrive Documents exists
                const oneDriveDocs = path.join(oneDrivePath, 'Documents');
                if (fs.existsSync(oneDriveDocs)) {
                    return oneDriveDocs;
                }
                // Fallback to regular Documents if OneDrive doesn't exist
                return path.join(userProfile, 'Documents');
            case 'Desktop':
                // Check if OneDrive Desktop exists
                const oneDriveDesktop = path.join(oneDrivePath, 'Desktop');
                if (fs.existsSync(oneDriveDesktop)) {
                    return oneDriveDesktop;
                }
                // Fallback to regular Desktop if OneDrive doesn't exist
                return path.join(userProfile, 'Desktop');
            case 'Downloads':
                return path.join(userProfile, 'Downloads');
            default:
                throw new Error(`Invalid directory: ${dirName}`);
        }
    } else {
        // For macOS and Linux
        return path.join(homeDir, dirName);
    }
}

// Handle file system operations
ipcMain.handle('create-file', async (event, { filename, content, targetDir }) => {
    try {
        let targetPath;
        
        // Determine the target directory
        if (targetDir) {
            const validDirs = ['Documents', 'Downloads', 'Desktop'];
            if (!validDirs.includes(targetDir)) {
                throw new Error(`Invalid directory. Please use one of: ${validDirs.join(', ')}`);
            }
            targetPath = getDirectoryPath(targetDir);
        } else {
            targetPath = getDirectoryPath('Downloads');
        }

        // Log the target path for debugging
        console.log('Creating file in directory:', targetPath);

        // Check if the directory exists
        if (!fs.existsSync(targetPath)) {
            throw new Error(`Directory '${targetDir || 'Downloads'}' not found. Please make sure the directory exists.`);
        }

        // Create the file
        const filePath = path.join(targetPath, filename);
        console.log('Creating file at path:', filePath);
        
        fs.writeFileSync(filePath, content);
        
        return { success: true, message: `File '${filename}' created successfully in ${targetDir || 'Downloads'}` };
    } catch (error) {
        console.error('Error creating file:', error);
        return { success: false, message: `Error creating file: ${error.message}` };
    }
});

ipcMain.handle('delete-file', async (event, { filename, targetDir }) => {
    try {
        let targetPath;
        
        // Determine the target directory
        if (targetDir) {
            const validDirs = ['Documents', 'Downloads', 'Desktop'];
            if (!validDirs.includes(targetDir)) {
                throw new Error(`Invalid directory. Please use one of: ${validDirs.join(', ')}`);
            }
            targetPath = getDirectoryPath(targetDir);
        } else {
            targetPath = getDirectoryPath('Downloads');
        }

        const filePath = path.join(targetPath, filename);
        
        if (!fs.existsSync(filePath)) {
            throw new Error(`File '${filename}' not found in ${targetDir || 'Downloads'}`);
        }

        fs.unlinkSync(filePath);
        return { success: true, message: `File '${filename}' deleted successfully from ${targetDir || 'Downloads'}` };
    } catch (error) {
        console.error('Error deleting file:', error);
        return { success: false, message: `Error deleting file: ${error.message}` };
    }
});

// Handle file dialog operations
ipcMain.handle('open-file-dialog', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openFile'],
    });
    return result.filePaths;
});
