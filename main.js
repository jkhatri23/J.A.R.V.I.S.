const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');

// Create the main application window
let mainWindow;

// Function to check if a server is running
function waitForServer(url, maxAttempts = 30, interval = 1000) {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        
        const checkServer = () => {
            http.get(url, (res) => {
                if (res.statusCode === 200) {
                    resolve();
                } else {
                    attempts++;
                    if (attempts >= maxAttempts) {
                        reject(new Error(`Server not available after ${maxAttempts} attempts`));
                    } else {
                        setTimeout(checkServer, interval);
                    }
                }
            }).on('error', () => {
                attempts++;
                if (attempts >= maxAttempts) {
                    reject(new Error(`Server not available after ${maxAttempts} attempts`));
                } else {
                    setTimeout(checkServer, interval);
                }
            });
        };
        
        checkServer();
    });
}

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

    // Wait for the frontend server to be available
    waitForServer('http://localhost:3000')
        .then(() => {
            mainWindow.loadURL('http://localhost:3000');
        })
        .catch((error) => {
            console.error('Failed to connect to frontend server:', error);
            mainWindow.loadFile(path.join(__dirname, 'chatbot-frontend/out/index.html'));
        });

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

// Function to find a file in the filesystem
function findFileInFilesystem(filename) {
    const searchPaths = [
        path.join(homeDir, 'Documents'),
        path.join(homeDir, 'Downloads'),
        path.join(homeDir, 'Desktop'),
        path.join(homeDir, 'Pictures'),
        path.join(homeDir, 'Music'),
        path.join(homeDir, 'Videos')
    ];

    // First check common directories
    for (const dir of searchPaths) {
        const filePath = path.join(dir, filename);
        if (fs.existsSync(filePath)) {
            return filePath;
        }
    }

    // If not found in common directories, search the entire home directory
    try {
        const files = fs.readdirSync(homeDir, { withFileTypes: true });
        for (const file of files) {
            if (file.isDirectory()) {
                const dirPath = path.join(homeDir, file.name);
                try {
                    const foundPath = findFileInDirectory(dirPath, filename);
                    if (foundPath) return foundPath;
                } catch (err) {
                    // Skip directories we can't access
                    continue;
                }
            }
        }
    } catch (err) {
        console.error('Error searching home directory:', err);
    }

    return null;
}

// Helper function to recursively search a directory
function findFileInDirectory(dirPath, filename) {
    const files = fs.readdirSync(dirPath, { withFileTypes: true });
    
    for (const file of files) {
        const fullPath = path.join(dirPath, file.name);
        
        if (file.isDirectory()) {
            try {
                const foundPath = findFileInDirectory(fullPath, filename);
                if (foundPath) return foundPath;
            } catch (err) {
                // Skip directories we can't access
                continue;
            }
        } else if (file.name === filename) {
            return fullPath;
        }
    }
    
    return null;
}

// Function to find a directory using depth-first search
function findDirectoryDFS(startPath, targetDir) {
    try {
        // First check common directories
        const commonDirs = [
            path.join(startPath, 'Desktop'),
            path.join(startPath, 'Documents'),
            path.join(startPath, 'Downloads'),
            path.join(startPath, 'Pictures'),
            path.join(startPath, 'Music'),
            path.join(startPath, 'Videos')
        ];

        // Check common directories first
        for (const dirPath of commonDirs) {
            if (fs.existsSync(dirPath) && path.basename(dirPath).toLowerCase() === targetDir.toLowerCase()) {
                return dirPath;
            }
        }

        // If not found in common directories, check if the target directory exists directly
        const targetPath = path.join(startPath, targetDir);
        if (fs.existsSync(targetPath)) {
            return targetPath;
        }

        // If still not found, perform a depth-first search
        const files = fs.readdirSync(startPath, { withFileTypes: true });
        for (const file of files) {
            if (file.isDirectory()) {
                const dirPath = path.join(startPath, file.name);
                try {
                    const foundPath = findDirectoryDFS(dirPath, targetDir);
                    if (foundPath) return foundPath;
                } catch (err) {
                    // Skip directories we can't access
                    continue;
                }
            }
        }
    } catch (err) {
        console.error(`Error searching directory ${startPath}:`, err);
    }
    return null;
}

