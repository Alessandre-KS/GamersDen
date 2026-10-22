import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { 
    getAuth, 
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    sendEmailVerification,
    sendPasswordResetEmail,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";
import { 
    getFirestore, 
    doc, 
    setDoc, 
    getDoc, 
    collection, 
    query, 
    where, 
    getDocs,
    updateDoc 
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

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

console.log("🔥 Firebase initialized successfully");

// Enhanced connection test that works with your rules
async function testFirestoreConnection() {
    try {
        console.log("🔍 Testing Firestore connection...");
        
        // Test 1: Check if we can read usernames (public read)
        const usernameQuery = query(collection(db, "usernames"));
        await getDocs(usernameQuery);
        console.log("✅ Username collection readable");
        
        // Test 2: Check if authenticated user can write (only if logged in)
        const user = auth.currentUser;
        if (user) {
            const testDocRef = doc(collection(db, "connection_test"), "test_" + Date.now());
            await setDoc(testDocRef, {
                timestamp: new Date().toISOString(),
                uid: user.uid,
                test: true
            });
            console.log("✅ Authenticated write permissions working");
        } else {
            console.log("ℹ️ Not authenticated, skipping write test");
        }
        
        console.log("✅ All Firestore permissions working correctly");
        return true;
    } catch (error) {
        console.error("❌ Firestore connection failed:", error);
        
        let errorMessage = "Database connection error: ";
        if (error.code === 'permission-denied') {
            errorMessage += "Permissions denied. Please check if you're logged in and try again.";
        } else {
            errorMessage += error.message;
        }
        
        alert(errorMessage);
        return false;
    }
}

// Call connection test when auth state changes
onAuthStateChanged(auth, (user) => {
    if (user) {
        console.log("✅ User authenticated, testing Firestore connection...");
        testFirestoreConnection();
    }
});

// Tab switching functionality
document.querySelectorAll('.auth-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const targetTab = this.getAttribute('data-tab');
        
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
        document.getElementById(targetTab + 'Form').classList.add('active');
    });
});

// Switch link functionality
document.querySelectorAll('.switch-link').forEach(link => {
    link.addEventListener('click', function() {
        const targetTab = this.getAttribute('data-tab');
        document.querySelector(`[data-tab="${targetTab}"]`).click();
    });
});

// Registration Functionality - UPDATED FOR RULES COMPATIBILITY
document.getElementById('createAccount').addEventListener("click", async function (event) {
    event.preventDefault();

    const fullName = document.getElementById('signupName').value;
    const age = document.getElementById('signupAge').value;
    const section = document.getElementById('signupSection').value;
    const email = document.getElementById('signupEmail').value;
    const userName = document.getElementById('signupUsername').value;
    const password = document.getElementById('signupPassword').value;

    // Validation
    if (!fullName || !age || !section || !email || !userName || !password) {
        alert('Please fill in all fields');
        return;
    }

    if (!email.endsWith('@gmail.com')) {
        alert('Please use a valid Gmail address');
        return;
    }

    if (password.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
    }

    if (userName.length < 3) {
        alert('Username must be at least 3 characters long');
        return;
    }

    // Show loading state
    const submitButton = document.getElementById('createAccount');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Creating Account...';
    submitButton.disabled = true;

    try {
        console.log("🔍 Starting registration process...");
        
        // STEP 1: Check username availability (public read)
        console.log("🔍 Checking username availability:", userName);
        const usernameDoc = await getDoc(doc(db, "usernames", userName.toLowerCase()));
        if (usernameDoc.exists()) {
            throw new Error('USERNAME_EXISTS');
        }

        // STEP 2: Check email availability via usernames collection
        console.log("🔍 Checking email availability:", email);
        const emailQuery = query(collection(db, "usernames"), where("email", "==", email));
        const emailSnapshot = await getDocs(emailQuery);
        if (!emailSnapshot.empty) {
            throw new Error('EMAIL_EXISTS');
        }

        // STEP 3: Create Firebase auth account
        console.log("✅ Creating Firebase auth account...");
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        console.log("✅ Firebase auth account created:", user.uid);
        
        // STEP 4: Send verification email
        console.log("✅ Sending verification email...");
        await sendEmailVerification(user);
        console.log("✅ Verification email sent");

        // STEP 5: Save username reservation (authenticated write)
        console.log("✅ Saving username reservation...");
        await setDoc(doc(db, "usernames", userName.toLowerCase()), {
            uid: user.uid,
            userName: userName,
            email: email,
            createdAt: new Date().toISOString()
        });
        console.log("✅ Username reserved");

        // STEP 6: Save user data to Firestore (authenticated write to own document)
        console.log("✅ Saving user data to Firestore...");
        await setDoc(doc(db, "users", user.uid), {
            // User profile information
            fullName: fullName,
            age: parseInt(age),
            section: section,
            email: email,
            userName: userName,
            joinDate: new Date().toISOString(),
            emailVerified: false,
            
            // Gaming Statistics
            totalPlayTime: 0,
            totalSessions: 0,
            gameVisits: {},
            gameSessions: [],
            lastSession: null,
            gamesPlayed: 0,
            
            // Account status
            isActive: true,
            lastLogin: null
        });
        console.log("✅ User data saved to Firestore");

        // STEP 7: Success
        console.log("🎮 Account creation complete!");
        
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        
        alert(`🎮 ACCOUNT CREATED SUCCESSFULLY!\n\n✅ Check your email: ${email}\n📧 Verification link sent\n\n🔒 You MUST verify your email before you can login!`);
        
        // Reset form and switch to login
        document.getElementById('signupForm').reset();
        document.querySelector('[data-tab="login"]').click();
        document.getElementById('loginEmail').value = email;
        
        // Add verification reminder
        addVerificationReminder(email);

    } catch (error) {
        console.error("❌ Registration error:", error);
        
        // Reset button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        
        if (error.message === 'EMAIL_EXISTS') {
            alert('❌ This email is already registered. Please login instead.');
            document.querySelector('[data-tab="login"]').click();
            document.getElementById('loginEmail').value = email;
        } else if (error.message === 'USERNAME_EXISTS') {
            alert('❌ Username already taken. Please choose a different username.');
        } else if (error.code === 'auth/email-already-in-use') {
            alert('❌ This email is already registered. Please login instead.');
            document.querySelector('[data-tab="login"]').click();
            document.getElementById('loginEmail').value = email;
        } else if (error.code === 'permission-denied') {
            alert('❌ DATABASE PERMISSIONS ERROR\n\nPlease try again or contact support.\n\nError: ' + error.message);
            console.error("Firestore permission error details:", error);
        } else if (error.code === 'auth/weak-password') {
            alert('❌ Password is too weak. Please use a stronger password (at least 6 characters).');
        } else if (error.code === 'auth/invalid-email') {
            alert('❌ Invalid email address format.');
        } else {
            alert('❌ Registration failed: ' + error.message + '\n\nError code: ' + (error.code || 'Unknown'));
        }
    }
});

