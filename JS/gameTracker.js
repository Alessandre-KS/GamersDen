// gameTracker.js - Complete Game Tracking System (No Debug Popup)
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { 
    getAuth, 
    onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";
import { 
    getFirestore, 
    doc, 
    updateDoc,
    increment,
    serverTimestamp,
    arrayUnion
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID",
    measurementId: "YOUR_MEASUREMENT_ID"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

let currentUser = null;
let sessionStartTime = null;
let currentGame = null;
let isTracking = false;
let periodicSaveInterval = null;

// Game pages mapping - matches working game file names
const gamePages = {
    'inscriptionReloadedframe.html': 'Inscription_Reloaded',
    'gameTwoFrame.html': 'CappuciNyaa'
};

// Alternative mapping using folder detection for better reliability
const gameFolders = {
    'inscriptionReloaded': 'Inscription_Reloaded',
    'gameTwo': 'CappuciNyaa'
};

// Initialize game tracking
function initializeGameTracking() {
    const currentPage = window.location.pathname;
    console.log("📍 Current page path:", currentPage);
    
    currentGame = getGameFromPage(currentPage);
    
    if (currentGame) {
        console.log(`🎮 Tracking started for: ${currentGame}`);
        startGameSession();
        
        // Track when user leaves the page
        window.addEventListener('beforeunload', endGameSession);
        window.addEventListener('pagehide', endGameSession);
        window.addEventListener('unload', endGameSession);
        
    } else {
        console.log('❌ Not a game frame page, tracking disabled');
        console.log('🔍 Page path:', currentPage);
    }
}

function getGameFromPage(pagePath) {
    // Method 1: Check by exact filename
    const pageName = pagePath.split('/').pop();
    console.log("📄 Page name:", pageName);
    
    if (gamePages[pageName]) {
        console.log("✅ Game found by filename:", gamePages[pageName]);
        return gamePages[pageName];
    }
    
    // Method 2: Check by folder name (more reliable)
    for (const [folder, gameName] of Object.entries(gameFolders)) {
        if (pagePath.includes(folder)) {
            console.log("✅ Game found by folder:", gameName);
            return gameName;
        }
    }
    
    // Method 3: Check for common game frame patterns
    if (pagePath.includes('Frame.html') || pagePath.includes('frame.html')) {
        // Extract game name from path
        const pathParts = pagePath.split('/');
        const gameFolder = pathParts[pathParts.length - 2]; // Get folder name
        console.log("🔍 Game folder detected:", gameFolder);
        
        if (gameFolders[gameFolder]) {
            console.log("✅ Game found by folder mapping:", gameFolders[gameFolder]);
            return gameFolders[gameFolder];
        }
        
        // Fallback: Use folder name as game name
        const fallbackGame = gameFolder.replace(/([A-Z])/g, ' $1').trim();
        console.log("🔄 Using fallback game name:", fallbackGame);
        return fallbackGame || 'Unknown_Game';
    }
    
    console.log("❌ No game mapping found for page:", pagePath);
    return null;
}

async function startGameSession() {
    if (!currentGame || isTracking) return;
    
    const user = auth.currentUser;
    if (!user) {
        console.log('❌ No user logged in, cannot track session');
        return;
    }
    
    sessionStartTime = Date.now();
    isTracking = true;
    
    try {
        // Record game visit and session start
        const gameKey = currentGame.replace(/\s+/g, '_').toLowerCase();
        
        await updateDoc(doc(db, "users", user.uid), {
            [`gameVisits.${gameKey}`]: increment(1),
            totalSessions: increment(1),
            lastSession: serverTimestamp(),
            gameSessions: arrayUnion({
                game: currentGame,
                startTime: new Date().toISOString(),
                duration: 0,
                sessionId: generateSessionId()
            })
        });
        
        console.log(`▶️ Game session started for: ${currentGame}`);
        console.log(`🕒 Session start time: ${new Date(sessionStartTime).toLocaleTimeString()}`);
        
        // Start periodic saving
        startPeriodicSaving();
        
    } catch (error) {
        console.error("❌ Error starting game session:", error);
        if (error.code === 'permission-denied') {
            console.error("Firestore permissions denied. Please check security rules.");
        }
    }
}

async function endGameSession() {
    if (!currentGame || !isTracking || !sessionStartTime) {
        console.log('❌ No active session to end');
        return;
    }
    
    const user = auth.currentUser;
    if (!user) {
        console.log('❌ No user logged in, cannot end session');
        return;
    }
    
    const sessionEndTime = Date.now();
    const sessionDuration = Math.floor((sessionEndTime - sessionStartTime) / 1000);
    
    // Only record sessions longer than 5 seconds to avoid accidental clicks
    if (sessionDuration < 5) {
        console.log(`⏱️ Session too short (${sessionDuration}s), not recording`);
        cleanupSession();
        return;
    }
    
    try {
        // Update total play time
        await updateDoc(doc(db, "users", user.uid), {
            totalPlayTime: increment(sessionDuration),
            lastSession: serverTimestamp()
        });
        
        console.log(`⏹️ Game session ended for: ${currentGame}`);
        console.log(`🕒 Session duration: ${sessionDuration} seconds`);
        console.log(`📊 Total play time updated by: ${sessionDuration}s`);
        
    } catch (error) {
        console.error("❌ Error ending game session:", error);
        if (error.code === 'permission-denied') {
            console.error("Firestore permissions denied. Please check security rules.");
        }
    }
    
    cleanupSession();
}

function startPeriodicSaving() {
    if (periodicSaveInterval) {
        clearInterval(periodicSaveInterval);
    }
    
    periodicSaveInterval = setInterval(async () => {
        if (isTracking && sessionStartTime && currentUser) {
            const currentDuration = Math.floor((Date.now() - sessionStartTime) / 1000);
            if (currentDuration > 30) { // Only save if more than 30 seconds
                try {
                    await updateDoc(doc(db, "users", currentUser.uid), {
                        totalPlayTime: increment(30)
                    });
                    sessionStartTime = Date.now(); // Reset start time
                    console.log(`💾 Periodic save: Added 30 seconds to total play time`);
                } catch (error) {
                    console.error("❌ Error in periodic save:", error);
                }
            }
        }
    }, 30000); // Every 30 seconds
}

function cleanupSession() {
    // Stop periodic saving
    if (periodicSaveInterval) {
        clearInterval(periodicSaveInterval);
        periodicSaveInterval = null;
    }
    
    isTracking = false;
    sessionStartTime = null;
    currentGame = null;
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Game Tracker Initializing...');
    
    onAuthStateChanged(auth, (user) => {
        if (user) {
            currentUser = user;
            console.log('✅ User authenticated:', user.email);
            initializeGameTracking();
        } else {
            console.log('❌ No user authenticated - tracking disabled');
        }
    });
});

// Make functions available globally for manual testing (but no popup)
window.endGameSession = endGameSession;
window.getCurrentGame = () => currentGame;
window.getSessionDuration = () => {
    if (!sessionStartTime) return 0;
    return Math.floor((Date.now() - sessionStartTime) / 1000);
};

console.log('✅ Game Tracker System Loaded');