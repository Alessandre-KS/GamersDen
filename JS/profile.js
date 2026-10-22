import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { 
    getAuth, 
    onAuthStateChanged, 
    signOut, 
    deleteUser,
    reauthenticateWithCredential,
    EmailAuthProvider
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";
import { 
    getFirestore, 
    doc, 
    getDoc, 
    deleteDoc,
    collection,
    query,
    where,
    getDocs
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

// Check if user is logged in with STRICT verification
onAuthStateChanged(auth, async (user) => {
    console.log("🔐 Auth state changed:", user ? "User logged in" : "No user");
    
    // STRICT VERIFICATION CHECK
    if (user && !user.emailVerified) {
        console.log("🚫 Email not verified - blocking profile access");
        showVerificationRequired();
        return;
    }
    
    if (user && user.emailVerified) {
        currentUser = user;
        console.log("✅ Current user UID:", user.uid);
        console.log("📧 User email:", user.email);
        console.log("✅ Email verified:", user.emailVerified);
        
        // Update UI to show user is authenticated
        updateAuthUI(true);
        
        await loadUserProfile(user.uid);
    } else {
        console.log("🚫 No verified user found, redirecting to login");
        updateAuthUI(false);
        window.location.href = 'login.html';
    }
});

// Show verification required message
function showVerificationRequired() {
    const profileContainer = document.querySelector('.profile-page') || document.body;
    profileContainer.innerHTML = `
        <div class="verification-required" style="display: flex; justify-content: center; align-items: center; min-height: 80vh; background: transparent; color: white; text-align: center; padding: 2rem;">
            <div style="background: var(--darker); padding: 3rem; border-radius: 15px; border: 3px solid var(--primary); max-width: 500px; width: 100%;">
                <div style="font-size: 4rem; color: var(--primary); margin-bottom: 1rem;">🚫</div>
                <h2 style="color: var(--primary); margin-bottom: 1rem; font-family: 'Press Start 2P', cursive;">EMAIL VERIFICATION REQUIRED</h2>
                <p style="margin-bottom: 1.5rem; line-height: 1.6;">
                    You must verify your email address before accessing your profile.
                </p>
                <p style="margin-bottom: 2rem; color: var(--text-secondary);">
                    Please check your inbox and click the verification link we sent to:<br>
                    <strong style="color: var(--primary);">${currentUser?.email || 'your email'}</strong>
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <button onclick="resendVerification()" style="background: var(--primary); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-family: 'Silkscreen', cursive;">
                        <i class="fas fa-envelope"></i> Resend Verification
                    </button>
                    <button onclick="handleLogout()" style="background: var(--secondary); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-family: 'Silkscreen', cursive;">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Resend verification email
async function resendVerification() {
    if (!currentUser) return;
    
    try {
        // Import sendEmailVerification dynamically
        const { sendEmailVerification } = await import("https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js");
        await sendEmailVerification(currentUser);
        alert('✅ Verification email sent! Please check your inbox and spam folder.');
    } catch (error) {
        console.error('Error sending verification email:', error);
        alert('❌ Error sending verification email: ' + error.message);
    }
}

// Update UI based on authentication state
function updateAuthUI(isAuthenticated) {
    const authElements = document.querySelectorAll('[data-auth]');
    authElements.forEach(element => {
        const authState = element.getAttribute('data-auth');
        if (authState === 'true') {
            element.style.display = isAuthenticated ? 'block' : 'none';
        } else if (authState === 'false') {
            element.style.display = isAuthenticated ? 'none' : 'block';
        }
    });
}

// Load user profile data
async function loadUserProfile(userId) {
    try {
        console.log("📥 Loading profile for user:", userId);
        
        // Show loading state
        showLoadingState(true);
        
        const userDoc = await getDoc(doc(db, "users", userId));
        
        if (userDoc.exists()) {
            const userData = userDoc.data();
            console.log("✅ User data found:", userData);
            
            // Display user information on profile page
            displayUserProfile(userData);
            
            // Load gaming statistics
            await loadGamingStatistics(userData);
            
        } else {
            console.error("❌ No user data found in Firestore");
            showErrorState("No user profile data found. Please contact support.");
        }
    } catch (error) {
        console.error("❌ Error loading profile:", error);
        
        if (error.code === 'permission-denied') {
            showErrorState("Permission denied. Please make sure you're logged in correctly.");
        } else if (error.code === 'not-found') {
            showErrorState("User profile not found. Please contact support.");
        } else {
            showErrorState('Error loading profile data: ' + error.message);
        }
    } finally {
        // Hide loading state
        showLoadingState(false);
    }
}

// Display user profile information
function displayUserProfile(userData) {
    console.log("🎯 Displaying user profile data:", userData);
    
    // Basic profile information
    setElementContent('profileName', userData.fullName || 'Not set');
    setElementContent('profileUsername', userData.userName || 'Not set');
    setElementContent('profileAge', userData.age || 'Not set');
    setElementContent('profileSection', userData.section || 'Not set');
    setElementContent('profileEmail', userData.email || 'Not set');
    
    // Format join date
    if (userData.joinDate) {
        const joinDate = new Date(userData.joinDate);
        setElementContent('profileJoinDate', joinDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }));
    } else {
        setElementContent('profileJoinDate', 'Not available');
    }
    
    // Email verification status
    const emailVerified = currentUser?.emailVerified || userData.emailVerified;
    setElementContent('profileVerification', emailVerified ? 
        '<span style="color: #4CAF50;">✅ Verified</span>' : 
        '<span style="color: #ff9800;">⚠️ Not Verified</span>'
    );
    
    // Show profile section
    showSection('profileSection');
    console.log("✅ Profile data displayed successfully");
}

// Helper function to set element content safely
function setElementContent(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    } else {
        console.warn(`⚠️ Element with ID '${elementId}' not found`);
    }
}

// Helper function to show section safely
function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
    }
}

// Load gaming statistics
async function loadGamingStatistics(userData) {
    try {
        console.log("📊 Loading gaming statistics...");
        
        // Total Play Time
        const totalPlayTime = userData.totalPlayTime || 0;
        console.log(`⏱️ Raw total play time: ${totalPlayTime} seconds`);
        
        const hours = Math.floor(totalPlayTime / 3600);
        const minutes = Math.floor((totalPlayTime % 3600) / 60);
        const seconds = totalPlayTime % 60;
        
        let timeDisplay = '';
        if (hours > 0) {
            timeDisplay = `${hours}h ${minutes}m ${seconds}s`;
        } else if (minutes > 0) {
            timeDisplay = `${minutes}m ${seconds}s`;
        } else {
            timeDisplay = `${seconds}s`;
        }
        
        setElementContent('totalPlayTime', timeDisplay);
        console.log(`⏱️ Formatted play time: ${timeDisplay}`);
        
        // Most Played Game
        const gameVisits = userData.gameVisits || {};
        console.log(`🎮 Game visits:`, gameVisits);
        
        let mostPlayedGame = 'No games played yet';
        let maxVisits = 0;
        
        Object.entries(gameVisits).forEach(([game, visits]) => {
            console.log(`Game: ${game}, Visits: ${visits}`);
            if (visits > maxVisits) {
                maxVisits = visits;
                mostPlayedGame = formatGameName(game);
            }
        });
        
        setElementContent('mostPlayedGame', mostPlayedGame);
        setElementContent('gameVisitCount', maxVisits > 0 ? `${maxVisits} visit${maxVisits !== 1 ? 's' : ''}` : 'No visits');
        console.log(`🏆 Most played game: ${mostPlayedGame} (${maxVisits} visits)`);
        
        // Total Sessions
        const totalSessions = userData.totalSessions || 0;
        setElementContent('totalSessions', totalSessions);
        console.log(`🔢 Total sessions: ${totalSessions}`);
        
        // Last Session
        if (userData.lastSession) {
            const lastSession = new Date(userData.lastSession.toDate());
            setElementContent('lastSession', lastSession.toLocaleDateString());
        }
        
        // Show statistics section
        showSection('statsSection');
        console.log("✅ Gaming statistics displayed successfully");
        
    } catch (error) {
        console.error("❌ Error loading gaming statistics:", error);
        setElementContent('statsSection', '<p style="color: #ff6b6b;">Error loading statistics</p>');
    }
}

// Format game name for display
function formatGameName(gameKey) {
    const gameNames = {
        'cappucinyaa': 'CappuciNyaa~',
        'inscription_reloaded': 'Inscription Reloaded'
    };
    
    return gameNames[gameKey] || gameKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Show loading state
function showLoadingState(show) {
    const loadingElement = document.getElementById('loadingState');
    const profileElement = document.getElementById('profileSection');
    const statsElement = document.getElementById('statsSection');
    
    if (loadingElement) {
        loadingElement.style.display = show ? 'block' : 'none';
    }
    
    if (!show) {
        if (profileElement) profileElement.style.display = 'block';
        if (statsElement) statsElement.style.display = 'block';
    }
}

// Show error state
function showErrorState(message) {
    const errorElement = document.getElementById('errorState');
    if (errorElement) {
        errorElement.innerHTML = `<div class="error-message">${message}</div>`;
        errorElement.style.display = 'block';
    }
    
    // Hide other sections
    const profileSection = document.getElementById('profileSection');
    const statsSection = document.getElementById('statsSection');
    if (profileSection) profileSection.style.display = 'none';
    if (statsSection) statsSection.style.display = 'none';
}

// Logout function
function handleLogout() {
    console.log("🚪 Logout function called");
    
    // Show confirmation
    const confirmed = confirm('Are you sure you want to log out?');
    if (!confirmed) return;
    
    // Show loading state
    const logoutBtn = document.getElementById('logoutBtn');
    const originalText = logoutBtn?.innerHTML;
    if (logoutBtn) {
        logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
        logoutBtn.disabled = true;
    }
    
    signOut(auth).then(() => {
        console.log("✅ User signed out successfully");
        window.location.href = 'login.html';
    }).catch((error) => {
        console.error("❌ Error during logout:", error);
        alert('Error during logout: ' + error.message);
        
        // Reset button
        if (logoutBtn) {
            logoutBtn.innerHTML = originalText;
            logoutBtn.disabled = false;
        }
    });
}

// Show delete confirmation modal
function showDeleteConfirmation() {
    console.log("🗑️ Show delete confirmation called");
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'flex';
        console.log("✅ Delete modal shown");
        
        // Reset password field
        const passwordInput = document.getElementById('deletePassword');
        if (passwordInput) {
            passwordInput.value = '';
            passwordInput.focus(); // Focus on password field
        }
    } else {
        console.error("❌ Delete modal element not found");
    }
}

// Hide delete confirmation modal
function hideDeleteConfirmation() {
    console.log("❌ Hide delete confirmation called");
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
        console.log("✅ Delete modal hidden");
    }
}

// Enhanced delete account function with reauthentication
async function deleteAccount() {
    console.log("=== 🗑️ DELETE ACCOUNT FUNCTION STARTED ===");
    
    if (!currentUser) {
        console.error("❌ No current user found");
        alert('No user logged in');
        return;
    }

    console.log("🗑️ Deleting account for user:", currentUser.uid);
    console.log("📧 User email:", currentUser.email);

    try {
        // Get password from modal - SAFELY
        const passwordInput = document.getElementById('deletePassword');
        if (!passwordInput) {
            console.error("❌ Password input not found in modal");
            alert('Error: Password input not found. Please refresh the page and try again.');
            return;
        }

        const password = passwordInput.value;
        if (!password) {
            alert('Please enter your password to confirm account deletion.');
            passwordInput.focus();
            return;
        }

        // Show loading state
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (deleteBtn) {
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> DELETING...';
            deleteBtn.disabled = true;
        }

        console.log("🔐 Step 1: Reauthenticating user...");
        
        // Reauthenticate user
        const credential = EmailAuthProvider.credential(currentUser.email, password);
        await reauthenticateWithCredential(currentUser, credential);
        console.log("✅ User reauthenticated successfully");

        console.log("🗃️ Step 2: Deleting Firestore data...");
        
        // Delete user data from Firestore - users collection
        await deleteDoc(doc(db, "users", currentUser.uid));
        console.log("✅ Firestore user data deleted successfully");
        
        // Delete username reservation
        try {
            const usernameQuery = query(
                collection(db, "usernames"), 
                where("uid", "==", currentUser.uid)
            );
            const usernameSnapshot = await getDocs(usernameQuery);
            
            if (!usernameSnapshot.empty) {
                const usernameDoc = usernameSnapshot.docs[0];
                await deleteDoc(doc(db, "usernames", usernameDoc.id));
                console.log("✅ Username reservation deleted");
            }
        } catch (error) {
            console.warn("⚠️ Could not delete username reservation:", error);
        }
        
        console.log("👤 Step 3: Deleting Authentication user...");
        
        // Delete user from Authentication
        await deleteUser(currentUser);
        console.log("✅ Authentication user deleted successfully");
        
        // Success - redirect to login page
        console.log("🎉 Account deletion complete, redirecting to login");
        
        // Show success message
        alert('Account deleted successfully. Thank you for using our service!');
        window.location.href = 'login.html';
        
    } catch (error) {
        console.error("❌ Error deleting account:", error);
        console.error("Error code:", error.code);
        console.error("Error message:", error.message);
        
        // Handle specific error cases
        let errorMessage = 'Error deleting account: ';
        
        if (error.code === 'auth/wrong-password') {
            errorMessage = 'Incorrect password. Please try again.';
            // Clear password field and focus on it
            const passwordInput = document.getElementById('deletePassword');
            if (passwordInput) {
                passwordInput.value = '';
                passwordInput.focus();
            }
        } else if (error.code === 'auth/requires-recent-login') {
            errorMessage = 'For security reasons, please log out and log in again before deleting your account.';
        } else if (error.code === 'auth/too-many-requests') {
            errorMessage = 'Too many attempts. Please try again later.';
        } else if (error.code === 'permission-denied') {
            errorMessage = 'Permission denied. Please check if you are properly authenticated.';
        } else if (error.code === 'not-found') {
            errorMessage = 'User data not found. The account may have already been deleted.';
        } else {
            errorMessage += error.message;
        }
        
        alert(errorMessage);
        
        // Reset button state
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (deleteBtn) {
            deleteBtn.innerHTML = 'DELETE ACCOUNT';
            deleteBtn.disabled = false;
        }
        
        // Don't hide modal on error so user can try again
    }
}

// Setup event listeners
function setupEventListeners() {
    console.log("🔗 Setting up event listeners...");
    
    // Get all buttons by ID
    const logoutBtn = document.getElementById('logoutBtn');
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    
    // Add event listeners
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            console.log("🚪 LOGOUT BUTTON CLICKED");
            e.preventDefault();
            handleLogout();
        });
        console.log("✅ Logout button listener added");
    } else {
        console.warn("⚠️ Logout button not found");
    }
    
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function(e) {
            console.log("🗑️ DELETE ACCOUNT BUTTON CLICKED");
            e.preventDefault();
            showDeleteConfirmation();
        });
        console.log("✅ Delete account button listener added");
    } else {
        console.warn("⚠️ Delete account button not found");
    }
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function(e) {
            console.log("✅ CONFIRM DELETE BUTTON CLICKED - STARTING DELETE PROCESS");
            e.preventDefault();
            e.stopPropagation();
            deleteAccount();
        });
        console.log("✅ Confirm delete button listener added");
    } else {
        console.warn("⚠️ Confirm delete button not found");
    }
    
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function(e) {
            console.log("❌ CANCEL BUTTON CLICKED");
            e.preventDefault();
            hideDeleteConfirmation();
        });
        console.log("✅ Cancel button listener added");
    } else {
        console.warn("⚠️ Cancel button not found");
    }
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', function(e) {
            console.log("❌ MODAL CLOSE BUTTON CLICKED");
            e.preventDefault();
            hideDeleteConfirmation();
        });
        console.log("✅ Modal close button listener added");
    } else {
        console.warn("⚠️ Modal close button not found");
    }
    
    // Add keyboard event for modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideDeleteConfirmation();
        }
        // Allow Enter key to submit delete (but only if password field is focused)
        if (e.key === 'Enter' && document.activeElement.id === 'deletePassword') {
            e.preventDefault();
            deleteAccount();
        }
    });
    
    // Add click outside modal to close
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideDeleteConfirmation();
            }
        });
    }
}

// Setup when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("📄 DOM loaded, setting up event listeners");
    setupEventListeners();
    console.log("✅ All event listeners setup complete");
    
    // Check if user data is already loaded
    if (currentUser) {
        console.log("🔄 User already authenticated, reloading profile");
        loadUserProfile(currentUser.uid);
    }
});

// Make functions available globally
window.handleLogout = handleLogout;
window.showDeleteConfirmation = showDeleteConfirmation;
window.hideDeleteConfirmation = hideDeleteConfirmation;
window.deleteAccount = deleteAccount;
window.resendVerification = resendVerification;

console.log("=== ✅ PROFILE.JS LOADED SUCCESSFULLY ===");
console.log("🔧 Functions attached to window object");
console.log("👤 Profile management system ready");