// Login Functionality
document.getElementById('loginButton').addEventListener("click", async function (event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        alert('Please fill in both email and password');
        return;
    }

    let loginEmail = email.trim();
    if (!loginEmail.includes('@')) {
        try {
            const userDoc = await getDoc(doc(db, "usernames", loginEmail.toLowerCase()));
            if (userDoc.exists() && userDoc.data().email) {
                loginEmail = userDoc.data().email;
            } else {
                loginEmail = loginEmail + '@gmail.com';
            }
        } catch {
            loginEmail = loginEmail + '@gmail.com';
        }
    }

    // Show loading state
    const loginButton = document.getElementById('loginButton');
    const originalText = loginButton.textContent;
    loginButton.textContent = 'Logging in...';
    loginButton.disabled = true;

    signInWithEmailAndPassword(auth, loginEmail, password)
        .then(async (userCredential) => {
            const user = userCredential.user;
            console.log("✅ Login successful, checking verification...");
            
            // STRICT VERIFICATION CHECK
            if (!user.emailVerified) {
                console.log("🚫 Email not verified");
                const userAction = confirm(
                    '🚫 EMAIL NOT VERIFIED\n\n' +
                    'You must verify your email before entering the gaming universe.\n\n' +
                    'Email: ' + user.email + '\n\n' +
                    'Click OK to resend verification email.\n\n' +
                    'Check your spam folder if you don\'t see it!'
                );
                
                if (userAction) {
                    await sendEmailVerification(user);
                    alert('✅ Verification email sent! Please check your inbox and verify your email.');
                }
                
                await signOut(auth);
                loginButton.textContent = originalText;
                loginButton.disabled = false;
                return;
            }
            
            // ✅ EMAIL IS VERIFIED - PROCEED TO MAIN PAGE
            console.log("✅ Email verified, proceeding to main page");
            try {
                // Update user data (authenticated write to own document)
                await updateDoc(doc(db, "users", user.uid), {
                    emailVerified: true,
                    lastLogin: new Date().toISOString()
                });
                
                alert("✅ Welcome to Gamers Den!");
                window.location.href = 'index.html';
            } catch (error) {
                console.error("Error updating user data:", error);
                // Still allow login even if Firestore update fails
                alert("✅ Welcome to Gamers Den!");
                window.location.href = 'index.html';
            }
        })
        .catch((error) => {
            console.error("Login error:", error);
            
            loginButton.textContent = originalText;
            loginButton.disabled = false;
            
            if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password') {
                alert('❌ Invalid email or password.');
            } else if (error.code === 'auth/user-not-found') {
                alert('❌ No account found with this email.');
            } else if (error.code === 'auth/too-many-requests') {
                alert('🔒 Too many failed login attempts. Please try again later.');
            } else if (error.code === 'auth/network-request-failed') {
                alert('🌐 Network error. Please check your internet connection.');
            } else {
                alert('❌ Login error: ' + error.message);
            }
        });
});

