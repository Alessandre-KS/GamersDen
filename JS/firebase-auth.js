// JS/firebase-auth.js - Centralized Firebase authentication with STRICT email verification
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";

console.log('🔥 Firebase auth initializing...');

const firebaseConfig = {
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID",
    measurementId: "YOUR_MEASUREMENT_ID"
};

// Initialize Firebase only once
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

console.log('✅ Firebase auth initialized');

// Global auth state management with STRICT email verification
onAuthStateChanged(auth, (user) => {
    const currentPage = window.location.pathname.split('/').pop();
    
    console.log('👤 Auth state changed:', user ? 'Logged in' : 'Not logged in');
    console.log('📄 Current page:', currentPage);
    if (user) {
        console.log('📧 Email verified:', user.emailVerified);
    }
    
    // STRICT VERIFICATION CHECK - BLOCK ACCESS IF EMAIL NOT VERIFIED
    if (user && !user.emailVerified) {
        console.log('🚫 Email not verified - blocking access');
        
        // Don't redirect if already on login page
        if (currentPage !== 'login.html' && !currentPage.includes('login')) {
            console.log('🔒 Redirecting to login for verification');
            
            // Force logout and redirect
            signOut(auth).then(() => {
                const message = '🚫 EMAIL VERIFICATION REQUIRED\n\nYou must verify your email before accessing the site.\n\nPlease check your inbox and click the verification link.';
                if (window.location.pathname.includes('profile.html')) {
                    // For profile page, show message on page
                    document.body.innerHTML = `
                        <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: var(--dark); color: white; text-align: center;">
                            <div style="background: var(--darker); padding: 2rem; border-radius: 10px; border: 2px solid var(--primary);">
                                <h1 style="color: var(--primary); margin-bottom: 1rem;">🚫 Verification Required</h1>
                                <p>${message}</p>
                                <button onclick="window.location.href='login.html'" style="background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 5px; margin-top: 1rem; cursor: pointer;">
                                    Go to Login
                                </button>
                            </div>
                        </div>
                    `;
                } else {
                    // For other pages, use alert and redirect
                    alert(message);
                    window.location.href = 'login.html';
                }
            }).catch((error) => {
                console.error('Error during logout:', error);
                window.location.href = 'login.html';
            });
        }
        return;
    }
    
    // Update UI based on auth state
    updateAuthUI(user);
    
    // Only redirect if we're not already on login page
    if (!user && currentPage !== 'login.html' && !currentPage.includes('login')) {
        console.log('🚫 Not authenticated, redirecting to login...');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1000);
    }
    
    // If user is logged in and verified, and on login page, redirect to home
    if (user && user.emailVerified && (currentPage === 'login.html' || currentPage.includes('login'))) {
        console.log('✅ Already logged in and verified, redirecting to home...');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    }
});

// Function to update UI based on authentication state
function updateAuthUI(user) {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const userInfo = document.getElementById('userInfo');
    
    if (loginBtn) loginBtn.style.display = user ? 'none' : 'block';
    if (logoutBtn) logoutBtn.style.display = user ? 'block' : 'none';
    
    if (userInfo && user) {
        userInfo.textContent = `Welcome, ${user.email}`;
        userInfo.style.display = 'block';
    }
}

// Logout functionality
function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await signOut(auth);
                alert('✅ Logged out successfully!');
                window.location.href = 'login.html';
            } catch (error) {
                console.error('Logout error:', error);
                alert('❌ Logout failed: ' + error.message);
            }
        });
    }
}

// Make auth available globally
window.firebaseAuth = auth;
window.firebaseSignOut = signOut;

// Initialize logout functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupLogout();
    console.log('✅ Firebase Auth System Ready');
});

// Export function to check verification status
window.checkEmailVerification = function() {
    const user = auth.currentUser;
    if (user && !user.emailVerified) {
        alert('🚫 EMAIL VERIFICATION REQUIRED\n\nPlease verify your email to access all features.');
        return false;
    }
    return true;
};