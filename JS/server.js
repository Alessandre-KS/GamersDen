// JS/server.js
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { join, extname, resolve } from 'path';
import { fileURLToPath } from 'url';

// Fix for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = join(__filename, '..');
const projectRoot = resolve(__dirname, '..');

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.mjs': 'text/javascript',
    '.css': 'text/css',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.json': 'application/json',
    '.ico': 'image/x-icon',
    '.wasm': 'application/wasm',
    '.pck': 'application/octet-stream',
    '.data': 'application/octet-stream',
    '.apk': 'application/octet-stream',
    '.zip': 'application/zip',
    '.wav': 'audio/wav',
    '.mp3': 'audio/mpeg',
    '.ogg': 'audio/ogg',
    '.ttf': 'font/ttf',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2'
};

// Create HTTP server to serve your static files
const server = createServer(async (req, res) => {
    // Add CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    // Don't try to serve external CDN files - let browser handle them
    if (req.url.includes('cdnjs.cloudflare.com') || 
        req.url.includes('://') || 
        req.url.startsWith('//')) {
        res.writeHead(404);
        res.end('External resource - use CDN directly');
        return;
    }
    
    let cleanPath = decodeURIComponent(req.url.split('?')[0]);
    if (cleanPath === '/') cleanPath = '/index.html';
    const filePath = resolve(projectRoot, '.' + cleanPath);
    
    // Security: prevent directory traversal
    if (!filePath.startsWith(projectRoot)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
    }
    
    try {
        const content = await readFile(filePath);
        const ext = extname(filePath).toLowerCase();
        const contentType = mimeTypes[ext] || 'application/octet-stream';
        
        const range = req.headers.range;
        if (range) {
            const parts = range.replace(/bytes=/, "").split("-");
            const start = parseInt(parts[0], 10);
            const end = parts[1] ? parseInt(parts[1], 10) : content.length - 1;
            const chunksize = (end - start) + 1;
            res.writeHead(206, {
                'Content-Range': `bytes ${start}-${end}/${content.length}`,
                'Accept-Ranges': 'bytes',
                'Content-Length': chunksize,
                'Content-Type': contentType,
            });
            res.end(content.subarray(start, end + 1));
            return;
        }
        
        res.writeHead(200, { 
            'Content-Type': contentType,
            'Content-Length': content.length,
            'Accept-Ranges': 'bytes'
        });
        res.end(content);
    } catch (error) {
        console.log('📁 File not found:', req.url);
        res.writeHead(404);
        res.end('File not found');
    }
});

// Create WebSocket server
const wss = new WebSocketServer({ 
    server,
    verifyClient: (info, callback) => {
        const origin = info.origin || info.req.headers.origin;
        if (origin && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
            console.log('🚫 Blocked connection from:', origin);
            callback(false, 403, 'Forbidden');
        } else {
            callback(true);
        }
    }
});

console.log('🚀 Starting GAMERS_DEN server...');

wss.on('connection', function connection(ws, req) {
    const clientId = Math.random().toString(36).substr(2, 9);
    console.log('✅ Client connected:', clientId);
    
    // Send immediate response
    try {
        ws.send(JSON.stringify({ 
            type: 'connected', 
            status: 'ok',
            message: 'Welcome to GAMERS_DEN 4.0!',
            clientId: clientId
        }));
    } catch (error) {
        console.error('Error sending welcome message:', error);
    }
    
    ws.on('message', function message(data) {
        try {
            console.log('📨 Received from', clientId + ':', data.toString().substring(0, 100));
            
            // Echo back safely
            if (ws.readyState === ws.OPEN) {
                ws.send(JSON.stringify({
                    type: 'echo',
                    message: `Server received your message`,
                    timestamp: Date.now()
                }));
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    });
    
    ws.on('close', function close() {
        console.log('❌ Client disconnected:', clientId);
    });
    
    ws.on('error', function error(err) {
        console.error('💥 WebSocket error for', clientId + ':', err);
    });
});

// Start the server
const PORT = 5500;
server.listen(PORT, () => {
    console.log(`✅ GAMERS_DEN server running on http://localhost:${PORT}`);
    console.log(`✅ WebSocket server ready on ws://localhost:${PORT}`);
    console.log('📍 Open http://localhost:5500 in your browser');
});