// Function to create a DOCX file
async function createDocxFile(filePath, content) {
    try {
        // Create a temporary directory for the virtual environment
        const tempDir = path.join(os.tmpdir(), 'docx_env');
        const venvPath = path.join(tempDir, 'venv');
        const tempScript = path.join(tempDir, 'create_docx.py');

        // Create the Python script
        const pythonCode = `
import sys
from docx import Document

def create_docx(file_path, content):
    doc = Document()
    doc.add_paragraph(content)
    doc.save(file_path)

if __name__ == '__main__':
    create_docx(sys.argv[1], sys.argv[2])
`;

        // Write the Python script
        fs.mkdirSync(tempDir, { recursive: true });
        fs.writeFileSync(tempScript, pythonCode);

        // Create and activate virtual environment, install python-docx, and run the script
        const { execSync } = require('child_process');
        const commands = [
            `python3 -m venv "${venvPath}"`,
            `source "${venvPath}/bin/activate" && pip install python-docx`,
            `source "${venvPath}/bin/activate" && python "${tempScript}" "${filePath}" "${content}"`
        ];

        // Execute commands
        for (const command of commands) {
            execSync(command, { stdio: 'inherit', shell: '/bin/bash' });
        }

        // Clean up
        fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (error) {
        console.error('Error creating DOCX file:', error);
        throw error;
    }
}

// Handle file system operations
ipcMain.handle('create-file', async (event, { filename, content, targetDir }) => {
    try {
        let targetPath;
        
        // If targetDir is provided, find it using DFS
        if (targetDir) {
            // First try to find the directory using DFS
            targetPath = findDirectoryDFS(homeDir, targetDir);
            
            if (!targetPath) {
                // If directory not found, create it in the home directory
                targetPath = path.join(homeDir, targetDir);
            }
        } else {
            // Default to Downloads if no directory specified
            targetPath = getDirectoryPath('Downloads');
        }

        // Log the target path for debugging
        console.log('Creating file in directory:', targetPath);

        // Ensure the directory exists
        if (!fs.existsSync(targetPath)) {
            fs.mkdirSync(targetPath, { recursive: true });
        }

        // Create the file
        const filePath = path.join(targetPath, filename);
        console.log('Creating file at path:', filePath);
        
        // Handle different file types
        const extension = path.extname(filename).toLowerCase();
        
        if (extension === '.docx') {
            // Use python-docx for DOCX files
            await createDocxFile(filePath, content);
        } else {
            // For other file types, write directly
            fs.writeFileSync(filePath, content);
        }
        
        return { success: true, message: `File '${filename}' created successfully in ${targetPath}` };
    } catch (error) {
        console.error('Error creating file:', error);
        return { success: false, message: `Error creating file: ${error.message}` };
    }
});

ipcMain.handle('delete-file', async (event, { filename, targetDir }) => {
    try {
        let filePath;

        // If target directory is specified, only search there
        if (targetDir) {
            const targetPath = getDirectoryPath(targetDir);
            filePath = path.join(targetPath, filename);
            
            if (!fs.existsSync(filePath)) {
                throw new Error(`File '${filename}' not found in ${targetDir}`);
            }
        } else {
            // Search the entire filesystem for the file
            filePath = findFileInFilesystem(filename);
            
            if (!filePath) {
                throw new Error(`File '${filename}' not found in the filesystem`);
            }
        }

        // Delete the file
        fs.unlinkSync(filePath);
        return { success: true, message: `File '${filename}' deleted successfully from ${path.dirname(filePath)}` };
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
