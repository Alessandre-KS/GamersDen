// assets/web_firebase.js - Enhanced Firebase Firestore bridge
console.log("🚀 web_firebase.js: Script loading...");

let firestore = null;
let firebaseInitialized = false;
let initializationAttempted = false;

// Firebase configuration
const firebaseConfig = {
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID",
    measurementId: "YOUR_MEASUREMENT_ID"
};

// Make functions available globally IMMEDIATELY
window.saveScoreToFirebase = saveScoreToFirebase;
window.getLeaderboardData = getLeaderboardData;
window.initializeFirebase = initializeFirebase;

console.log("✅ web_firebase.js: Global functions registered");

function initializeFirebase() {
    console.log("🔄 initializeFirebase() called");
    
    if (firebaseInitialized) {
        console.log("✅ Firebase already initialized");
        return true;
    }
    
    if (initializationAttempted) {
        console.log("🔄 Firebase initialization already attempted");
        return false;
    }
    
    initializationAttempted = true;
    
    try {
        // Check if Firebase is available
        console.log("🔍 Checking for Firebase SDK...");
        if (typeof firebase === 'undefined') {
            console.error("❌ Firebase SDK not loaded - make sure firebase scripts are included in HTML");
            return false;
        }

        console.log("✅ Firebase SDK found:", typeof firebase);
        console.log("Firebase version:", firebase.SDK_VERSION);

        // Initialize Firebase
        try {
            if (firebase.apps.length === 0) {
                firebase.initializeApp(firebaseConfig);
                console.log("✅ Firebase App initialized successfully");
            } else {
                console.log("✅ Using existing Firebase App");
            }
        } catch (appError) {
            console.error("❌ Firebase App initialization error:", appError);
            return false;
        }
        
        // Initialize Firestore
        try {
            console.log("🔧 Initializing Firestore...");
            firestore = firebase.firestore();
            
            // Enable offline persistence
            firestore.enablePersistence()
                .then(() => console.log("✅ Firestore persistence enabled"))
                .catch(err => console.warn("⚠️ Firestore persistence failed:", err));
                
            console.log("✅ Firestore initialized successfully");
            
        } catch (firestoreError) {
            console.error("❌ Firestore initialization error:", firestoreError);
            return false;
        }
        
        firebaseInitialized = true;
        console.log("🎉 Firebase Firestore fully initialized for leaderboard");
        return true;
        
    } catch (error) {
        console.error("💥 Critical Firebase initialization error:", error);
        return false;
    }
}

// Function to save score to Firestore
async function saveScoreToFirebase(name, wave) {
    console.log(`💾 saveScoreToFirebase() called: "${name}", Wave: ${wave}`);
    
    if (!firebaseInitialized && !initializeFirebase()) {
        console.error("❌ Cannot save - Firebase not initialized");
        return false;
    }
    
    try {
        // Validate inputs
        if (!name || name.trim() === '') {
            console.error("❌ Invalid player name");
            return false;
        }
        
        const waveNum = parseInt(wave);
        if (isNaN(waveNum) || waveNum < 1) {
            console.error("❌ Invalid wave number");
            return false;
        }

        const scoreData = {
            name: name.trim(),
            wave: waveNum,
            date: new Date().toLocaleDateString('en-US'),
            timestamp: firebase.firestore.FieldValue.serverTimestamp(),
            game: "Inscription Reloaded"
        };
        
        console.log("📊 Saving leaderboard data:", scoreData);
        
        const docRef = await firestore.collection('leaderboard').add(scoreData);
        console.log("✅ Score saved to leaderboard successfully! Document ID:", docRef.id);
        return true;
        
    } catch (error) {
        console.error("❌ Error saving score to Firestore:", error);
        return false;
    }
}

// Function to get leaderboard data from Firestore
async function getLeaderboardData(limit = 10) {
    console.log(`📊 getLeaderboardData() called, limit: ${limit}`);
    
    if (!firebaseInitialized && !initializeFirebase()) {
        console.error("❌ Cannot fetch - Firebase not initialized");
        return [];
    }
    
    try {
        const querySnapshot = await firestore.collection('leaderboard')
            .where('game', '==', 'Inscription Reloaded')
            .orderBy('wave', 'desc')
            .orderBy('timestamp', 'desc')
            .limit(limit)
            .get();
            
        const scores = [];
        
        querySnapshot.forEach((doc) => {
            const data = doc.data();
            if (data.name && data.wave) {
                scores.push([
                    data.name,
                    data.wave,
                    data.date || new Date().toLocaleDateString('en-US')
                ]);
            }
        });
        
        console.log(`✅ Successfully loaded ${scores.length} scores from leaderboard`);
        return scores;
        
    } catch (error) {
        console.error("❌ Error fetching leaderboard from Firestore:", error);
        return [];
    }
}

// Auto-initialize Firebase when script loads
console.log("🧪 Auto-initializing Firebase...");
setTimeout(() => {
    if (typeof firebase !== 'undefined') {
        initializeFirebase();
    } else {
        console.log("⏳ Firebase SDK not loaded yet, will initialize when needed");
    }
}, 1000);

console.log("🎯 Inscription RELOADED Firebase bridge fully loaded!");