# 🎮 GAMERS DEN

> **BSIT 2-A — 1st Semester A.Y. 2025–2026**  
> A retro-anime pixel gaming hub featuring web-based games, user authentication, game session tracking, and real-time leaderboards.

---

## 📖 Overview

**Gamers Den** is a web-based game portal created for BSIT 2-A. The platform combines a custom retro pixel-art aesthetic with modern web technologies, providing players with an arcade experience directly in the browser.

The entire web platform and its flagship game, **Inscription Reloaded**, were created and engineered by the **Lead Developer**, with frontend layout contributions and game submissions from section classmates.

### 🎮 Playable Games
1. **Inscription Reloaded** *(Developed by Lead Developer)* — An intense wave-survival arcade shooter built in Python/Pygame and compiled to WebAssembly via Pygbag. Features custom weapon switching, enemy wave scaling, boss battles, and a real-time leaderboard system.
2. **CappuciNyaa~** — A charming cat cafe management simulator developed in Godot Engine and exported to WebAssembly.

---

## ✨ Features

- **Pixel-Art Retro UI:** Custom retro theme powered by Google Fonts (*Press Start 2P*, *Silkscreen*) and pixel-shaded components.
- **Theme Switcher:** Toggle between **Light Theme** (Cyan/Neon Green) and **Dark Theme** (Deep Violet/Orange/Red) with state persistence.
- **Dynamic Game Hub:**
  - Interactive banner carousel with direct play links.
  - Live search bar and category filter chips (*Arcade*, *Cafe Simulator*).
- **Authentication System (Firebase):**
  - Sign up with section, age, Gmail, and custom username.
  - Login using **either Gmail address or Username**.
  - Built-in **"Forgot Password?"** recovery feature sending reset links directly to player inboxes.
- **Player Profile & Tracking:**
  - Real-time playtime and session tracker via [JS/gameTracker.js](JS/gameTracker.js).
  - Personalized profile dashboard displaying user statistics and game history.
- **Leaderboards System:**
  - Real-time scoring integration for *Inscription Reloaded*.
  - Records player name, highest wave reached, and timestamp.
  - Dynamic ranking table featuring Gold Crown 👑, Silver, and Bronze badges, plus aggregate stats (Highest Wave, Average Wave, Total Players).

---

## 🛠️ Tech Stack

| Area | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Flexbox, CSS Grid, Custom Properties), JavaScript (ES Modules) |
| **Styling & Fonts** | FontAwesome 6, Google Fonts (*Press Start 2P*, *Silkscreen*) |
| **Backend / Server** | Node.js (v18+), Custom HTTP & WebSocket server (`ws`), HTTP 206 Range streaming |
| **Authentication & Database** | Firebase Authentication, Cloud Firestore |
| **Game Engines & Compilers** | Pygame + Pygbag (WebAssembly/WASI), Godot Engine 4 (WASM + WebGL) |

---

## 🚀 Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18 or higher recommended)
- Modern web browser (Chrome, Edge, Firefox, or Brave)

### Installation & Launch

1. **Clone or open the repository directory:**
   ```bash
   cd GAMERSDEN_BSIT2.A
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the local server:**
   ```bash
   npm start
   ```

4. **Open in your browser:**
   ```
   http://localhost:5500
   ```

### ⚙️ Firebase Setup (Optional)

> 💡 **The arcade games and hub work 100% out of the box** without any Firebase configuration. Both *Inscription Reloaded* and *CappuciNyaa~*, as well as the leaderboard system, are fully playable immediately.

To enable optional cloud user authentication and profile sync:
1. Create a free project at [console.firebase.google.com](https://console.firebase.google.com/).
2. Enable **Authentication** (Email/Password provider) and **Cloud Firestore**.
3. In `JS/firebase-auth.js` and `JS/auth-combined.js`, replace the `firebaseConfig` placeholder values with your project credentials:
   ```javascript
   const firebaseConfig = {
       apiKey: "YOUR_API_KEY",
       authDomain: "your-project-id.firebaseapp.com",
       projectId: "your-project-id",
       storageBucket: "your-project-id.firebasestorage.app",
       messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
       appId: "YOUR_APP_ID"
   };
   ```

---

## 📁 Project Structure

```text
GAMERSDEN_BSIT2.A/
├── index.html              # Homepage with banner carousel & game catalog
├── login.html              # Sign in, Sign up & Password recovery
├── profile.html            # Player dashboard & game stats
├── about.html              # Team information & project vision
├── style.css               # Unified retro pixel-art design system
├── package.json            # Node.js project manifest & scripts
│
├── JS/
│   ├── server.js           # Static HTTP & WebSocket server (with WASM & Range support)
│   ├── main.js             # Game catalog, carousel, search & category filtering
│   ├── auth-combined.js    # Firebase Authentication, login/signup & password reset
│   ├── firebase-auth.js    # Centralized Firebase initialization & state guards
│   ├── gameTracker.js      # Game session and playtime logging
│   ├── profile.js          # Profile data fetching & stats formatting
│   └── websocket-client.js # Client-side WebSocket integration
│
├── gamePages/
│   ├── inscriptionReloaded/
│   │   ├── inscriptionReloadedframe.html # Game frame & navbar wrapper
│   │   ├── main.py                       # Python game source code
│   │   └── build/web/
│   │       ├── index.html                # Pygbag WebAssembly runtime
│   │       ├── leaderboards.html         # Real-time high score board
│   │       └── inscriptionreloaded.apk   # Packed game assets and logic
│   │
│   └── gameTwo/
│       ├── gameTwoFrame.html             # Game frame & navbar wrapper
│       └── CappuciNyaa.html.0.1.0/       # Godot Web export (HTML, WASM, PCK)
│
├── gameBanners/            # Carousel and featured card banners
└── gameIcon/               # Game card thumbnails
```

---

## 👥 Development & Credits

- **Creator & Lead Developer**
  - Designed, architected, and built the complete **Gamers Den** website platform and UI system.
  - Developed and programmed **Inscription Reloaded** from scratch in Python (Pygame + Pygbag WASM).
  - Engineered backend server infrastructure, Firebase Authentication, game session tracking, and the real-time leaderboard data pipeline.
- **Frontend Contributor**
  - Contributed to frontend page layouts and structural CSS styling.
- **Section:** BSIT 2-A (1st Semester, 2025)

---

## 📄 License

This project was built for educational purposes as part of the BSIT curriculum.