// Forgot Password Functionality
const forgotPasswordLink = document.getElementById('forgotPassword');
if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', async function (event) {
        event.preventDefault();
        
        const emailInput = document.getElementById('loginEmail');
        let identifier = emailInput ? emailInput.value.trim() : '';
        
        if (!identifier) {
            identifier = prompt('Enter your Gmail address or Username to reset your password:');
            if (!identifier) return;
            identifier = identifier.trim();
        }
        
        let resetEmail = identifier;
        if (!resetEmail.includes('@')) {
            try {
                const userDoc = await getDoc(doc(db, "usernames", resetEmail.toLowerCase()));
                if (userDoc.exists() && userDoc.data().email) {
                    resetEmail = userDoc.data().email;
                } else {
                    resetEmail = resetEmail + '@gmail.com';
                }
            } catch {
                resetEmail = resetEmail + '@gmail.com';
            }
        }
        
        try {
            await sendPasswordResetEmail(auth, resetEmail);
            alert(`📧 Password reset email sent to:\n${resetEmail}\n\nPlease check your inbox and spam folder.`);
        } catch (error) {
            console.error('Password reset error:', error);
            if (error.code === 'auth/user-not-found') {
                alert('❌ No account found with that email or username.');
            } else if (error.code === 'auth/invalid-email') {
                alert('❌ Please enter a valid email address.');
            } else {
                alert('❌ Error: ' + error.message);
            }
        }
    });
}

// Function to add verification reminder
function addVerificationReminder(email) {
    const loginForm = document.getElementById('loginForm');
    
    const existingReminder = document.getElementById('verificationReminder');
    if (existingReminder) {
        existingReminder.remove();
    }
    
    const reminderDiv = document.createElement('div');
    reminderDiv.id = 'verificationReminder';
    reminderDiv.innerHTML = `
        <div style="background: #e3f2fd; border: 2px solid #2196f3; border-radius: 8px; padding: 12px; margin: 10px 0; text-align: left;">
            <p style="margin: 0 0 8px 0; color: #1976d2; font-weight: bold; font-size: 14px;">📧 Verification Required</p>
            <p style="margin: 0 0 8px 0; font-size: 12px;">Verification email sent to <strong>${email}</strong></p>
            <p style="margin: 0; font-size: 11px; color: #666;">
                ✅ Verify your email before logging in<br>
                📨 Check your spam folder if needed<br>
                🔄 Then come back here to login
            </p>
        </div>
    `;
    
    loginForm.insertBefore(reminderDiv, loginForm.querySelector('.auth-switch'));
}

// Real-time username availability check (public read)
document.getElementById('signupUsername').addEventListener('blur', async function() {
    const userName = this.value.trim();
    
    if (!userName || userName.length < 3) {
        clearFieldStyle('signupUsername', 'usernameWarning');
        return;
    }
    
    try {
        console.log("🔍 Checking username availability:", userName);
        const usernameDoc = await getDoc(doc(db, "usernames", userName.toLowerCase()));
        
        if (usernameDoc.exists()) {
            setFieldWarning('signupUsername', 'usernameWarning', '⚠️ Username already taken', '#f44336');
        } else {
            setFieldWarning('signupUsername', 'usernameWarning', '✅ Username is available', '#4caf50');
        }
    } catch (error) {
        console.log("Username check error:", error);
        clearFieldStyle('signupUsername', 'usernameWarning');
        setFieldWarning('signupUsername', 'usernameWarning', '⚠️ Could not check username availability', '#ff9800');
    }
});

// Helper functions for field styling
function setFieldWarning(fieldId, warningId, message, color) {
    const field = document.getElementById(fieldId);
    let warning = document.getElementById(warningId);
    
    field.style.borderColor = color;
    field.style.borderWidth = '2px';
    
    if (!warning) {
        warning = document.createElement('div');
        warning.id = warningId;
        warning.style.color = color;
        warning.style.fontSize = '12px';
        warning.style.marginTop = '5px';
        warning.style.fontWeight = 'bold';
        field.parentNode.appendChild(warning);
    }
    warning.textContent = message;
    warning.style.display = 'block';
}

function clearFieldStyle(fieldId, warningId) {
    const field = document.getElementById(fieldId);
    const warning = document.getElementById(warningId);
    
    field.style.borderColor = '';
    field.style.borderWidth = '';
    
    if (warning) {
        warning.style.display = 'none';
    }
}

// Clear warnings when user starts typing
document.getElementById('signupUsername').addEventListener('input', function() {
    clearFieldStyle('signupUsername', 'usernameWarning');
});

console.log("🔥 Firebase Auth System Loaded Successfully!");