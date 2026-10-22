// JS/websocket-client.js - Minimal version
console.log('🔌 Loading WebSocket client...');

let connectionAttempted = false;

function safeConnect() {
    if (connectionAttempted) return;
    connectionAttempted = true;
    
    try {
        console.log('🔄 Attempting WebSocket connection...');
        const socket = new WebSocket('ws://localhost:5500');
        
        socket.onopen = function(event) {
            console.log('✅ WebSocket connected successfully!');
        };
        
        socket.onmessage = function(event) {
            console.log('📨 Message from server:', event.data);
        };
        
        socket.onclose = function(event) {
            console.log('❌ WebSocket disconnected');
        };
        
        socket.onerror = function(error) {
            console.log('💥 WebSocket connection error');
        };
        
        window.gameSocket = socket;
        
    } catch (error) {
        console.log('⚠️ WebSocket failed:', error.message);
    }
}

// Wait for page to fully load before connecting
window.addEventListener('load', function() {
    setTimeout(safeConnect, 2000); // Wait 2 seconds after load
});