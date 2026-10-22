import pygame
import random
import math
import sys
import asyncio
import json
import time

# Web detection
WEB = False
if sys.platform in ["wasi", "emscripten"]:
    WEB = True
    from platform import window
    window.canvas.style.imageRendering = "pixelated"

pygame.init()

# --- Window setup ---
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Inscription RELOADED")

# --- Font System ---
def load_font(font_path, size):
    """Load a custom font - web compatible"""
    try:
        # For both web and desktop, use the same path structure
        return pygame.font.Font(f"assets/{font_path}", size)
    except Exception as e:
        print(f"[FONT ERROR] Could not load {font_path}: {e}")
        # Fallback to system font
        return pygame.font.Font(None, size)

# Initialize custom fonts
CUSTOM_FONT_REGULAR = None
CUSTOM_FONT_BOLD = None
CUSTOM_FONT_TITLE = None
CUSTOM_FONT_SMALL = None

def initialize_fonts():
    """Initialize custom fonts"""
    global CUSTOM_FONT_REGULAR, CUSTOM_FONT_BOLD, CUSTOM_FONT_TITLE, CUSTOM_FONT_SMALL
    
    try:
        # Use PressStart2P-Regular.ttf for all text - SMALLER SIZES
        CUSTOM_FONT_REGULAR = load_font("PressStart2P-Regular.ttf", 16)  # Regular text (was 24)
        CUSTOM_FONT_BOLD = load_font("PressStart2P-Regular.ttf", 18)     # Slightly larger for emphasis (was 28)
        CUSTOM_FONT_TITLE = load_font("PressStart2P-Regular.ttf", 32)    # Title text (was 48)
        CUSTOM_FONT_SMALL = load_font("PressStart2P-Regular.ttf", 12)    # Small text (was 16)
        print("[FONT] PressStart2P font loaded successfully")
    except Exception as e:
        print(f"[FONT ERROR] Could not load custom fonts: {e}")
        # Fallback to system fonts
        CUSTOM_FONT_REGULAR = pygame.font.Font(None, 16)
        CUSTOM_FONT_BOLD = pygame.font.Font(None, 18)
        CUSTOM_FONT_TITLE = pygame.font.Font(None, 32)
        CUSTOM_FONT_SMALL = pygame.font.Font(None, 12)

# --- Audio Volume Settings ---
AUDIO_VOLUMES = {
    "title_music": 0.5,
    "gameplay_music": 0.4,  
    "boss_music": 0.4,
    "sound_effects": 0.3
}

# --- Ground level constant ---
GROUND_LEVEL = HEIGHT - 50

# --- Debug settings ---
DEBUG_START_WAVE = 1

# --- Game States ---
TITLE_SCREEN = 0
GAME_ACTIVE = 1
LEADERBOARD = 2
NAME_ENTRY = 3
PAUSED = 4
HOW_TO_PLAY = 5

current_game_state = TITLE_SCREEN

# --- Screen Shake Variables ---
screen_shake_intensity = 0
screen_shake_duration = 0
screen_offset_x = 0
screen_offset_y = 0

# --- Leaderboard Data ---
leaderboard_data = []

# --- Name Entry Variables ---
player_name = ""
name_entry_active = True
final_wave = 0
final_score = 0

# --- Background System ---
BACKGROUND_ORIGINAL = None
background_surface = None
current_wave_temperature = 0.0
current_wave_darkness = 0.0
BACKGROUND_MARGIN_BOTTOM = 50

# --- Sound Effects ---
pygame.mixer.init()

def load_sound(name, volume=1.0, sound_type="effect"):
    """Load sound effect safely with volume control - WEB COMPATIBLE"""
    try:
        if WEB:
            path = f"assets/{name}"
            sound = pygame.mixer.Sound(path)
        else:
            import os
            ASSET_DIR = "assets"
            path = os.path.join(ASSET_DIR, name)
            sound = pygame.mixer.Sound(path)
        
        if sound_type == "effect":
            final_volume = volume * AUDIO_VOLUMES["sound_effects"]
        else:
            final_volume = volume
        sound.set_volume(final_volume)
        return sound
    except Exception as e:
        print(f"[SOUND ERROR] Could not load {name}: {e}")
        try:
            silent_sound = pygame.mixer.Sound(buffer=bytes([0] * 44))
            silent_sound.set_volume(0)
            return silent_sound
        except:
            print(f"[SOUND CRITICAL] Could not create placeholder for {name}")
            return None

def play_sound_safe(sound, name="unknown"):
    """Safely play a sound with error handling"""
    if sound is not None:
        try:
            sound.play()
        except Exception as e:
            print(f"[SOUND PLAY ERROR] Could not play {name}: {e}")
    else:
        print(f"[SOUND WARNING] Sound {name} is None, cannot play")

# Load sound effects with volume control
dragon_roar_sound = None
gun_sound = None
gun_empty_sound = None
player_hit_sound = None
player_blast_sound = None

# Music file paths
title_music = None
gameplay_music = None
boss_music = None

# Music state tracking
current_music = None
music_playing = False

# Sound flags
dragon_roar_played = False
boss_music_playing = False

# --- Music Management Functions ---
def play_music(music_type, loop=True):
    """Play background music with proper volume control"""
    global current_music, music_playing
    
    if current_music != music_type:
        stop_music()
    
    try:
        music_file = None
        volume = 0.0
        
        if music_type == "title" and title_music:
            music_file = title_music
            volume = AUDIO_VOLUMES["title_music"]
        elif music_type == "gameplay" and gameplay_music:
            music_file = gameplay_music
            volume = AUDIO_VOLUMES["gameplay_music"]
        elif music_type == "boss" and boss_music:
            music_file = boss_music
            volume = AUDIO_VOLUMES["boss_music"]
        
        if music_file:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(volume)
            if loop:
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.play()
            
            current_music = music_type
            music_playing = True
            print(f"[MUSIC] Now playing: {music_type} at volume {volume}")
            
    except Exception as e:
        print(f"[MUSIC ERROR] Could not play {music_type} music: {e}")

def stop_music():
    """Stop any currently playing music"""
    global current_music, music_playing
    pygame.mixer.music.stop()
    current_music = None
    music_playing = False
    print("[MUSIC] Music stopped")

def update_music_for_state():
    """Update music based on current game state"""
    global current_game_state, wave_system
    
    if current_game_state in [TITLE_SCREEN, LEADERBOARD, HOW_TO_PLAY]:
        if current_music != "title":
            play_music("title")
    elif current_game_state == GAME_ACTIVE:
        # Don't auto-switch to gameplay music if boss music is playing
        if not boss_music_playing and current_music != "gameplay":
            play_music("gameplay")
    elif current_game_state == NAME_ENTRY:
        stop_music()

# --- Background Functions ---
def load_background():
    """Load and scale the background image with subtle dark overlay"""
    global BACKGROUND_ORIGINAL, background_surface
    try:
        bg = load_image("mainGameBackGround.jpg")
        available_height = HEIGHT - BACKGROUND_MARGIN_BOTTOM
        
        bg_ratio = bg.get_width() / bg.get_height()
        target_ratio = WIDTH / available_height
        
        if bg_ratio > target_ratio:
            new_height = available_height
            new_width = int(bg.get_width() * (available_height / bg.get_height()))
        else:
            new_width = WIDTH
            new_height = int(bg.get_height() * (WIDTH / bg.get_width()))
            
        scaled_bg = pygame.transform.scale(bg, (new_width, new_height))
        
        dark_overlay = pygame.Surface((new_width, new_height))
        dark_overlay.fill((0, 0, 0))
        dark_overlay.set_alpha(50)
        
        scaled_bg.blit(dark_overlay, (0, 0))
        
        BACKGROUND_ORIGINAL = pygame.Surface((WIDTH, available_height))
        BACKGROUND_ORIGINAL.blit(scaled_bg, (WIDTH//2 - new_width//2, available_height//2 - new_height//2))
        background_surface = BACKGROUND_ORIGINAL.copy()
        print(f"[BACKGROUND] Loaded with subtle dark overlay (20% reduction)")
    except Exception as e:
        print(f"[BACKGROUND ERROR] Could not load background: {e}")
        available_height = HEIGHT - BACKGROUND_MARGIN_BOTTOM
        BACKGROUND_ORIGINAL = pygame.Surface((WIDTH, available_height))
        BACKGROUND_ORIGINAL.fill((50, 50, 80))
        background_surface = BACKGROUND_ORIGINAL.copy()

def update_background_for_wave(wave_number):
    """Update ang background temperature at darkness based sa wave number """
    global background_surface, current_wave_temperature, current_wave_darkness
    
    cycle_wave = (wave_number - 1) % 10
    progress = cycle_wave / 9.0
    
    current_wave_temperature = progress
    current_wave_darkness = progress * 0.9
    
    background_surface = BACKGROUND_ORIGINAL.copy()
    
    if current_wave_temperature > 0:
        temp_surface = pygame.Surface((WIDTH, HEIGHT - BACKGROUND_MARGIN_BOTTOM))
        temp_color = (
            min(255, int(100 * current_wave_temperature)),
            min(255, int(30 * current_wave_temperature)),
            min(255, int(10 * current_wave_temperature))
        )
        temp_surface.fill(temp_color)
        temp_surface.set_alpha(int(80 * current_wave_temperature))
        background_surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    if current_wave_darkness > 0:
        dark_surface = pygame.Surface((WIDTH, HEIGHT - BACKGROUND_MARGIN_BOTTOM))
        dark_surface.fill((0, 0, 0))
        dark_surface.set_alpha(int(220 * current_wave_darkness))
        background_surface.blit(dark_surface, (0, 0))

def draw_background():
    """Draw the current background with bottom margin"""
    screen.blit(background_surface, (0, 0))
    
    margin_rect = pygame.Rect(0, HEIGHT - BACKGROUND_MARGIN_BOTTOM, WIDTH, BACKGROUND_MARGIN_BOTTOM)
    pygame.draw.rect(screen, (20, 20, 30), margin_rect)
    pygame.draw.line(screen, (50, 50, 70), (0, HEIGHT - BACKGROUND_MARGIN_BOTTOM), 
                    (WIDTH, HEIGHT - BACKGROUND_MARGIN_BOTTOM), 2)

# --- Screen Shake Functions ---
def update_screen_shake():
    global screen_shake_intensity, screen_shake_duration, screen_offset_x, screen_offset_y
    
    if screen_shake_duration > 0:
        screen_shake_duration -= 1
        screen_offset_x = random.randint(-screen_shake_intensity, screen_shake_intensity)
        screen_offset_y = random.randint(-screen_shake_intensity, screen_shake_intensity)
        
        if screen_shake_duration % 5 == 0:
            screen_shake_intensity = max(0, screen_shake_intensity - 1)
    else:
        screen_offset_x = 0
        screen_offset_y = 0
        screen_shake_intensity = 0

def trigger_screen_shake(intensity=10, duration=20):
    global screen_shake_intensity, screen_shake_duration
    screen_shake_intensity = intensity
    screen_shake_duration = duration

# =======================
# 🏆 LOCAL LEADERBOARD SYSTEM WITH POSTMESSAGE
# =======================
class LocalLeaderboard:
    def __init__(self):
        self.scores = []
        self.game_name = "Inscription Reloaded"
        self.leaderboard_window = None
        self.load_scores()
        print("🏆 Local Leaderboard System initialized")
    
    def load_scores(self):
        """Load scores from localStorage"""
        try:
            if WEB:
                import js
                storage_data = js.localStorage.getItem("inscription_leaderboard")
                if storage_data:
                    self.scores = json.loads(storage_data)
                    print(f"📥 Loaded {len(self.scores)} scores from localStorage")
                else:
                    self.scores = []
            else:
                # Desktop fallback - create some dummy scores
                self.scores = [
                    {"name": "HERO", "wave": 15, "timestamp": time.time() - 86400, "date": "2024-01-01 12:00:00"},
                    {"name": "CHAMP", "wave": 12, "timestamp": time.time() - 172800, "date": "2024-01-02 10:30:00"},
                    {"name": "LEGEND", "wave": 8, "timestamp": time.time() - 259200, "date": "2024-01-03 14:20:00"}
                ]
                print("📥 Loaded dummy scores for desktop")
        except Exception as e:
            print(f"❌ Could not load scores: {e}")
            self.scores = []
    
    def save_scores(self):
        """Save scores to localStorage"""
        try:
            if WEB:
                import js
                js.localStorage.setItem("inscription_leaderboard", json.dumps(self.scores))
                print("💾 Saved scores to localStorage")
        except Exception as e:
            print(f"❌ Could not save scores: {e}")
    
    async def submit_score(self, name, wave):
        """Submit score using multiple communication methods"""
        print(f"🏆 SUBMITTING SCORE: '{name}' - Wave {wave}")
        
        # Create score entry
        score_entry = {
            "name": name,
            "wave": wave,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "web_game",
            "game": "Inscription Reloaded"
        }
        
        self.add_score(score_entry)
        
        if WEB:
            await self.broadcast_score_to_leaderboard(score_entry)
    
    def add_score(self, score_entry):
        """Add score to local leaderboard"""
        self.scores.append(score_entry)
        
        # Sort by wave (descending) and keep top 20
        self.scores.sort(key=lambda x: x["wave"], reverse=True)
        self.scores = self.scores[:20]
        
        self.save_scores()
        print(f"✅ Score saved: {score_entry['name']} - Wave {score_entry['wave']}")
    
    async def broadcast_score_to_leaderboard(self, score_entry):
        """Broadcast score to leaderboard.html using multiple methods"""
        try:
            import js
            
            # JavaScript code that will run in the browser
            js_code = f"""
            console.log("📢 Broadcasting score to leaderboard...");
            
            // Method 1: postMessage to parent window
            if (window.parent && window.parent !== window) {{
                window.parent.postMessage({{
                    type: 'NEW_SCORE',
                    game: 'Inscription Reloaded',
                    data: {json.dumps(score_entry)}
                }}, "*");
                console.log("✅ Score sent to parent window");
            }}
            
            // Method 2: postMessage to opener window  
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'NEW_SCORE',
                    game: 'Inscription Reloaded', 
                    data: {json.dumps(score_entry)}
                }}, "*");
                console.log("✅ Score sent to opener window");
            }}
            
            // Method 3: localStorage for cross-tab communication
            localStorage.setItem('inscription_latest_score', JSON.stringify({json.dumps(score_entry)}));
            localStorage.setItem('inscription_leaderboard_updated', Date.now().toString());
            
            // Method 4: Custom event for same-tab communication
            const scoreEvent = new CustomEvent('inscriptionNewScore', {{
                detail: {json.dumps(score_entry)}
            }});
            window.dispatchEvent(scoreEvent);
            
            console.log("🎯 Score broadcast complete!");
            """
            
            await js.eval(js_code)
            print("🌐 Score broadcast to leaderboard systems")
            
        except Exception as e:
            print(f"🌐 Leaderboard broadcast error: {e}")
    
    def get_leaderboard(self, limit=10):
        """Get leaderboard for display"""
        self.load_scores()  # Make sure scores are loaded
        return self.scores[:limit]

# Initialize the local leaderboard system
leaderboard_system = LocalLeaderboard()

# --- Web-Compatible Database Functions ---
def init_database():
    """Initialize web-compatible database"""
    if not WEB:
        print("[DATABASE] Running in desktop mode - no database initialized")
    else:
        print("[DATABASE] Web mode - using localStorage")

def get_leaderboard_data(limit=5):
    """Get leaderboard data from localStorage using the new system"""
    scores = leaderboard_system.get_leaderboard(limit)
    # Convert to the format expected by the existing UI
    formatted_scores = []
    for score in scores:
        formatted_scores.append([score["name"], score["wave"], int(score["wave"] * 100)])
    return formatted_scores

def save_score(name, wave, score):
    """Save score to localStorage using the new system"""
    asyncio.create_task(leaderboard_system.submit_score(name, wave))

# Initialize database on startup
init_database()

# --- Asset loading ---
ASSET_DIR = "assets"

def load_image(name):
    try:
        image = pygame.image.load(f"{ASSET_DIR}/{name}").convert_alpha()
        return image
    except Exception as e:
        print(f"[ERROR] Could not load {name}: {e}")
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        placeholder.fill((255, 0, 255))
        return placeholder

def load_player_frames():
    frames = []
    for fname in ["MAIN RUN - FRAME1.png", "MAIN RUN - FRAME2.png",
                  "MAIN RUN - FRAME3.png", "MAIN-IDLE.png"]:
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        frames.append(cropped_img)
    return frames

def load_frog_frames():
    frames = []
    target_height = 50
    for i in range(1, 9):
        fname = f"frogFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_rocket_frames():
    frames = []
    target_height = 70
    for i in range(1, 13):
        fname = f"rocketEnemyFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_ghoul_frames():
    frames = []
    target_height = 70
    for i in range(1, 8):
        fname = f"Ghoul{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_axolotl_frames():
    frames = []
    target_height = 50
    for i in range(1, 7):
        fname = f"axoltlFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_bat_frames():
    frames = []
    target_height = 30
    for i in range(1, 3):
        fname = f"bat{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_reaper_frames():
    frames = []
    target_height = 60
    for i in range(1, 7):
        fname = f"reaperFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_ally_frames():
    frames = []
    target_height = 40
    for i in range(1, 20):
        fname = f"partnerFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_witch_frames():
    frames = []
    target_height = 60
    for i in range(1, 7):
        fname = f"witchFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_witch_projectile_image():
    img = load_image("witchFrameFire.png")
    img_rect = img.get_bounding_rect()
    cropped_img = img.subsurface(img_rect).copy()
    original_width = cropped_img.get_width()
    original_height = cropped_img.get_height()
    new_w = int(original_width * 0.5)
    new_h = int(original_height * 0.5)
    scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
    return scaled_img

def load_dragon_frames():
    frames = []
    target_height = 150
    for i in range(1, 14):
        fname = f"dragon-{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_fire_boss_frames():
    frames = []
    target_height = 200
    for i in range(1, 6):
        fname = f"FireBossFrame{i}.png"
        img = load_image(fname)
        img_rect = img.get_bounding_rect()
        cropped_img = img.subsurface(img_rect).copy()
        scale_factor = target_height / cropped_img.get_height()
        new_w = int(cropped_img.get_width() * scale_factor)
        new_h = int(cropped_img.get_height() * scale_factor)
        scaled_img = pygame.transform.scale(cropped_img, (new_w, new_h))
        frames.append(scaled_img)
    return frames

def load_ak_image():
    img = load_image("akGun.png")
    return img

def load_pistol_image():
    img = load_image("pistol.png")
    return img

def load_shotgun_image():
    img = load_image("Shotgun.png")
    return img

def load_blast_radius_image():
    img = load_image("blastRadius.png")
    scaled_img = pygame.transform.scale(img, (200, 200))
    return scaled_img

def load_platform_image():
    img = load_image("woodPlatform.png")
    scaled_img = pygame.transform.scale(img, (120, 20))
    return scaled_img

# --- UI Drawing Functions ---
def draw_title_screen():
    bg = load_image("titleScreenBackground.png")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))

    menu_rect = pygame.Rect(WIDTH // 2 - 150, 300, 300, 160)
    menu_surface = pygame.Surface((menu_rect.width, menu_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(menu_surface, (0, 0, 64, 220), menu_surface.get_rect(), border_radius=10)
    pygame.draw.rect(menu_surface, (255, 255, 255, 120), menu_surface.get_rect(), 3, border_radius=10)
    screen.blit(menu_surface, (menu_rect.x, menu_rect.y))

    # Use custom fonts - INCREASED SIZES FOR MENU TEXT
    font = CUSTOM_FONT_BOLD  # Changed from REGULAR to BOLD for better visibility
    white = (255, 255, 255)

    # Increased font sizes for menu items
    start_text = font.render("START", True, white)
    leaderboard_text = font.render("LEADERBOARD", True, white)
    howtoplay_text = font.render("HOW TO PLAY", True, white)

    # Adjust vertical positioning to accommodate larger text
    screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 320))  # Was 315
    screen.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, 370))  # Was 365
    screen.blit(howtoplay_text, (WIDTH // 2 - howtoplay_text.get_width() // 2, 420))  # Was 415

    # Adjust button positions to match new text positioning
    start_button = pygame.Rect(WIDTH // 2 - 150, 315, 300, 45)  # Was 310
    leaderboard_button = pygame.Rect(WIDTH // 2 - 150, 365, 300, 45)  # Was 360
    howtoplay_button = pygame.Rect(WIDTH // 2 - 150, 415, 300, 45)  # Was 410

    return start_button, leaderboard_button, howtoplay_button

def draw_leaderboard():
    bg = load_image("titleScreenBackground.png")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))

    panel_rect = pygame.Rect(WIDTH//2 - 310, 100, 620, 340)
    panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (0, 0, 64, 230), panel_surface.get_rect(), border_radius=15)
    pygame.draw.rect(panel_surface, (255, 255, 255, 140), panel_surface.get_rect(), 3, border_radius=15)
    screen.blit(panel_surface, panel_rect.topleft)

    # Use custom fonts
    title_font = CUSTOM_FONT_TITLE
    label_font = CUSTOM_FONT_BOLD
    entry_font = CUSTOM_FONT_REGULAR
    small_font = CUSTOM_FONT_SMALL
    white = (255, 255, 255)
    yellow = (255, 220, 100)

    leaderboard_title = label_font.render("LEADERBOARD:", True, white)
    screen.blit(leaderboard_title, (WIDTH//2 - leaderboard_title.get_width()//2, 120))

    rank_text = small_font.render("RANK", True, white)
    name_text = small_font.render("NAME", True, white)
    wave_text = small_font.render("TOTAL WAVE", True, white)
    screen.blit(rank_text, (panel_rect.x + 60, 170))
    screen.blit(name_text, (panel_rect.x + 200, 170))
    screen.blit(wave_text, (panel_rect.x + 400, 170))

    crown_image = load_image("topCrown.png")
    if crown_image:
        crown_image = pygame.transform.scale(crown_image, (30, 30))
    else:
        crown_image = None

    leaderboard_data = get_leaderboard_data(limit=5)

    if not leaderboard_data:
        no_scores_text = label_font.render("No scores yet!", True, (200, 200, 200))
        screen.blit(no_scores_text, (WIDTH//2 - no_scores_text.get_width()//2, HEIGHT//2 - 20))
    else:
        start_y = 210
        for i, entry in enumerate(leaderboard_data[:5], start=1):
            name = entry[0]
            wave = entry[1]

            color = yellow if i == 1 else white

            rank_render = entry_font.render(f"{i}", True, color)
            name_render = entry_font.render(f"{name}", True, color)
            wave_render = entry_font.render(f"Wave {wave}", True, color)

            screen.blit(rank_render, (panel_rect.x + 80, start_y))
            screen.blit(name_render, (panel_rect.x + 200, start_y))
            screen.blit(wave_render, (panel_rect.x + 400, start_y))
            
            if i == 1 and crown_image:
                crown_x = panel_rect.x + 200 + name_render.get_width() + 10
                crown_y = start_y + (name_render.get_height() - crown_image.get_height()) // 2
                screen.blit(crown_image, (crown_x, crown_y))
            
            start_y += 45

    back_rect = pygame.Rect(WIDTH//2 - 160, 420, 320, 55)
    back_surface = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(back_surface, (0, 0, 64, 220), back_surface.get_rect(), border_radius=10)
    pygame.draw.rect(back_surface, (255, 255, 255, 140), back_surface.get_rect(), 3, border_radius=10)
    screen.blit(back_surface, back_rect.topleft)

    back_text = label_font.render("BACK TO MENU", True, white)
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, 432))

    return back_rect

def draw_how_to_play():
    bg = load_image("titleScreenBackground.png")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))

    panel = pygame.Surface((700, 400), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 64, 230), panel.get_rect(), border_radius=15)
    pygame.draw.rect(panel, (255, 255, 255, 140), panel.get_rect(), 3, border_radius=15)
    screen.blit(panel, (WIDTH//2 - 350, 80))

    # Use custom fonts
    title_font = CUSTOM_FONT_TITLE
    text_font = CUSTOM_FONT_REGULAR
    white = (255, 255, 255)

    title = title_font.render("HOW TO PLAY", True, white)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

    instructions = [
        "WASD  : Movement",
        "Left Click : Shoot",
        "Right Click : Knockback Attack",
        "Q : Switch Weapon",
        "ESC : Return to Menu"
    ]

    y = 180
    for line in instructions:
        text = text_font.render(line, True, white)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
        y += 40

    back_rect = pygame.Rect(WIDTH//2 - 120, 440, 240, 50)
    back_surface = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(back_surface, (0, 0, 64, 220), back_surface.get_rect(), border_radius=10)
    pygame.draw.rect(back_surface, (255, 255, 255, 140), back_surface.get_rect(), 3, border_radius=10)
    screen.blit(back_surface, back_rect.topleft)

    back_text = text_font.render("BACK TO MENU", True, white)
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, 450))

    return back_rect

def draw_name_entry():
    screen.fill((20, 20, 30))
    
    # Use custom fonts
    title_font = CUSTOM_FONT_TITLE
    score_font = CUSTOM_FONT_BOLD
    prompt_font = CUSTOM_FONT_REGULAR
    name_font = CUSTOM_FONT_REGULAR
    submit_font = CUSTOM_FONT_REGULAR
    instr_font = CUSTOM_FONT_SMALL
    
    title_text = title_font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 80))
    
    wave_text = score_font.render(f"Wave Reached: {final_wave}", True, (255, 255, 255))
    
    screen.blit(wave_text, (WIDTH//2 - wave_text.get_width()//2, 150))
    
    prompt_text = prompt_font.render("Enter your name:", True, (200, 200, 255))
    screen.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, 270))
    
    input_box = pygame.Rect(WIDTH//2 - 200, 320, 400, 60)
    pygame.draw.rect(screen, (50, 50, 70), input_box, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 200), input_box, 3, border_radius=10)
    
    name_surface = name_font.render(player_name, True, (255, 255, 255))
    screen.blit(name_surface, (input_box.x + 20, input_box.y + 15))
    
    if pygame.time.get_ticks() % 1000 < 500:
        cursor_x = input_box.x + 20 + name_surface.get_width() + 2
        pygame.draw.line(screen, (255, 255, 255), (cursor_x, input_box.y + 15), 
                        (cursor_x, input_box.y + input_box.height - 15), 3)
    
    submit_button = pygame.Rect(WIDTH//2 - 100, 410, 200, 50)
    submit_color = (50, 150, 50) if len(player_name) > 0 else (80, 80, 80)
    pygame.draw.rect(screen, submit_color, submit_button, border_radius=10)
    pygame.draw.rect(screen, (100, 255, 100) if len(player_name) > 0 else (120, 120, 120), 
                    submit_button, 3, border_radius=10)
    
    submit_text = submit_font.render("SUBMIT", True, (255, 255, 255))
    screen.blit(submit_text, (submit_button.centerx - submit_text.get_width()//2, 
                            submit_button.centery - submit_text.get_height()//2))
    
    instr_text = instr_font.render("Press ENTER to submit, BACKSPACE to delete", True, (150, 150, 150))
    screen.blit(instr_text, (WIDTH//2 - instr_text.get_width()//2, 480))
    
    return input_box, submit_button

# --- Wave System Classes ---
class WaveSystem:
    def __init__(self):
        self.current_wave = DEBUG_START_WAVE
        self.wave_timer = 0
        self.wave_duration = 1800
        self.bosses_spawned_this_wave = False
        self.fire_boss_count = 0
        self.max_fire_bosses = 2
        self.total_bosses_spawned = 0
        
        self.wave_state = "break"
        self.break_timer = 0
        self.break_duration = 300
        self.enemies_remaining = 0
        self.wave_enemies_spawned = 0
        self.wave_enemies_total = 0
        
        self.boss_minion_timer = 0
        self.boss_minion_delay = 210
        self.boss_minions_spawned = 0
        self.max_boss_minions = 15
        
    def update(self):
        global boss_music_playing, dragon_roar_played
        
        if self.wave_state == "break":
            self.break_timer += 1
            
            if self.break_timer == 1:
                update_background_for_wave(self.current_wave)
            
            if self.break_timer >= self.break_duration:
                self.start_wave()
                
        elif self.wave_state == "active":
            self.wave_timer += 1
            
            if self.is_boss_wave() and self.bosses_spawned_this_wave:
                self.boss_minion_timer += 1
                if (self.boss_minion_timer >= self.boss_minion_delay and 
                    self.boss_minions_spawned < self.max_boss_minions):
                    self.spawn_boss_minions()
                    self.boss_minion_timer = 0
            
            current_enemies = len(ground_enemy_group) + len(flying_enemy_group)
            
            if (self.wave_enemies_spawned >= self.wave_enemies_total and 
                current_enemies == 0):
                self.complete_wave()
                
    def start_wave(self):
        global boss_music_playing, dragon_roar_played
        
        self.wave_state = "active"
        self.break_timer = 0
        self.wave_timer = 0
        self.bosses_spawned_this_wave = False
        self.wave_enemies_spawned = 0
        self.boss_minion_timer = 0
        self.boss_minions_spawned = 0
        
        # Don't play boss music here - wait for actual boss spawn
        if not self.is_boss_wave() and current_music != "gameplay":
            play_music("gameplay")
        
        if self.current_wave > 1:
            bonus_waves = self.current_wave - 1
            gun.ak_ammo = max(gun.ak_ammo, 15 + (bonus_waves * 2))
            gun.shotgun_ammo = max(gun.shotgun_ammo, 8 + (bonus_waves * 1))
            player.health = player.max_health
            print(f"[BALANCE] Starting wave {self.current_wave} with balanced ammo!")
        elif gun.ak_ammo < 10 and self.is_boss_wave():
            gun.ak_ammo = 15
        elif gun.ak_ammo < 5:
            gun.ak_ammo = 10
        
        if self.is_boss_wave():
            self.wave_enemies_total = 1
            self.enemies_remaining = self.wave_enemies_total
            print(f"[WAVE SYSTEM] BOSS WAVE {self.current_wave} started! Boss spawning immediately.")
        else:
            base_enemies = 5 + (self.current_wave * 2)
            self.wave_enemies_total = min(base_enemies, 35)
            self.enemies_remaining = self.wave_enemies_total
            print(f"[WAVE SYSTEM] Wave {self.current_wave} started! Enemies: {self.wave_enemies_total}")
        
    def is_boss_wave(self):
        return self.current_wave >= 10 and self.current_wave % 10 == 0
                
    def complete_wave(self):
        global boss_music_playing
        
        self.wave_state = "break"
        
        just_completed_boss_wave = (self.current_wave >= 10 and self.current_wave % 10 == 0)
        
        if just_completed_boss_wave:
            play_music("gameplay")
            print("[SOUND] Switching back to gameplay music after boss victory")
        
        if self.is_boss_wave():
            player.health = player.max_health
                
            boss_bonus = score_system.add_boss_victory_bonus(self.current_wave)
            ak_reward = 20
            shotgun_reward = 10
            gun.ak_ammo += ak_reward
            gun.shotgun_ammo += shotgun_reward
            
            gun.ak_ammo = min(gun.ak_ammo, 50)
            gun.shotgun_ammo = min(gun.shotgun_ammo, 25)
            
            print(f"[BOSS VICTORY] Player fully healed!")
            print(f"[BOSS BONUS] +{ak_reward} AK ammo! +{shotgun_reward} Shotgun ammo!")
            print(f"[AMMO CAPS] AK: {gun.ak_ammo}/50, Shotgun: {gun.shotgun_ammo}/25")
            
            minions_killed = 0
            for enemy in list(ground_enemy_group) + list(flying_enemy_group):
                if not isinstance(enemy, (FireBoss, DragonBoss)):
                    enemy.kill()
                    minions_killed += 1
            if minions_killed > 0:
                print(f"[BOSS CLEANUP] Despawned {minions_killed} remaining minions")
        else:
            player.heal_between_waves()
                
            wave_bonus = score_system.add_wave_completion_bonus(self.current_wave)
            ak_reward = 8 + min(self.current_wave, 10)
            shotgun_reward = 4 + min(self.current_wave // 2, 5)
            
            gun.ak_ammo += ak_reward
            gun.shotgun_ammo += shotgun_reward
            
            gun.ak_ammo = min(gun.ak_ammo, 50)
            gun.shotgun_ammo = min(gun.shotgun_ammo, 25)
            
            print(f"[WAVE COMPLETION] +{ak_reward} AK ammo! +{shotgun_reward} Shotgun ammo!")
            print(f"[AMMO CAPS] AK: {gun.ak_ammo}/50, Shotgun: {gun.shotgun_ammo}/25")
        
        score_system.update_highest_wave(self.current_wave)
        
        self.current_wave += 1
        self.wave_timer = 0
        
        print(f"[WAVE SYSTEM] Wave {self.current_wave-1} completed! Moving to Wave {self.current_wave}")
        
    def spawn_boss_minions(self):
        if self.boss_minions_spawned >= self.max_boss_minions:
            return
            
        if self.current_wave >= 50:
            max_spawn = 1
        elif self.current_wave >= 30:
            max_spawn = 2
        else:
            max_spawn = 3
            
        minion_count = random.randint(1, max_spawn)
        
        for _ in range(minion_count):
            if self.boss_minions_spawned >= self.max_boss_minions:
                break
                
            if random.random() < 0.7:
                enemy_type = random.choice(["frog", "ghoul", "axolotl"])
                spawn_on_platform = random.random() < 0.3
                
                if spawn_on_platform and platform_group:
                    platform = random.choice(list(platform_group))
                    spawn_x = random.randint(platform.rect.left + 20, platform.rect.right - 20)
                    spawn_y = platform.rect.top
                else:
                    spawn_x = random.randint(100, WIDTH - 100)
                    spawn_y = GROUND_LEVEL
                    
                if enemy_type == "frog":
                    enemy = Frog(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                elif enemy_type == "ghoul":
                    enemy = Ghoul(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                else:
                    enemy = Axolotl(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                    
                ground_enemy_group.add(enemy)
                all_sprites.add(enemy)
            else:
                enemy_type = random.choice(["rocket", "reaper", "bat"])
                spawn_x = random.randint(100, WIDTH - 100)
                spawn_y = random.randint(100, HEIGHT - 200)
                
                if enemy_type == "rocket":
                    enemy = RocketEnemy(spawn_x, spawn_y, player)
                elif enemy_type == "reaper":
                    enemy = Reaper(spawn_x, spawn_y, player)
                else:
                    enemy = Bat(spawn_x, spawn_y)
                    
                flying_enemy_group.add(enemy)
                all_sprites.add(enemy)
            
            self.boss_minions_spawned += 1
            self.wave_enemies_spawned += 1
            self.wave_enemies_total += 1
            self.enemies_remaining += 1
            
        print(f"[BOSS MINIONS] Spawned {minion_count} minions ({self.boss_minions_spawned}/{self.max_boss_minions} total)")
            
    def should_spawn_enemies(self):
        if self.is_boss_wave() and self.bosses_spawned_this_wave:
            return False
        return (self.wave_state == "active" and 
                self.wave_enemies_spawned < self.wave_enemies_total and
                self.enemies_remaining > 0)
        
    def should_spawn_bosses(self):
        if (self.wave_state == "active" and 
            not self.bosses_spawned_this_wave and
            self.current_wave >= 10 and 
            self.current_wave % 10 == 0):
            
            self.bosses_spawned_this_wave = True
            return True
        return False
        
    def get_bosses_to_spawn(self):
        bosses_to_spawn = []
        wave = self.current_wave
        
        if wave == 10 and self.fire_boss_count < self.max_fire_bosses:
            bosses_to_spawn.append(("fire", "left"))
            self.fire_boss_count += 1
            
        elif wave == 20:
            bosses_to_spawn.append(("dragon", "right"))
            
        elif wave >= 30 and wave % 10 == 0:
            if self.fire_boss_count < self.max_fire_bosses:
                side = "left" if self.fire_boss_count == 0 else "right"
                bosses_to_spawn.append(("fire", side))
                self.fire_boss_count += 1
                
            dragon_count = 1 + ((wave - 30) // 10)
            for i in range(dragon_count):
                bosses_to_spawn.append(("dragon", f"position_{i}"))
                
        self.total_bosses_spawned += len(bosses_to_spawn)
        return bosses_to_spawn

class EnemySpawner:
    def __init__(self, wave_system):
        self.wave_system = wave_system
        self.ground_spawn_timer = 0
        self.flying_spawn_timer = 0
        self.bat_spawn_timer = 0
        
        self.base_ground_delay = 90
        self.base_flying_delay = 180
        self.base_bat_delay = 150
        
    def get_spawn_delays(self):
        wave = self.wave_system.current_wave
        speed_factor = max(0.3, 1.0 - (min(wave, 50) * 0.012))
        
        return {
            'ground': max(30, int(self.base_ground_delay * speed_factor)),
            'flying': max(50, int(self.base_flying_delay * speed_factor)),
            'bat': max(70, int(self.base_bat_delay * speed_factor))
        }
        
    def get_enemy_limits(self):
        wave = self.wave_system.current_wave
        ground_limit = min(8 + wave // 2, 20)
        flying_limit = min(4 + wave // 3, 12)
        
        return {
            'ground': ground_limit,
            'flying': flying_limit,
            'total': min(ground_limit + flying_limit, 30)
        }
        
    def get_enemy_types(self):
        wave = self.wave_system.current_wave
        enemy_weights = {
            'ground': {
                'frog': max(0.2, 0.5 - (wave * 0.015)),
                'ghoul': min(0.5, 0.2 + (wave * 0.008)),
                'axolotl': min(0.4, 0.15 + (wave * 0.006)),
                'witch': min(0.4, 0.1 + (wave * 0.01))
            },
            'flying': {
                'rocket': max(0.3, 0.6 - (wave * 0.01)),
                'reaper': min(0.6, 0.2 + (wave * 0.012)),
                'bat': max(0.1, 0.3 - (wave * 0.005))
            }
        }
        return enemy_weights

class ScoreSystem:
    def __init__(self):
        self.score = 0
        self.highest_wave = 1
        
    def update_highest_wave(self, wave):
        if wave > self.highest_wave:
            self.highest_wave = wave
            self.score = self.highest_wave
            
    def add_wave_completion_bonus(self, wave):
        wave_bonus = 10
        self.score += wave_bonus
        return wave_bonus
        
    def add_boss_victory_bonus(self, wave):
        boss_bonus = 50
        self.score += boss_bonus
        return boss_bonus
        
    def get_final_score(self):
        return self.score

# --- Platform class ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=120, height=20):
        super().__init__()
        self.original_image = load_platform_image()
        self.image = pygame.transform.scale(self.original_image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = load_player_frames()
        self.current_frame = 3
        self.image = self.frames[self.current_frame]
        
        img_rect = self.image.get_bounding_rect()
        self.image = self.image.subsurface(img_rect).copy()
        
        self.rect = self.image.get_rect(midbottom=(x, GROUND_LEVEL))
        self.mask = pygame.mask.from_surface(self.image)

        self.speed = 5
        self.vel_y = 0
        self.gravity = 0.8
        self.on_ground = False
        self.on_platform = False
        self.current_platform = None
        self.facing_right = True
        self.anim_timer = 0
        self.anim_delay = 6

        self.max_health = 25 
        self.health = self.max_health
        self.invincible_timer = 0
        self.god_mode = False

        self.wave_heal_amount = 5
        self.min_health_for_heal = 30

    def update_keyboard(self, keys, platforms):
        dx = 0
        
        if keys[pygame.K_a]:
            dx = -self.speed
            self.facing_right = False
        if keys[pygame.K_d]:
            dx = self.speed
            self.facing_right = True

        self.rect.x += dx

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (self.on_ground or self.on_platform):
            self.vel_y = -15
            self.on_ground = False
            self.on_platform = False
            self.current_platform = None

        self.update_physics(platforms)
        self.update_animation(dx)

    def update_physics(self, platforms):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        self.on_ground = False
        self.on_platform = False
        self.current_platform = None

        if self.vel_y >= 0:
            for platform in platforms:
                if (self.rect.bottom >= platform.rect.top and 
                    self.rect.bottom <= platform.rect.top + 20 and
                    self.rect.right > platform.rect.left + 5 and
                    self.rect.left < platform.rect.right - 5):
                    
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_platform = True
                    self.current_platform = platform
                    break

        if not self.on_platform and self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def update_animation(self, dx):
        if dx != 0:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 3
        else:
            self.current_frame = 3

        frame = self.frames[self.current_frame]
        img_rect = frame.get_bounding_rect()
        cropped_frame = frame.subsurface(img_rect).copy()
        
        if not self.facing_right:
            cropped_frame = pygame.transform.flip(cropped_frame, True, False)

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = cropped_frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

        if self.god_mode:
            self.image.set_alpha(150 if pygame.time.get_ticks() % 1000 < 500 else 255)
        elif self.invincible_timer > 0:
            self.invincible_timer -= 1
            self.image.set_alpha(150 if self.invincible_timer % 30 < 15 else 255)
        else:
            self.image.set_alpha(255)

    def heal_between_waves(self):
        if self.health < self.min_health_for_heal:
            self.health = min(self.max_health, self.health + self.wave_heal_amount)
            print(f"[HEAL] Player healed to {self.health} HP")

    def toggle_god_mode(self):
        self.god_mode = not self.god_mode
        print(f"[GOD MODE] {'ON' if self.god_mode else 'OFF'}")

# --- Gun Class ---
class Gun(pygame.sprite.Sprite):
    def __init__(self, player, bullet_group):
        super().__init__()
        self.player = player
        self.bullet_group = bullet_group
        self.radius = 60
        
        self.ak_image = self.load_scaled_gun(load_ak_image(), 0.09)
        self.pistol_image = self.load_scaled_gun(load_pistol_image(), 0.07)
        self.shotgun_image = self.load_scaled_gun(load_shotgun_image(), 0.12)
        
        self.current_gun = "ak"
        self.original_image = self.ak_image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=player.rect.center)

        self.cooldown = 0
        self.switch_cooldown = 0
        
        self.ak_ammo = 25
        self.shotgun_ammo = 12
        self.pistol_unlimited = True

    def load_scaled_gun(self, original, scale):
        w, h = original.get_size()
        new_size = (int(w * scale), int(h * scale))
        return pygame.transform.scale(original, new_size)

    def switch_weapon(self):
        if self.switch_cooldown == 0:
            if self.current_gun == "pistol":
                print("[SWITCH] Switching from unlimited pistol!")
            elif self.current_gun == "ak" and self.ak_ammo < 10:
                print("[LOW AMMO] AK running low, consider using pistol!")
            elif self.current_gun == "shotgun" and self.shotgun_ammo < 5:
                print("[LOW AMMO] Shotgun running low, consider using pistol!")
            
            if self.current_gun == "ak":
                self.current_gun = "pistol"
                self.original_image = self.pistol_image
            elif self.current_gun == "pistol":
                self.current_gun = "shotgun"
                self.original_image = self.shotgun_image
            else:
                self.current_gun = "ak"
                self.original_image = self.ak_image
            self.switch_cooldown = 20

    def update_keyboard(self):
        if knife.active:
            return

        if self.switch_cooldown > 0:
            self.switch_cooldown -= 1

        px, py = self.player.rect.center
        mx, my = pygame.mouse.get_pos()
        dx, dy = mx - px, my - py
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        self.update_gun_position(px, py, angle_rad, angle_deg)
        
        barrel_length = self.original_image.get_width() * 0.5
        barrel_tip_x = self.rect.centerx + math.cos(angle_rad) * barrel_length
        barrel_tip_y = self.rect.centery + math.sin(angle_rad) * barrel_length

        if pygame.mouse.get_pressed()[0] and self.cooldown == 0:
            self.shoot(barrel_tip_x, barrel_tip_y, angle_rad)

        if self.cooldown > 0:
            self.cooldown -= 1

    def update_gun_position(self, px, py, angle_rad, angle_deg):
        offset_x = math.cos(angle_rad) * self.radius
        offset_y = math.sin(angle_rad) * self.radius
        gun_x = px + offset_x
        gun_y = py + offset_y

        rotated_image = pygame.transform.rotate(self.original_image, -angle_deg)
        
        if math.cos(angle_rad) < 0:
            rotated_image = pygame.transform.flip(rotated_image, False, True)

        self.image = rotated_image
        self.rect = self.image.get_rect(center=(gun_x, gun_y))

    def shoot(self, barrel_tip_x, barrel_tip_y, angle_rad):
        if wave_system.is_boss_wave():
            boss_damage = 1 + (wave_system.current_wave // 20)
            damage = boss_damage
        else:
            wave_bonus_damage = (wave_system.current_wave - 1) // 10
            damage = 1 + wave_bonus_damage
        
        if self.current_gun == "ak" and self.ak_ammo > 0:
            bullet = Bullet((barrel_tip_x, barrel_tip_y), angle_rad, speed=12, is_pistol=False, damage=damage)
            self.bullet_group.add(bullet)
            self.cooldown = 10
            self.ak_ammo -= 1
            play_sound_safe(gun_sound, "gun_sound")
            print(f"[AK SHOT] Ammo: {self.ak_ammo}, Damage: {damage}")
        
        elif self.current_gun == "pistol":
            bullet = Bullet((barrel_tip_x, barrel_tip_y), angle_rad, speed=14, is_pistol=True, damage=damage)
            self.bullet_group.add(bullet)
            self.cooldown = 20
            play_sound_safe(gun_sound, "gun_sound")
            print(f"[PISTOL SHOT] Damage: {damage}")
        
        elif self.current_gun == "shotgun" and self.shotgun_ammo > 0:
            spread_angle = 0.2
            angles = [
                angle_rad - spread_angle,
                angle_rad,
                angle_rad + spread_angle
            ]
            
            for angle in angles:
                bullet = Bullet((barrel_tip_x, barrel_tip_y), angle, speed=10, is_pistol=False, is_shotgun=True, damage=damage)
                self.bullet_group.add(bullet)
            
            self.cooldown = 30
            self.shotgun_ammo -= 1
            play_sound_safe(gun_sound, "gun_sound")
            print(f"[SHOTGUN SHOT] Ammo: {self.shotgun_ammo}, Damage: {damage}")
        
        else:
            play_sound_safe(gun_empty_sound, "gun_empty_sound")
            print(f"[EMPTY GUN] No ammo for {self.current_gun}!")

# --- Knife Class ---
class Knife(pygame.sprite.Sprite):
    def __init__(self, player, ground_enemy_group, flying_enemy_group):
        super().__init__()
        self.player = player
        self.ground_enemy_group = ground_enemy_group
        self.flying_enemy_group = flying_enemy_group
        self.radius = 80
        self.duration = 40
        self.timer = 0
        self.active = False
        self.cooldown = 0
        self.cooldown_max = 90
        self.hit_enemies = set()
        
        self.original_image = load_blast_radius_image()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=player.rect.center)
        self.mask = self.create_circular_mask()

    def create_circular_mask(self):
        mask_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask_surface, (255, 255, 255), (self.radius, self.radius), self.radius)
        return pygame.mask.from_surface(mask_surface)

    def update_keyboard(self):
        if self.cooldown > 0:
            self.cooldown -= 1
            
        if pygame.mouse.get_pressed()[2] and not self.active and self.cooldown == 0:
            self.activate_knife()

        self.update_knife_state()

    def activate_knife(self):
        self.active = True
        self.timer = self.duration
        self.cooldown = self.cooldown_max
        self.hit_enemies.clear()
        
        play_sound_safe(player_blast_sound, "player_blast_sound")

    def update_knife_state(self):
        if self.active:
            self.rect.center = self.player.rect.center
            
            pulse = math.sin(pygame.time.get_ticks() * 0.1) * 0.2 + 0.8
            scaled_width = int(self.original_image.get_width() * pulse)
            scaled_height = int(self.original_image.get_height() * pulse)
            self.image = pygame.transform.scale(self.original_image, (scaled_width, scaled_height))
            self.rect = self.image.get_rect(center=self.player.rect.center)

            for enemy in self.ground_enemy_group:
                if enemy not in self.hit_enemies:
                    distance = math.hypot(enemy.rect.centerx - self.player.rect.centerx, 
                                         enemy.rect.centery - self.player.rect.centery)
                    if distance <= self.radius:
                        self.hit_enemies.add(enemy)
                        self.apply_knockback(enemy, distance)
                        print(f"[KNIFE KNOCKBACK] {enemy.__class__.__name__} launched!")
            
            for enemy in self.flying_enemy_group:
                if enemy not in self.hit_enemies:
                    distance = math.hypot(enemy.rect.centerx - self.player.rect.centerx, 
                                         enemy.rect.centery - self.player.rect.centery)
                    if distance <= self.radius:
                        self.hit_enemies.add(enemy)
                        self.apply_knockback(enemy, distance)
                        print(f"[KNIFE KNOCKBACK] {enemy.__class__.__name__} launched!")
                        
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
                self.image.set_alpha(0)

    def apply_knockback(self, enemy, distance):
        dx = enemy.rect.centerx - self.player.rect.centerx
        dy = enemy.rect.centery - self.player.rect.centery
        if dx != 0 or dy != 0:
            norm_x, norm_y = dx / distance, dy / distance
            knockback_strength = 40
            
            enemy.rect.x += int(norm_x * knockback_strength)
            enemy.rect.y += int(norm_y * knockback_strength)
            
            if hasattr(enemy, 'on_platform') and enemy.on_platform:
                enemy.on_platform = False
                if hasattr(enemy, 'current_platform'):
                    enemy.current_platform = None
                if hasattr(enemy, 'vel_y'):
                    enemy.vel_y = -12
            elif hasattr(enemy, 'vel_y'):
                enemy.vel_y = -15
            
            if hasattr(enemy, 'state') and enemy.state == "attack":
                if hasattr(enemy, 'reset_to_hover'):
                    enemy.reset_to_hover()

# --- Bullet class ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, angle, speed=12, is_pistol=False, is_shotgun=False, damage=1):
        super().__init__()
        if is_pistol:
            self.image = pygame.Surface((6, 3), pygame.SRCALPHA)
            color = (200, 200, 255)
            pygame.draw.rect(self.image, color, (0, 0, 6, 3))
        elif is_shotgun:
            self.image = pygame.Surface((10, 6), pygame.SRCALPHA)
            color = (255, 165, 0)
            pygame.draw.ellipse(self.image, color, (0, 0, 10, 6))
        else:
            self.image = pygame.Surface((8, 4), pygame.SRCALPHA)
            color = (255, 220, 100)
            pygame.draw.rect(self.image, color, (0, 0, 8, 4))
        
        self.image = pygame.transform.rotate(self.image, -math.degrees(angle))
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.lifetime = 90
        self.is_pistol = is_pistol
        self.is_shotgun = is_shotgun
        self.damage = damage

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.lifetime -= 1
        if self.lifetime <= 0 or not screen.get_rect().colliderect(self.rect):
            self.kill()

# --- Bat Enemy ---
class Bat(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = load_bat_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.speed_x = random.choice([-2, -1, 1, 2])
        self.speed_y = random.choice([-2, -1, 1, 2])
        self.anim_timer = 0
        self.anim_delay = 10
        self.health = 1
        self.float_timer = 0
        self.float_speed = 0.5
        self.damage = 1
        self.contact_cooldown = 0

    def update(self, player=None):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        self.float_timer += 1
        self.rect.y += math.sin(self.float_timer * 0.1) * self.float_speed
        
        if self.rect.left < 0:
            self.rect.left = 0
            self.speed_x = abs(self.speed_x)
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.speed_x = -abs(self.speed_x)
            
        if self.rect.top < 50:
            self.rect.top = 50
            self.speed_y = abs(self.speed_y)
        elif self.rect.bottom > HEIGHT - 100:
            self.rect.bottom = HEIGHT - 100
            self.speed_y = -abs(self.speed_y)
        
        if random.random() < 0.01:
            self.speed_x = random.choice([-2, -1, 1, 2])
            self.speed_y = random.choice([-2, -1, 1, 2])
        
        if self.speed_x > 0:
            self.image = pygame.transform.flip(self.frames[self.current_frame], True, False)
        else:
            self.image = self.frames[self.current_frame]
        
        self.anim_timer += 1
        if self.anim_timer >= self.anim_delay:
            self.anim_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1
            
        self.mask = pygame.mask.from_surface(self.image)

# --- GROUND ENEMIES ---

class Frog(pygame.sprite.Sprite):
    def __init__(self, x, y, spawn_on_ground=True):
        super().__init__()
        self.frames = load_frog_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        if spawn_on_ground:
            self.rect = self.image.get_rect(midbottom=(x, GROUND_LEVEL))
        else:
            self.rect = self.image.get_rect(midbottom=(x, y))
            
        self.mask = pygame.mask.from_surface(self.image)
        
        self.state = "walk"
        self.anim_timer = 0
        self.anim_delay = 8
        self.frame_counter = 0
        self.attack_cooldown = 0
        self.speed = 2
        self.vel_y = 0
        self.gravity = 0.6
        self.on_ground = spawn_on_ground
        self.on_platform = not spawn_on_ground
        self.current_platform = None
        self.facing_right = False
        self.health = 3
        self.idle_timer = 0
        self.idle_duration = 60
        self.last_player_x = 0
        self.spawn_y = y if not spawn_on_ground else GROUND_LEVEL

    def update(self, player):
        if player.rect.centerx > self.rect.centerx:
            self.facing_right = True
        else:
            self.facing_right = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == "walk":
            self.walk_behavior(player)
        elif self.state == "attack":
            self.attack_behavior(player)
        elif self.state == "idle":
            self.idle_behavior(player)

        if not self.on_platform:
            self.vel_y += self.gravity
            self.rect.y += self.vel_y

        was_on_platform = self.on_platform
        self.on_platform = False
        self.current_platform = None

        if self.vel_y >= 0:
            for platform in platform_group:
                if (self.rect.bottom >= platform.rect.top and 
                    self.rect.bottom <= platform.rect.top + 20 and
                    self.rect.right > platform.rect.left + 5 and 
                    self.rect.left < platform.rect.right - 5):
                    
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_platform = True
                    self.current_platform = platform
                    break

        if not self.on_platform and self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.on_platform and self.current_platform:
            if (self.rect.bottom != self.current_platform.rect.top or
                self.rect.right <= self.current_platform.rect.left or 
                self.rect.left >= self.current_platform.rect.right):
                self.on_platform = False
                self.current_platform = None
                self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
            self.facing_right = True
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.facing_right = False

        self.update_animation()

    def walk_behavior(self, player):
        player_on_platform = player.on_platform
        player_above = player.rect.bottom < self.rect.top
        
        if player_on_platform and player_above and abs(player.rect.centerx - self.rect.centerx) < 150:
            self.state = "idle"
            self.idle_timer = 0
            return

        if self.facing_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        if abs(player.rect.centerx - self.rect.centerx) < 120 and self.attack_cooldown == 0:
            self.state = "attack"
            self.frame_counter = 4

    def idle_behavior(self, player):
        self.idle_timer += 1
        
        player_moved = abs(player.rect.centerx - self.last_player_x) > 50
        player_still_above = player.on_platform and player.rect.bottom < self.rect.top
        player_close = abs(player.rect.centerx - self.rect.centerx) < 150
        
        if self.idle_timer >= self.idle_duration or not player_still_above or not player_close or player_moved:
            self.state = "walk"
            self.idle_timer = 0
        
        self.last_player_x = player.rect.centerx

    def attack_behavior(self, player):
        self.frame_counter += 1

        if self.frame_counter == 5:
            self.current_frame = 4
        elif self.frame_counter == 6:
            if self.on_ground:
                self.vel_y = -10
            self.current_frame = 5
        elif self.frame_counter == 7:
            lunge = 6 if self.facing_right else -6
            self.rect.x += lunge
            self.current_frame = 6

            if player.invincible_timer == 0 and not player.god_mode:
                if pygame.sprite.collide_mask(self, player):
                    player.health -= 1
                    player.invincible_timer = 180
                    trigger_screen_shake(8, 15)
                    play_sound_safe(player_hit_sound, "player_hit_sound")
                    print(f"[HIT] Player health: {player.health}")
        elif self.frame_counter == 8:
            self.current_frame = 7
        elif self.frame_counter > 8:
            self.state = "walk"
            self.frame_counter = 0
            self.attack_cooldown = random.randint(180, 300)

    def update_animation(self):
        if self.state == "walk":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 4
        elif self.state == "idle":
            self.current_frame = 0
        elif self.state == "attack":
            pass

        frame = self.frames[self.current_frame]
        
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

class Ghoul(pygame.sprite.Sprite):
    def __init__(self, x, y, spawn_on_ground=True):
        super().__init__()
        self.frames = load_ghoul_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        if spawn_on_ground:
            self.rect = self.image.get_rect(midbottom=(x, GROUND_LEVEL))
        else:
            self.rect = self.image.get_rect(midbottom=(x, y))
            
        self.mask = pygame.mask.from_surface(self.image)
        
        self.state = "walk"
        self.anim_timer = 0
        self.anim_delay = 10
        self.frame_counter = 0
        self.attack_cooldown = 0
        self.speed = 1.5
        self.vel_y = 0
        self.gravity = 0.6
        self.on_ground = spawn_on_ground
        self.on_platform = not spawn_on_ground
        self.current_platform = None
        self.facing_right = False
        self.health = 4
        self.idle_timer = 0
        self.idle_duration = 80
        self.last_player_x = 0
        self.spawn_y = y if not spawn_on_ground else GROUND_LEVEL

    def update(self, player):
        if player.rect.centerx > self.rect.centerx:
            self.facing_right = True
        else:
            self.facing_right = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == "walk":
            self.walk_behavior(player)
        elif self.state == "attack":
            self.attack_behavior(player)
        elif self.state == "idle":
            self.idle_behavior(player)

        if not self.on_platform:
            self.vel_y += self.gravity
            self.rect.y += self.vel_y

        was_on_platform = self.on_platform
        self.on_platform = False
        self.current_platform = None

        if self.vel_y >= 0:
            for platform in platform_group:
                if (self.rect.bottom >= platform.rect.top and 
                    self.rect.bottom <= platform.rect.top + 20 and
                    self.rect.right > platform.rect.left + 5 and 
                    self.rect.left < platform.rect.right - 5):
                    
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_platform = True
                    self.current_platform = platform
                    break

        if not self.on_platform and self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.on_platform and self.current_platform:
            if (self.rect.bottom != self.current_platform.rect.top or
                self.rect.right <= self.current_platform.rect.left or 
                self.rect.left >= self.current_platform.rect.right):
                self.on_platform = False
                self.current_platform = None
                self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
            self.facing_right = True
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.facing_right = False

        self.update_animation()

    def walk_behavior(self, player):
        player_on_platform = player.on_platform
        player_above = player.rect.bottom < self.rect.top
        
        if player_on_platform and player_above and abs(player.rect.centerx - self.rect.centerx) < 150:
            self.state = "idle"
            self.idle_timer = 0
            return

        if self.facing_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        if abs(player.rect.centerx - self.rect.centerx) < 100 and self.attack_cooldown == 0:
            self.state = "attack"
            self.frame_counter = 4

    def idle_behavior(self, player):
        self.idle_timer += 1
        
        player_moved = abs(player.rect.centerx - self.last_player_x) > 50
        player_still_above = player.on_platform and player.rect.bottom < self.rect.top
        player_close = abs(player.rect.centerx - self.rect.centerx) < 150
        
        if self.idle_timer >= self.idle_duration or not player_still_above or not player_close or player_moved:
            self.state = "walk"
            self.idle_timer = 0
        
        self.last_player_x = player.rect.centerx

    def attack_behavior(self, player):
        self.frame_counter += 1

        if self.frame_counter == 1:
            self.current_frame = 4
        elif self.frame_counter == 3:
            self.current_frame = 5
        elif self.frame_counter == 5:
            self.current_frame = 6
            if player.invincible_timer == 0 and not player.god_mode:
                if pygame.sprite.collide_mask(self, player):
                    player.health -= 1
                    player.invincible_timer = 180
                    trigger_screen_shake(8, 15)
                    play_sound_safe(player_hit_sound, "player_hit_sound")
                    print(f"[GHOUL HIT] Player health: {player.health}")
        elif self.frame_counter == 7:
            self.current_frame = 6
        elif self.frame_counter > 8:
            self.state = "walk"
            self.frame_counter = 0
            self.attack_cooldown = random.randint(200, 350)

    def update_animation(self):
        if self.state == "walk":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 4
        elif self.state == "idle":
            self.current_frame = 0
        elif self.state == "attack":
            pass

        frame = self.frames[self.current_frame]
        
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        else:
            frame = frame

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

class Axolotl(pygame.sprite.Sprite):
    def __init__(self, x, y, spawn_on_ground=True):
        super().__init__()
        self.frames = load_axolotl_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        if spawn_on_ground:
            self.rect = self.image.get_rect(midbottom=(x, GROUND_LEVEL))
        else:
            self.rect = self.image.get_rect(midbottom=(x, y))
            
        self.mask = pygame.mask.from_surface(self.image)
        
        self.state = "idle"
        self.anim_timer = 0
        self.anim_delay = 10
        self.frame_counter = 0
        self.attack_cooldown = 0
        self.speed = 1.2
        self.vel_y = 0
        self.gravity = 0.6
        self.on_ground = spawn_on_ground
        self.on_platform = not spawn_on_ground
        self.current_platform = None
        self.facing_right = False
        self.health = 3
        self.idle_timer = 0
        self.idle_duration = 90
        self.last_player_x = 0
        self.spawn_y = y if not spawn_on_ground else GROUND_LEVEL

    def update(self, player):
        if player.rect.centerx > self.rect.centerx:
            self.facing_right = True
        else:
            self.facing_right = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == "idle":
            self.idle_behavior(player)
        elif self.state == "attack":
            self.attack_behavior(player)
        elif self.state == "recovery":
            self.recovery_behavior(player)

        if not self.on_platform:
            self.vel_y += self.gravity
            self.rect.y += self.vel_y

        was_on_platform = self.on_platform
        self.on_platform = False
        self.current_platform = None

        if self.vel_y >= 0:
            for platform in platform_group:
                if (self.rect.bottom >= platform.rect.top and 
                    self.rect.bottom <= platform.rect.top + 20 and
                    self.rect.right > platform.rect.left + 5 and 
                    self.rect.left < platform.rect.right - 5):
                    
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_platform = True
                    self.current_platform = platform
                    break

        if not self.on_platform and self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.on_platform and self.current_platform:
            if (self.rect.bottom != self.current_platform.rect.top or
                self.rect.right <= self.current_platform.rect.left or 
                self.rect.left >= self.current_platform.rect.right):
                self.on_platform = False
                self.current_platform = None
                self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
            self.facing_right = True
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.facing_right = False

        self.update_animation()

    def idle_behavior(self, player):
        self.current_frame = 0
        
        player_on_platform = player.on_platform
        player_above = player.rect.bottom < self.rect.top
        
        if player_on_platform and player_above and abs(player.rect.centerx - self.rect.centerx) < 150:
            self.idle_timer += 1
            if self.idle_timer >= self.idle_duration:
                self.idle_timer = 0
                return

        if self.facing_right:
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        if abs(player.rect.centerx - self.rect.centerx) < 100 and self.attack_cooldown == 0:
            self.state = "attack"
            self.frame_counter = 0
            self.current_frame = 1

    def attack_behavior(self, player):
        self.frame_counter += 1

        if self.frame_counter == 1:
            self.current_frame = 1
        elif self.frame_counter == 5:
            self.current_frame = 2
        elif self.frame_counter == 10:
            self.current_frame = 3
        elif self.frame_counter == 15:
            self.current_frame = 4
            if player.invincible_timer == 0 and not player.god_mode:
                if pygame.sprite.collide_mask(self, player):
                    player.health -= 1
                    player.invincible_timer = 180
                    trigger_screen_shake(8, 15)
                    play_sound_safe(player_hit_sound, "player_hit_sound")
                    print(f"[AXOLOTL HIT] Player health: {player.health}")
        elif self.frame_counter == 20:
            self.current_frame = 5
        elif self.frame_counter == 25:
            self.current_frame = 0
        elif self.frame_counter > 30:
            self.state = "recovery"
            self.frame_counter = 0
            self.attack_cooldown = random.randint(200, 350)

    def recovery_behavior(self, player):
        self.frame_counter += 1
        if self.frame_counter >= 30:
            self.state = "idle"
            self.frame_counter = 0

    def update_animation(self):
        frame = self.frames[self.current_frame]
        
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

class Witch(pygame.sprite.Sprite):
    def __init__(self, x, y, player, spawn_on_ground=True):
        super().__init__()
        self.frames = load_witch_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        if spawn_on_ground:
            self.rect = self.image.get_rect(midbottom=(x, GROUND_LEVEL))
        else:
            self.rect = self.image.get_rect(midbottom=(x, y))
            
        self.mask = pygame.mask.from_surface(self.image)
        
        self.player = player
        self.state = "idle"
        self.anim_timer = 0
        self.anim_delay = 10
        self.attack_cooldown = 0
        self.attack_range = 300
        self.buildup_timer = 0
        self.buildup_duration = 60
        self.recovery_timer = 0
        self.recovery_duration = 30
        self.speed = 1.0
        self.vel_y = 0
        self.gravity = 0.6
        self.on_ground = spawn_on_ground
        self.on_platform = not spawn_on_ground
        self.current_platform = None
        self.health = 4
        self.facing_right = False
        self.spawn_y = y if not spawn_on_ground else GROUND_LEVEL

    def update(self, player):
        self.player = player
        
        if player.rect.centerx > self.rect.centerx:
            self.facing_right = True
        else:
            self.facing_right = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == "idle":
            self.idle_behavior(player)
        elif self.state == "buildup":
            self.buildup_behavior()
        elif self.state == "attack":
            self.attack_behavior()
        elif self.state == "recovery":
            self.recovery_behavior()

        if not self.on_platform:
            self.vel_y += self.gravity
            self.rect.y += self.vel_y

        was_on_platform = self.on_platform
        self.on_platform = False
        self.current_platform = None

        if self.vel_y >= 0:
            for platform in platform_group:
                if (self.rect.bottom >= platform.rect.top and 
                    self.rect.bottom <= platform.rect.top + 20 and
                    self.rect.right > platform.rect.left + 5 and 
                    self.rect.left < platform.rect.right - 5):
                    
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_platform = True
                    self.current_platform = platform
                    break

        if not self.on_platform and self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.on_platform and self.current_platform:
            if (self.rect.bottom != self.current_platform.rect.top or
                self.rect.right <= self.current_platform.rect.left or 
                self.rect.left >= self.current_platform.rect.right):
                self.on_platform = False
                self.current_platform = None
                self.vel_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
            self.facing_right = True
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.facing_right = False

        self.update_animation()

    def idle_behavior(self, player):
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        
        if player.on_platform and player.rect.bottom < self.rect.top and distance_to_player < 150:
            pass
        else:
            if self.facing_right:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed

        if distance_to_player < self.attack_range and self.attack_cooldown == 0:
            self.state = "buildup"
            self.buildup_timer = 0
            self.current_frame = 0

    def buildup_behavior(self):
        self.buildup_timer += 1
        
        buildup_progress = min(self.buildup_timer / self.buildup_duration, 1.0)
        self.current_frame = int(buildup_progress * 4)
        
        if self.buildup_timer >= self.buildup_duration:
            self.state = "attack"
            self.current_frame = 4
            
            projectile = WitchProjectile(
                self.rect.center, 
                self.player.rect.center,
                speed=6
            )
            all_sprites.add(projectile)
            enemy_projectile_group.add(projectile)

    def attack_behavior(self):
        self.anim_timer += 1
        if self.anim_timer >= 15:
            self.current_frame = 5
            self.state = "recovery"
            self.recovery_timer = 0
            self.anim_timer = 0
            
            if pygame.sprite.collide_mask(self, self.player) and self.player.invincible_timer == 0 and not self.player.god_mode:
                self.player.health -= 1
                self.player.invincible_timer = 180
                trigger_screen_shake(8, 15)
                play_sound_safe(player_hit_sound, "player_hit_sound")
                print(f"[WITCH MELEE HIT] Player health: {self.player.health}")

    def recovery_behavior(self):
        self.recovery_timer += 1
        self.current_frame = 5
        
        if self.recovery_timer >= self.recovery_duration:
            self.state = "idle"
            self.attack_cooldown = 120
            self.current_frame = 0

    def update_animation(self):
        frame = self.frames[self.current_frame]
        
        if self.facing_right:
            frame = pygame.transform.flip(frame, True, False)

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

class WitchProjectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, speed=6):
        super().__init__()
        self.image = load_witch_projectile_image()
        self.rect = self.image.get_rect(center=start_pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        distance = math.hypot(dx, dy)
        
        if distance > 0:
            self.vel_x = (dx / distance) * speed
            self.vel_y = (dy / distance) * speed
        else:
            self.vel_x = 0
            self.vel_y = -speed
            
        self.lifetime = 180

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.kill()
        if not screen.get_rect().colliderect(self.rect):
            self.kill()

class FireBoss(pygame.sprite.Sprite):
    def __init__(self, spawn_left=True, player=None):
        super().__init__()
        self.frames = load_fire_boss_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        self.height_scale = 1.8
        self.width_scale = 1.5
        self.scaled_frames = []
        for frame in self.frames:
            original_width, original_height = frame.get_size()
            new_width = int(original_width * self.width_scale)
            new_height = int(original_height * self.height_scale)
            scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
            self.scaled_frames.append(scaled_frame)
        
        self.image = self.scaled_frames[self.current_frame]
        
        if spawn_left:
            self.rect = self.scaled_frames[self.current_frame].get_rect(midbottom=(50, GROUND_LEVEL))
            self.facing_right = True
        else:
            self.rect = self.scaled_frames[self.current_frame].get_rect(midright=(WIDTH - 50, GROUND_LEVEL))
            self.facing_right = False
            
        self.mask = pygame.mask.from_surface(self.image) 
        
        self.player = player
        self.state = "idle"
        self.anim_timer = 0
        self.anim_delay = 10
        
        wave_bonus_health = (wave_system.current_wave - 10) // 10 * 50
        # 2x tankier - increased from 60 to 120 base health
        self.health = 120 + wave_bonus_health
        self.attack_cooldown = 0
        self.attack_range = 400
        
        self.buildup_duration = 120
        self.attack_duration = 90
        self.recovery_duration = 120
        # 2x damage - increased from 4 to 8
        self.attack_damage = 8
        
        self.contact_damage = 2  # Increased from 1 to 2
        self.contact_cooldown = 0
        self.contact_cooldown_max = 60
        
        self.normal_attack_range_width = 500
        self.enhanced_attack_range_width = 700
        self.attack_range_height = 200
        
        self.spawn_left = spawn_left
        
    def update(self, player=None):
        if player:
            self.player = player
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        if self.contact_cooldown > 0:
            self.contact_cooldown -= 1
            
        self.check_contact_damage()
            
        if self.state == "idle":
            self.idle_behavior()
        elif self.state == "buildup":
            self.buildup_behavior()
        elif self.state == "attack":
            self.attack_behavior()
        elif self.state == "recovery":
            self.recovery_behavior()
            
        self.update_animation()
        self.mask = pygame.mask.from_surface(self.image)
        
    def check_contact_damage(self):
        if (self.player and 
            self.contact_cooldown == 0 and 
            self.player.invincible_timer == 0 and 
            not self.player.god_mode and
            pygame.sprite.collide_mask(self, self.player)):
            
            self.player.health -= self.contact_damage
            self.player.invincible_timer = 180
            self.contact_cooldown = self.contact_cooldown_max
            trigger_screen_shake(12, 20)
            play_sound_safe(player_hit_sound, "player_hit_sound")
            print(f"[FIRE BOSS CONTACT] Player health: {self.player.health}")
        
    def idle_behavior(self):
        self.current_frame = 0
        
        if self.player and self.attack_cooldown == 0:
            if self.spawn_left:
                player_in_front = self.player.rect.centerx > self.rect.left
                player_in_range = abs(self.player.rect.centerx - self.rect.centerx) < self.attack_range
            else:
                player_in_front = self.player.rect.centerx < self.rect.right
                player_in_range = abs(self.player.rect.centerx - self.rect.centerx) < self.attack_range
            
            if player_in_front and player_in_range:
                self.state = "buildup"
                self.anim_timer = 0
                print("[FIRE BOSS] Starting attack buildup!")
                    
    def buildup_behavior(self):
        self.anim_timer += 1
        
        buildup_progress = min(self.anim_timer / self.buildup_duration, 1.0)
        self.current_frame = 1 + int(buildup_progress * 3)
        
        if self.anim_timer >= self.buildup_duration:
            self.state = "attack"
            self.anim_timer = 0
            self.current_frame = 4
            print("[FIRE BOSS] ATTACKING!")
            
    def attack_behavior(self):
        self.anim_timer += 1
        self.current_frame = 4
        
        if self.player and self.player.invincible_timer == 0 and not self.player.god_mode:
            current_attack_range = self.enhanced_attack_range_width
            
            if self.spawn_left:
                attack_rect = pygame.Rect(
                    self.rect.right, 
                    self.rect.top - self.attack_range_height,
                    current_attack_range,
                    self.attack_range_height + self.rect.height
                )
            else:
                attack_rect = pygame.Rect(
                    self.rect.left - current_attack_range,
                    self.rect.top - self.attack_range_height,
                    current_attack_range,
                    self.attack_range_height + self.rect.height
                )
            
            if attack_rect.colliderect(self.player.rect):
                self.player.health -= self.attack_damage
                self.player.invincible_timer = 180
                trigger_screen_shake(15, 25)
                play_sound_safe(player_hit_sound, "player_hit_sound")
                print(f"[FIRE BOSS HIT] Player health: {self.player.health}")
                
        if self.anim_timer >= self.attack_duration:
            self.state = "recovery"
            self.anim_timer = 0
            print("[FIRE BOSS] Attack finished, recovering...")
            
    def recovery_behavior(self):
        self.anim_timer += 1
        self.current_frame = 0
        
        if self.anim_timer >= self.recovery_duration:
            self.state = "idle"
            self.attack_cooldown = 180
            self.anim_timer = 0
            print("[FIRE BOSS] Ready for next attack!")
            
    def update_animation(self):
        frame = self.scaled_frames[self.current_frame]
        
        if self.spawn_left:
            frame = pygame.transform.flip(frame, True, False)
        
        old_bottom = self.rect.bottom
        if self.spawn_left:
            old_left = self.rect.left
        else:
            old_right = self.rect.right
        
        self.image = frame
        
        if self.spawn_left:
            self.rect = self.image.get_rect(bottomleft=(old_left, GROUND_LEVEL))
        else:
            self.rect = self.image.get_rect(bottomright=(old_right, GROUND_LEVEL))

# --- FLYING ENEMIES ---

class DragonBoss(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.frames = load_dragon_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.player = player
        self.state = "idle"
        self.anim_timer = 0
        self.anim_delay = 10
        self.attack_cooldown = 0
        wave_bonus_health = (wave_system.current_wave - 10) // 10 * 40
        # 2x tankier - increased from 50 to 100 base health
        self.health = 100 + wave_bonus_health
        # 2x damage - increased from 3 to 6
        self.attack_damage = 6
        
        self.attack_range = 400
        self.attack_duration = 180
        self.buildup_duration = 90
        self.recovery_duration = 60
        
        self.speed = 4
        self.chase_speed = 5
        self.direction = -1
        self.hover_range = 50
        self.original_x = x
        self.original_y = y
        
        self.attack_active = False
        self.enraged = False
        self.enrage_health_threshold = 0.4
        self.roar_played = False
        
        self.avoidance_force = 0
        self.avoidance_timer = 0
        self.personal_space = 150
    
    def update(self, player):
        global dragon_roar_played
        
        self.player = player
        
        if player.rect.centerx > self.rect.centerx:
            self.direction = 1
        else:
            self.direction = -1
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if not self.enraged and self.health <= (100 + ((wave_system.current_wave - 10) // 10 * 40)) * self.enrage_health_threshold:
            self.activate_enrage_mode()
            
        if self.state == "chase" and dragon_roar_sound and not dragon_roar_played and not self.roar_played:
            play_sound_safe(dragon_roar_sound, "dragon_roar_sound")
            dragon_roar_played = True
            self.roar_played = True
            print("[SOUND] Dragon roar!")
            
        if self.state == "idle":
            self.idle_behavior()
        elif self.state == "chase":
            self.chase_behavior()
        elif self.state == "buildup":
            self.buildup_behavior()
        elif self.state == "attack":
            self.attack_behavior()
        elif self.state == "recovery":
            self.recovery_behavior()
        
        if self.state != "attack":
            self.avoid_other_dragons()
        
        self.update_animation()
        self.mask = pygame.mask.from_surface(self.image)
    
    def avoid_other_dragons(self):
        self.avoidance_timer += 1
        
        if self.avoidance_timer >= 10:
            self.avoidance_timer = 0
            
            for dragon in ground_enemy_group:
                if isinstance(dragon, DragonBoss) and dragon != self:
                    distance = math.hypot(self.rect.centerx - dragon.rect.centerx,
                                        self.rect.centery - dragon.rect.centery)
                    
                    if distance < self.personal_space:
                        dx = self.rect.centerx - dragon.rect.centerx
                        dy = self.rect.centery - dragon.rect.centery
                        
                        if dx != 0 or dy != 0:
                            norm_x, norm_y = dx / distance, dy / distance
                            push_strength = (self.personal_space - distance) * 0.1
                            
                            self.rect.x += int(norm_x * push_strength)
                            self.rect.y += int(norm_y * push_strength)
                            
                            self.rect.left = max(50, self.rect.left)
                            self.rect.right = min(WIDTH - 50, self.rect.right)
                            self.rect.top = max(30, self.rect.top)
                            self.rect.bottom = min(HEIGHT - 80, self.rect.bottom)
    
    def activate_enrage_mode(self):
        self.enraged = True
        self.speed = 5
        self.chase_speed = 6
        self.attack_damage = 8  # Increased from 4 to 8 (2x damage)
        self.personal_space = 200
        print("[DRAGON BOSS] ENRAGED! Speed and damage increased!")
    
    def idle_behavior(self):
        hover_y = math.sin(pygame.time.get_ticks() * 0.005 + self.original_x) * 20
        self.rect.centery = self.original_y + hover_y
        
        drift_x = math.sin(pygame.time.get_ticks() * 0.002 + self.original_y) * 10
        self.rect.centerx = self.original_x + drift_x
        
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                      self.rect.centery - self.player.rect.centery)
        
        if distance_to_player > 300:
            self.state = "chase"
            print("[DRAGON BOSS] Player too far, chasing!")
        elif distance_to_player < self.attack_range and self.attack_cooldown == 0:
            self.state = "buildup"
            self.anim_timer = 0
            print("[DRAGON BOSS] Starting attack buildup!")

    def chase_behavior(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        
        if distance > 0:
            speed_multiplier = min(1.5, distance / 200)
            current_speed = self.chase_speed * speed_multiplier
            
            dx, dy = dx / distance, dy / distance
            self.rect.x += dx * current_speed
            self.rect.y += dy * current_speed
        
        if self.rect.left < 50:
            self.rect.left = 50
        elif self.rect.right > WIDTH - 50:
            self.rect.right = WIDTH - 50
        if self.rect.top < 30:
            self.rect.top = 30
        elif self.rect.bottom > HEIGHT - 80:
            self.rect.bottom = HEIGHT - 80
        
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                    self.rect.centery - self.player.rect.centery)
        
        if distance_to_player < 80:
            self.state = "idle"
            self.original_x = self.rect.centerx
            self.original_y = self.rect.centery
        elif distance_to_player < self.attack_range and self.attack_cooldown == 0:
            self.state = "buildup"
            self.anim_timer = 0
            print("[DRAGON BOSS] Close enough, starting attack buildup!")
    
    def buildup_behavior(self):
        self.anim_timer += 1
        
        buildup_progress = min(self.anim_timer / self.buildup_duration, 1.0)
        if buildup_progress < 0.5:
            self.current_frame = 2
        else:
            self.current_frame = 3
        
        if self.anim_timer >= self.buildup_duration:
            self.state = "attack"
            self.anim_timer = 0
            self.attack_active = True
            print("[DRAGON BOSS] ATTACKING!")
    
    def attack_behavior(self):
        self.anim_timer += 1
        
        if self.anim_timer < 30:
            self.current_frame = 4
        elif self.anim_timer < 60:
            self.current_frame = 5
        else:
            self.current_frame = 6
        
        if self.attack_active:
            breath_range = 300
            breath_width = 150
            
            if self.direction > 0:
                breath_rect = pygame.Rect(
                    self.rect.centerx,
                    self.rect.centery - breath_width//2,
                    breath_range,
                    breath_width
                )
            else:
                breath_rect = pygame.Rect(
                    self.rect.centerx - breath_range,
                    self.rect.centery - breath_width//2,
                    breath_range,
                    breath_width
                )
            
            if self.current_frame in [5, 6] and breath_rect.colliderect(self.player.rect):
                if self.player.invincible_timer == 0 and not self.player.god_mode:
                    self.player.health -= self.attack_damage
                    self.player.invincible_timer = 180
                    trigger_screen_shake(15, 25)
                    play_sound_safe(player_hit_sound, "player_hit_sound")
                    print(f"[DRAGON BREATH HIT] Player health: {self.player.health}")
                    self.attack_active = False
        
        if self.anim_timer >= self.attack_duration:
            self.state = "recovery"
            self.anim_timer = 0
            self.attack_active = False
            print("[DRAGON BOSS] Attack finished, recovering...")
    
    def recovery_behavior(self):
        self.anim_timer += 1
        
        recovery_progress = min(self.anim_timer / self.recovery_duration, 1.0)
        if recovery_progress < 0.33:
            self.current_frame = 6
        elif recovery_progress < 0.66:
            self.current_frame = 7
        else:
            self.current_frame = 8
        
        if self.anim_timer >= self.recovery_duration:
            distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                          self.rect.centery - self.player.rect.centery)
            
            if distance_to_player > 200:
                self.state = "chase"
                print("[DRAGON BOSS] Player moved away, chasing!")
            else:
                self.state = "idle"
                self.original_x = self.rect.centerx
                self.original_y = self.rect.centery
            
            self.attack_cooldown = 120
            self.anim_timer = 0
    
    def update_animation(self):
        if self.state == "idle":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 3
        elif self.state == "chase":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 3
        
        frame = self.frames[self.current_frame]
        
        if self.direction > 0:
            frame = pygame.transform.flip(frame, True, False)
        
        old_center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=old_center)

class RocketEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.frames = load_rocket_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.player = player
        self.state = "hover"
        self.anim_timer = 0
        self.anim_delay = 8
        self.attack_cooldown = 0
        self.hover_speed = 1
        self.hover_range = 50
        self.original_y = y
        self.original_x = x
        self.hover_direction = 1
        self.health = 2
        
        self.attack_speed = 8
        self.attack_direction = pygame.Vector2(0, 0)
        self.attack_duration = 90
        self.buildup_timer = 0
        self.buildup_duration = 70

    def update(self, player):
        self.player = player

        if self.state == "hover":
            self.hover_behavior()
        elif self.state == "buildup":
            self.buildup_behavior()
        elif self.state == "attack":
            self.attack_behavior()

        self.update_animation()

    def hover_behavior(self):
        self.rect.y += self.hover_speed * self.hover_direction
        
        if self.rect.centery <= self.original_y - self.hover_range:
            self.hover_direction = 1
        elif self.rect.centery >= self.original_y + self.hover_range:
            self.hover_direction = -1
        
        hover_x = math.sin(pygame.time.get_ticks() * 0.005) * 20
        self.rect.centerx = self.original_x + hover_x
        
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                      self.rect.centery - self.player.rect.centery)
        
        if distance_to_player < 400 and self.attack_cooldown == 0:
            self.state = "buildup"
            self.buildup_timer = 0
            self.current_frame = 4

    def buildup_behavior(self):
        self.buildup_timer += 1
        
        buildup_progress = self.buildup_timer / self.buildup_duration
        buildup_frame = 4 + int(buildup_progress * 7)
        self.current_frame = min(buildup_frame, 10)
        
        if self.buildup_timer >= self.buildup_duration:
            self.state = "attack"
            self.attack_duration = 90
            self.current_frame = 11
            
            dx = self.player.rect.centerx - self.rect.centerx
            dy = self.player.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                self.attack_direction = pygame.Vector2(dx/distance, dy/distance)
            else:
                self.attack_direction = pygame.Vector2(1, 0)

    def attack_behavior(self):
        self.current_frame = 11
        
        self.rect.x += self.attack_direction.x * self.attack_speed
        self.rect.y += self.attack_direction.y * self.attack_speed
        
        screen_padding = 100
        if (self.rect.right < -screen_padding or 
            self.rect.left > WIDTH + screen_padding or 
            self.rect.bottom < -screen_padding or 
            self.rect.top > HEIGHT + screen_padding):
            self.reset_to_hover()
            return
        
        self.attack_duration -= 1
        if self.attack_duration <= 0:
            self.reset_to_hover()

    def reset_to_hover(self):
        self.state = "hover"
        self.attack_cooldown = 60
        
        new_x = random.randint(100, WIDTH - 100)
        new_y = random.randint(100, HEIGHT - 200)
        
        min_distance_from_player = 200
        distance_to_player = math.hypot(new_x - self.player.rect.centerx, new_y - self.player.rect.centery)
        
        attempts = 0
        while distance_to_player < min_distance_from_player and attempts < 5:
            new_x = random.randint(100, WIDTH - 100)
            new_y = random.randint(100, HEIGHT - 200)
            distance_to_player = math.hypot(new_x - self.player.rect.centerx, new_y - self.player.rect.centery)
            attempts += 1
        
        self.rect.center = (new_x, new_y)
        self.original_x = new_x
        self.original_y = new_y
        self.hover_direction = 1
        
        self.buildup_timer = 0
        self.attack_duration = 90
        self.current_frame = 0

    def update_animation(self):
        if self.state == "hover":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 4
            
            if self.player.rect.centerx > self.rect.centerx:
                frame = pygame.transform.flip(self.frames[self.current_frame], True, False)
            else:
                frame = self.frames[self.current_frame]

        elif self.state == "buildup":
            frame = self.frames[self.current_frame]
            if self.player.rect.centerx > self.rect.centerx:
                frame = pygame.transform.flip(frame, True, False)
            else:
                frame = frame
        
        elif self.state == "attack":
            frame = self.frames[self.current_frame]
            if self.attack_direction.x > 0:
                frame = pygame.transform.flip(frame, True, False)
            else:
                frame = frame

        old_center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=old_center)
        self.mask = pygame.mask.from_surface(self.image)

class Reaper(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.frames = load_reaper_frames()
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.player = player
        self.state = "hover"
        self.anim_timer = 0
        self.anim_delay = 8
        self.attack_cooldown = 0
        
        self.speed = 2.5
        self.hover_speed = 1
        self.hover_range = 40
        self.original_y = y
        self.hover_direction = 1
        self.health = 2
        
        self.attack_range = 200
        self.attack_speed = 3
        self.damage = 1
        self.attack_timer = 0
        self.attack_duration = 60
        
        self.float_timer = 0

    def update(self, player):
        self.player = player
        
        if self.state == "hover":
            self.hover_behavior()
        elif self.state == "attack":
            self.attack_behavior()

        self.update_animation()

    def hover_behavior(self):
        self.rect.y += self.hover_speed * self.hover_direction
        
        if self.rect.centery <= self.original_y - self.hover_range:
            self.hover_direction = 1
        elif self.rect.centery >= self.original_y + self.hover_range:
            self.hover_direction = -1
        
        hover_x = math.sin(pygame.time.get_ticks() * 0.003) * 15
        self.rect.centerx = self.rect.centerx + hover_x * 0.1
        
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                      self.rect.centery - self.player.rect.centery)
        
        if distance_to_player < self.attack_range:
            self.state = "attack"
            self.attack_timer = 0
            self.current_frame = 1

    def attack_behavior(self):
        self.attack_timer += 1
        
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        
        if distance > 0:
            dx, dy = dx / distance, dy / distance
            self.rect.x += dx * self.attack_speed
            self.rect.y += dy * self.attack_speed
            
            if distance < 50 and self.player.invincible_timer == 0 and not self.player.god_mode:
                self.player.health -= self.damage
                self.player.invincible_timer = 180
                trigger_screen_shake(8, 15)
                play_sound_safe(player_hit_sound, "player_hit_sound")
                print(f"[REAPER HIT] Player health: {self.player.health}")
        
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 50:
            self.rect.top = 50
        elif self.rect.bottom > HEIGHT - 100:
            self.rect.bottom = HEIGHT - 100
        
        distance_to_player = math.hypot(self.rect.centerx - self.player.rect.centerx,
                                      self.rect.centery - self.player.rect.centery)
        
        if distance_to_player > 300 or self.attack_timer >= self.attack_duration:
            self.state = "hover"
            self.original_y = self.rect.centery

    def reset_to_hover(self):
        self.state = "hover"
        self.attack_cooldown = 60
        self.original_y = self.rect.centery

    def update_animation(self):
        if self.state == "hover":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 2
        elif self.state == "attack":
            self.anim_timer += 1
            if self.anim_timer >= self.anim_delay:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % 6
                if self.current_frame == 0:
                    self.current_frame = 1

        frame = self.frames[self.current_frame]
        
        if self.state == "attack":
            if self.player.rect.centerx > self.rect.centerx:
                frame = pygame.transform.flip(frame, True, False)
            else:
                frame = frame
        else:
            if hasattr(self, 'last_x'):
                if self.rect.centerx > self.last_x:
                    frame = pygame.transform.flip(frame, True, False)
            self.last_x = self.rect.centerx

        old_center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=old_center)
        self.mask = pygame.mask.from_surface(self.image)

# --- Ally Class ---
class Ally(pygame.sprite.Sprite):
    def __init__(self, ground_enemy_group):
        super().__init__()
        self.frames = load_ally_frames()
        self.current_frame = 15
        self.image = self.frames[self.current_frame]
        
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, GROUND_LEVEL))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.ground_enemy_group = ground_enemy_group
        
        self.combo_state = "idle"
        self.combo_step = 0
        self.combo_timer = 0
        self.attack_cooldown = 0
        
        self.speed = 3
        self.vel_y = 0
        self.gravity = 0.8
        self.on_ground = True
        
        self.attack_range = 200
        self.damage = 1
        
        self.anim_timer = 0
        self.anim_delay = 15
        self.running_frames = [15, 13, 14]
        self.running_frame_index = 0
        self.facing_right = True

        self.attack_delays = {
            0: 8, 1: 6, 2: 4, 3: 6, 4: 6, 5: 6, 6: 4, 7: 8, 8: 10, 9: 6, 10: 4
        }

        self.current_target = None
        self.target_reached = False

    def update(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        
        if self.rect.bottom >= GROUND_LEVEL:
            self.rect.bottom = GROUND_LEVEL
            self.vel_y = 0
            self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

        nearest_enemy = self.find_nearest_ground_level_enemy()
        
        if nearest_enemy:
            distance = abs(nearest_enemy.rect.centerx - self.rect.centerx)
            
            if distance <= self.attack_range and self.attack_cooldown == 0:
                if self.combo_state != "attacking" and self.combo_state != "recovery":
                    self.combo_state = "attacking"
                    self.combo_step = 0
                    self.combo_timer = 0
                    self.current_target = nearest_enemy
                    print(f"[ALLY] Starting combo against {nearest_enemy.__class__.__name__}!")
            elif distance > self.attack_range and self.combo_state == "idle":
                self.combo_state = "running"
                self.current_target = nearest_enemy
                self.move_toward_target()
            else:
                if self.combo_state != "attacking" and self.combo_state != "recovery":
                    self.combo_state = "idle"
                    self.current_frame = 15
        else:
            if self.combo_state != "attacking" and self.combo_state != "recovery":
                self.combo_state = "idle"
                self.current_frame = 15

        if self.combo_state == "idle":
            self.idle_behavior()
        elif self.combo_state == "running":
            self.running_behavior()
        elif self.combo_state == "attacking":
            self.attack_behavior()
        elif self.combo_state == "recovery":
            self.recovery_behavior()

        if self.current_target:
            if self.current_target.rect.centerx > self.rect.centerx:
                self.facing_right = True
            else:
                self.facing_right = False

        self.update_animation()

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def find_nearest_ground_level_enemy(self):
        nearest = None
        nearest_distance = float('inf')
        
        for enemy in self.ground_enemy_group:
            if hasattr(enemy, 'on_ground') and enemy.on_ground and not enemy.on_platform:
                distance = abs(enemy.rect.centerx - self.rect.centerx)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest = enemy
                
        return nearest

    def move_toward_target(self):
        if not self.current_target:
            return
            
        target_x = self.current_target.rect.centerx
        distance_to_target = abs(self.rect.centerx - target_x)
        
        if distance_to_target > 50:
            if self.rect.centerx < target_x:
                self.rect.x += min(self.speed, distance_to_target)
            else:
                self.rect.x -= min(self.speed, distance_to_target)

    def move_toward_target_during_attack(self):
        if not self.current_target:
            return
            
        target_x = self.current_target.rect.centerx
        distance_to_target = abs(self.rect.centerx - target_x)
        
        if distance_to_target > 30:
            attack_move_speed = 2
            if self.rect.centerx < target_x:
                self.rect.x += attack_move_speed
            else:
                self.rect.x -= attack_move_speed

    def idle_behavior(self):
        self.current_frame = 15

    def running_behavior(self):
        self.anim_timer += 1
        if self.anim_timer >= self.anim_delay:
            self.anim_timer = 0
            self.running_frame_index = (self.running_frame_index + 1) % len(self.running_frames)
            self.current_frame = self.running_frames[self.running_frame_index]
        
        self.move_toward_target()

    def attack_behavior(self):
        self.combo_timer += 1
        
        current_delay = self.attack_delays.get(self.combo_step, 4)
        
        if self.combo_step < 6 or self.combo_step > 8:
            self.move_toward_target_during_attack()
        
        if self.combo_step == 0:
            if self.combo_timer >= current_delay:
                self.combo_step = 1
                self.combo_timer = 0
                self.current_frame = 2
                
        elif self.combo_step == 1:
            if self.combo_timer >= current_delay:
                self.deal_damage_in_front()
                self.combo_step = 2
                self.combo_timer = 0
                self.current_frame = 4
                
        elif self.combo_step == 2:
            if self.combo_timer >= current_delay:
                self.combo_step = 3
                self.combo_timer = 0
                self.current_frame = 5
                
        elif self.combo_step == 3:
            if self.combo_timer >= current_delay:
                self.deal_damage_in_front()
                self.combo_step = 4
                self.combo_timer = 0
                self.current_frame = 7
                
        elif self.combo_step == 4:
            if self.combo_timer >= current_delay:
                self.combo_step = 5
                self.combo_timer = 0
                self.current_frame = 9
                
        elif self.combo_step == 5:
            if self.combo_timer >= current_delay:
                self.deal_damage_in_front()
                self.combo_step = 6
                self.combo_timer = 0
                self.current_frame = 11
                
        elif self.combo_step == 6:
            if self.combo_timer >= current_delay:
                self.combo_step = 7
                self.combo_timer = 0
                self.current_frame = 12
                if self.on_ground:
                    self.vel_y = -12
                    self.on_ground = False
                    self.deal_damage_above()
            
        elif self.combo_step == 7:
            if self.combo_timer >= current_delay:
                self.combo_step = 8
                self.combo_timer = 0
                self.current_frame = 14
            
        elif self.combo_step == 8:
            if self.current_target:
                jump_speed = 8
                if self.current_target.rect.centerx > self.rect.centerx:
                    self.rect.x += jump_speed
                else:
                    self.rect.x -= jump_speed
                    
            if self.combo_timer >= current_delay:
                self.combo_step = 9
                self.combo_timer = 0
                self.current_frame = 17
                
        elif self.combo_step == 9:
            if self.combo_timer >= current_delay:
                self.deal_damage_in_front()
                self.combo_step = 10
                self.combo_timer = 0
                self.current_frame = 18
                
        elif self.combo_step == 10:
            if self.combo_timer >= current_delay:
                self.combo_state = "recovery"
                self.combo_timer = 0
                self.attack_cooldown = 120

    def deal_damage_in_front(self):
        for enemy in self.ground_enemy_group:
            if hasattr(enemy, 'on_ground'):
                distance = abs(enemy.rect.centerx - self.rect.centerx)
                if distance < 80:
                    enemy.health -= self.damage
                    print(f"[ALLY HIT] {enemy.__class__.__name__} HP: {enemy.health}")
                    
                    knockback_dir = 1 if enemy.rect.centerx > self.rect.centerx else -1
                    enemy.rect.x += knockback_dir * 8
                    if hasattr(enemy, 'vel_y'):
                        enemy.vel_y = -4

    def deal_damage_above(self):
        for enemy in self.ground_enemy_group:
            if hasattr(enemy, 'on_ground'):
                if (abs(enemy.rect.centerx - self.rect.centerx) < 50 and 
                    enemy.rect.bottom < self.rect.top and 
                    enemy.rect.top > self.rect.top - 100):
                    
                    enemy.health -= self.damage
                    print(f"[ALLY UPPERCUT] {enemy.__class__.__name__} HP: {enemy.health}")
                    
                    if hasattr(enemy, 'vel_y'):
                        enemy.vel_y = -8

    def recovery_behavior(self):
        self.combo_timer += 1
        if self.combo_timer >= 45:
            self.combo_state = "idle"
            self.combo_timer = 0
            self.current_target = None

    def update_animation(self):
        frame = self.frames[self.current_frame]
        
        if self.current_frame == 10:
            if self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
        else:
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)

        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.image = frame
        self.rect = self.image.get_rect(midbottom=(old_centerx, old_bottom))
        self.mask = pygame.mask.from_surface(self.image)

# --- Initialize Systems ---
wave_system = WaveSystem()
enemy_spawner = EnemySpawner(wave_system)
score_system = ScoreSystem()

# --- Groups ---
all_sprites = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_projectile_group = pygame.sprite.Group()
ground_enemy_group = pygame.sprite.Group()
flying_enemy_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()

# --- Platform positions ---
platform_positions = [
    (WIDTH // 4 - 60, 380),
    (3 * WIDTH // 4 - 60, 380),
    (WIDTH // 6 - 60, 280),
    (WIDTH // 2 - 60, 260),
    (5 * WIDTH // 6 - 60, 280),
    (WIDTH // 3 - 60, 160),
    (2 * WIDTH // 3 - 60, 160)
]

# --- Game Initialization Function ---
def initialize_game():
    global player, gun, knife, ally, all_sprites, ground_enemy_group, flying_enemy_group, bullet_group, enemy_projectile_group
    global dragon_roar_played, boss_music_playing
    
    all_sprites.empty()
    ground_enemy_group.empty()
    flying_enemy_group.empty()
    bullet_group.empty()
    enemy_projectile_group.empty()
    
    dragon_roar_played = False
    boss_music_playing = False
    
    stop_music()
    
    player = Player(WIDTH // 2, GROUND_LEVEL)
    all_sprites.add(player)
    
    for pos in platform_positions:
        platform = Platform(pos[0], pos[1], width=120, height=20)
        platform_group.add(platform)
        all_sprites.add(platform)
    
    knife = Knife(player, ground_enemy_group, flying_enemy_group)
    all_sprites.add(knife)
    
    gun = Gun(player, bullet_group)
    all_sprites.add(gun)
    
    ally = Ally(ground_enemy_group)
    all_sprites.add(ally)

# Initialize the game
initialize_game()

# --- Load sound effects and music ---
def load_sounds():
    global dragon_roar_sound, gun_sound, player_hit_sound, player_blast_sound, gun_empty_sound
    global title_music, gameplay_music, boss_music
    
    print("[SOUND] Loading sound effects and music...")
    
    # Load sound effects with web compatibility
    sound_files = [
        ("dragonRoar.wav", 0.7, "dragon_roar_sound"),
        ("gunSound.wav", 0.5, "gun_sound"), 
        ("gunEmptySound.wav", 0.6, "gun_empty_sound"),
        ("playerGetHit.wav", 0.6, "player_hit_sound"),
        ("playerBlast.wav", 1.5, "player_blast_sound")
    ]
    
    for filename, volume, var_name in sound_files:
        try:
            sound = load_sound(filename, volume)
            globals()[var_name] = sound
            if sound:
                print(f"[SOUND] Loaded: {filename}")
            else:
                print(f"[SOUND WARNING] Failed to load: {filename}")
        except Exception as e:
            print(f"[SOUND ERROR] Failed to load {filename}: {e}")
            globals()[var_name] = None
    
    # Music file paths - handle format differences
    try:
        if WEB:
            # Web version - use direct paths
            title_music = "assets/titleScreenBG.wav"
            boss_music = "assets/bossMusic.wav"
            gameplay_music = "assets/gameplayBackground.mp3"
            
            print("[SOUND] Web music paths configured")
        else:
            # Desktop version - original paths
            import os
            ASSET_DIR = "assets"
            title_music = os.path.join(ASSET_DIR, "titleScreenBG.wav")
            gameplay_music = os.path.join(ASSET_DIR, "gameplayBackground.mp3")
            boss_music = os.path.join(ASSET_DIR, "bossMusic.wav")
            
        print("[SOUND] Music paths configured successfully")
            
    except Exception as e:
        print(f"[SOUND ERROR] Could not configure music files: {e}")

load_sounds()

# Load background
load_background()

# --- Main loop ---
clock = pygame.time.Clock()
running = True
show_hitboxes = False
switch_weapon_pressed = False
show_stats = False

# Start with title music
update_music_for_state()

async def main():
    global running, current_game_state, player_name, final_wave, final_score
    global show_hitboxes, switch_weapon_pressed, show_stats, boss_music_playing
    
    # Initialize custom fonts
    initialize_fonts()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if current_game_state == TITLE_SCREEN:
                    start_button, leaderboard_button, howtoplay_button = draw_title_screen()
                    
                    if start_button.collidepoint(mouse_pos):
                        current_game_state = GAME_ACTIVE
                        wave_system = WaveSystem()
                        enemy_spawner = EnemySpawner(wave_system)
                        score_system = ScoreSystem()
                        initialize_game()
                        update_background_for_wave(wave_system.current_wave)
                        update_music_for_state()
                        
                    elif leaderboard_button.collidepoint(mouse_pos):
                        current_game_state = LEADERBOARD
                    
                    elif howtoplay_button.collidepoint(mouse_pos):
                        current_game_state = HOW_TO_PLAY

                elif current_game_state == LEADERBOARD:
                    back_button = draw_leaderboard()
                    if back_button.collidepoint(mouse_pos):
                        current_game_state = TITLE_SCREEN

                elif current_game_state == HOW_TO_PLAY:
                    back_button = draw_how_to_play()
                    if back_button.collidepoint(mouse_pos):
                        current_game_state = TITLE_SCREEN

                elif current_game_state == NAME_ENTRY:
                    input_box, submit_button = draw_name_entry()
                    if submit_button.collidepoint(mouse_pos) and len(player_name) > 0:
                        save_score(player_name, final_wave, final_score)
                        player_name = ""
                        current_game_state = TITLE_SCREEN
        
            if event.type == pygame.KEYDOWN:
                if current_game_state == NAME_ENTRY:
                    if event.key == pygame.K_RETURN and len(player_name) > 0:
                        save_score(player_name, final_wave, final_score)
                        player_name = ""
                        current_game_state = TITLE_SCREEN
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        player_name = ""
                        current_game_state = TITLE_SCREEN
                    elif len(player_name) < 12:
                        if event.unicode.isalnum() or event.unicode == ' ':
                            player_name += event.unicode
                
                elif current_game_state == GAME_ACTIVE:
                    if event.key == pygame.K_h:
                        show_hitboxes = not show_hitboxes
                    if event.key == pygame.K_q:
                        if not switch_weapon_pressed:
                            gun.switch_weapon()
                            switch_weapon_pressed = True
                    if event.key == pygame.K_i:
                        player.toggle_god_mode()
                    if event.key == pygame.K_m:
                        show_stats = not show_stats
                    if event.key == pygame.K_ESCAPE:
                        current_game_state = TITLE_SCREEN
            
            if event.type == pygame.KEYUP and current_game_state == GAME_ACTIVE:
                if event.key == pygame.K_q:
                    switch_weapon_pressed = False

        update_music_for_state()

        if current_game_state == TITLE_SCREEN:
            start_button, leaderboard_button, howtoplay_button = draw_title_screen()
        
        elif current_game_state == LEADERBOARD:
            back_button = draw_leaderboard()
        
        elif current_game_state == HOW_TO_PLAY:
            back_button = draw_how_to_play()
        
        elif current_game_state == NAME_ENTRY:
            input_box, submit_button = draw_name_entry()
        
        elif current_game_state == GAME_ACTIVE:
            keys = pygame.key.get_pressed()
            player.update_keyboard(keys, platform_group)
            gun.update_keyboard()
            knife.update_keyboard()
            ground_enemy_group.update(player)
            flying_enemy_group.update(player)
            ally.update()
            bullet_group.update()
            enemy_projectile_group.update()

            update_screen_shake()

            wave_system.update()

            # Check if bosses should spawn
            if wave_system.should_spawn_bosses():
                bosses_to_spawn = wave_system.get_bosses_to_spawn()
                for boss_type, position in bosses_to_spawn:
                    if boss_type == "fire":
                        spawn_left = (position == "left")
                        fire_boss = FireBoss(spawn_left=spawn_left, player=player)
                        all_sprites.add(fire_boss)
                        ground_enemy_group.add(fire_boss)
                        wave_system.wave_enemies_spawned += 1
                        wave_system.enemies_remaining -= 1
                        print(f"[BOSS SPAWN] Fire Boss (Wave {wave_system.current_wave})")
                        
                        # Start boss music when boss spawns
                        if not boss_music_playing:
                            play_music("boss")
                            boss_music_playing = True
                            print("[SOUND] Boss music started!")
                            
                    elif boss_type == "dragon":
                        if isinstance(position, str) and position.startswith("position_"):
                            index = int(position.split("_")[1])
                            x_pos = WIDTH - 150 - (index * 200)
                            if x_pos < 100:
                                x_pos = 100
                        else:
                            x_pos = WIDTH - 150
                            
                        dragon_boss = DragonBoss(x_pos, 150, player)
                        all_sprites.add(dragon_boss)
                        ground_enemy_group.add(dragon_boss)
                        flying_enemy_group.add(dragon_boss)
                        wave_system.wave_enemies_spawned += 1
                        wave_system.enemies_remaining -= 1
                        print(f"[BOSS SPAWN] Dragon Boss (Wave {wave_system.current_wave})")
                        
                        # Start boss music when boss spawns
                        if not boss_music_playing:
                            play_music("boss")
                            boss_music_playing = True
                            print("[SOUND] Boss music started!")

            # Check if all bosses are defeated
            if boss_music_playing:
                boss_alive = False
                for enemy in ground_enemy_group:
                    if isinstance(enemy, (FireBoss, DragonBoss)):
                        boss_alive = True
                        break
                
                # If no bosses are alive, stop boss music
                if not boss_alive and boss_music_playing:
                    play_music("gameplay")
                    boss_music_playing = False
                    print("[SOUND] Boss defeated, switching back to gameplay music")

            if wave_system.should_spawn_enemies():
                spawn_delays = enemy_spawner.get_spawn_delays()
                enemy_limits = enemy_spawner.get_enemy_limits()
                enemy_weights = enemy_spawner.get_enemy_types()
                
                current_total_enemies = len(ground_enemy_group) + len(flying_enemy_group)
                
                enemy_spawner.ground_spawn_timer += 1
                if (enemy_spawner.ground_spawn_timer >= spawn_delays['ground'] and 
                    len(ground_enemy_group) < enemy_limits['ground'] and
                    current_total_enemies < enemy_limits['total'] and
                    wave_system.enemies_remaining > 0):
                    
                    enemy_type = random.choices(
                        list(enemy_weights['ground'].keys()),
                        weights=list(enemy_weights['ground'].values())
                    )[0]
                    
                    spawn_on_platform = random.random() < 0.3
                    if spawn_on_platform and platform_group:
                        platform = random.choice(list(platform_group))
                        spawn_x = random.randint(platform.rect.left + 20, platform.rect.right - 20)
                        spawn_y = platform.rect.top
                    else:
                        spawn_x = random.randint(100, WIDTH - 100)
                        spawn_y = GROUND_LEVEL
                        
                    if enemy_type == "frog":
                        enemy = Frog(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                    elif enemy_type == "ghoul":
                        enemy = Ghoul(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                    elif enemy_type == "axolotl":
                        enemy = Axolotl(spawn_x, spawn_y, spawn_on_ground=not spawn_on_platform)
                    else:
                        enemy = Witch(spawn_x, spawn_y, player, spawn_on_ground=not spawn_on_platform)
                        
                    ground_enemy_group.add(enemy)
                    all_sprites.add(enemy)
                    enemy_spawner.ground_spawn_timer = 0
                    wave_system.wave_enemies_spawned += 1
                    wave_system.enemies_remaining -= 1
                
                enemy_spawner.flying_spawn_timer += 1
                if (enemy_spawner.flying_spawn_timer >= spawn_delays['flying'] and 
                    len(flying_enemy_group) < enemy_limits['flying'] and
                    current_total_enemies < enemy_limits['total'] and
                    wave_system.enemies_remaining > 0):
                    
                    enemy_type = random.choices(
                        list(enemy_weights['flying'].keys()),
                        weights=list(enemy_weights['flying'].values())
                    )[0]
                    
                    if enemy_type == "rocket":
                        enemy = RocketEnemy(random.randint(100, WIDTH - 100), random.randint(100, 300), player)
                    elif enemy_type == "reaper":
                        enemy = Reaper(random.randint(100, WIDTH - 100), random.randint(100, 300), player)
                    else:
                        enemy = Bat(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 200))
                        
                    flying_enemy_group.add(enemy)
                    all_sprites.add(enemy)
                    enemy_spawner.flying_spawn_timer = 0
                    wave_system.wave_enemies_spawned += 1
                    wave_system.enemies_remaining -= 1

            for bullet in bullet_group:
                hit_ground = pygame.sprite.spritecollide(bullet, ground_enemy_group, False, pygame.sprite.collide_mask)
                for enemy in hit_ground:
                    if isinstance(enemy, (FireBoss, DragonBoss)):
                        damage_taken = max(1, bullet.damage // 3)
                        enemy.health -= damage_taken
                        print(f"[BOSS HIT] {enemy.__class__.__name__} took {damage_taken} damage (reduced from {bullet.damage})")
                    else:
                        enemy.health -= bullet.damage
                    
                    if enemy.health <= 0:
                        enemy.kill()
                        if bullet.is_pistol:
                            gun.ak_ammo += 1
                            gun.shotgun_ammo += 1
                            print(f"[PISTOL KILL] +1 AK/Shotgun ammo!")
                        elif bullet.is_shotgun:
                            gun.shotgun_ammo += 1
                            print(f"[SHOTGUN KILL] +1 Shotgun ammo!")
                    bullet.kill()

                hit_flying = pygame.sprite.spritecollide(bullet, flying_enemy_group, False, pygame.sprite.collide_mask)
                for enemy in hit_flying:
                    if isinstance(enemy, (FireBoss, DragonBoss)):
                        damage_taken = max(1, bullet.damage // 3)
                        enemy.health -= damage_taken
                        print(f"[BOSS HIT] {enemy.__class__.__name__} took {damage_taken} damage (reduced from {bullet.damage})")
                    else:
                        enemy.health -= bullet.damage
                    
                    if enemy.health <= 0:
                        enemy.kill()
                        if bullet.is_pistol:
                            gun.ak_ammo += 1
                            gun.shotgun_ammo += 1
                            print(f"[PISTOL KILL] +1 AK/Shotgun ammo!")
                        elif bullet.is_shotgun:
                            gun.shotgun_ammo += 1
                            print(f"[SHOTGUN KILL] +1 Shotgun ammo!")
                    bullet.kill()

            for projectile in enemy_projectile_group:
                if (pygame.sprite.collide_mask(projectile, player) and 
                    player.invincible_timer == 0 and 
                    not player.god_mode):

                    player.health -= 1
                    player.invincible_timer = 180
                    trigger_screen_shake(8, 15)
                    play_sound_safe(player_hit_sound, "player_hit_sound")
                    projectile.kill()
                    print(f"[PROJECTILE HIT] Player health: {player.health}")

            for enemy in ground_enemy_group:
                if hasattr(enemy, 'state') and enemy.state == "attack":
                    if pygame.sprite.collide_mask(enemy, player) and player.invincible_timer == 0 and not player.god_mode:
                        player.health -= 1
                        player.invincible_timer = 180
                        trigger_screen_shake(8, 15)
                        play_sound_safe(player_hit_sound, "player_hit_sound")
                        print(f"[{enemy.__class__.__name__} HIT] Player health: {player.health}")

            for enemy in flying_enemy_group:
                if isinstance(enemy, RocketEnemy):
                    if enemy.state == "attack":
                        if pygame.sprite.collide_mask(enemy, player) and player.invincible_timer == 0 and not player.god_mode:
                            player.health -= 1
                            player.invincible_timer = 180
                            trigger_screen_shake(8, 15)
                            play_sound_safe(player_hit_sound, "player_hit_sound")
                            enemy.reset_to_hover()
                            print(f"[ROCKET HIT] Player health: {player.health}")
                elif isinstance(enemy, Bat):
                    if pygame.sprite.collide_mask(enemy, player) and player.invincible_timer == 0 and not player.god_mode:
                        player.health -= 1
                        player.invincible_timer = 180
                        trigger_screen_shake(8, 15)
                        play_sound_safe(player_hit_sound, "player_hit_sound")
                        print(f"[BAT HIT] Player health: {player.health}")
                elif isinstance(enemy, Reaper):
                    if enemy.state == "attack":
                        if pygame.sprite.collide_mask(enemy, player) and player.invincible_timer == 0 and not player.god_mode:
                            player.health -= 1
                            player.invincible_timer = 180
                            trigger_screen_shake(8, 15)
                            play_sound_safe(player_hit_sound, "player_hit_sound")
                            print(f"[REAPER HIT] Player health: {player.health}")
                elif isinstance(enemy, DragonBoss):
                    if enemy.state == "attack":
                        if pygame.sprite.collide_mask(enemy, player) and player.invincible_timer == 0 and not player.god_mode:
                            player.health -= enemy.attack_damage
                            player.invincible_timer = 180
                            trigger_screen_shake(15, 25)
                            play_sound_safe(player_hit_sound, "player_hit_sound")
                            print(f"[DRAGON BOSS HIT] Player health: {player.health}")

            for enemy in ground_enemy_group:
                if enemy.health <= 0:
                    enemy.kill()
            for enemy in flying_enemy_group:
                if enemy.health <= 0:
                    enemy.kill()

            if player.health <= 0:
                final_wave = wave_system.current_wave
                final_score = score_system.get_final_score()
                current_game_state = NAME_ENTRY
                stop_music()
                boss_music_playing = False
                print(f"[GAME OVER] Final Score: {final_score}, Wave: {final_wave}")

            draw_background()
            
            pygame.draw.line(screen, (100, 100, 100), (0, GROUND_LEVEL), (WIDTH, GROUND_LEVEL), 2)
            
            for sprite in all_sprites:
                screen.blit(sprite.image, (sprite.rect.x + screen_offset_x, sprite.rect.y + screen_offset_y))
            
            for bullet in bullet_group:
                screen.blit(bullet.image, (bullet.rect.x + screen_offset_x, bullet.rect.y + screen_offset_y))
            
            for projectile in enemy_projectile_group:
                screen.blit(projectile.image, (projectile.rect.x + screen_offset_x, projectile.rect.y + screen_offset_y))

            # Use custom fonts for in-game UI
            font = CUSTOM_FONT_REGULAR
            small_font = CUSTOM_FONT_SMALL

            # Use custom fonts for in-game UI
            font = CUSTOM_FONT_REGULAR
            small_font = CUSTOM_FONT_SMALL

            ui_y_position = HEIGHT - BACKGROUND_MARGIN_BOTTOM + 10

            health_text = font.render(f"HP: {player.health}/{player.max_health}", True, (255, 255, 255))
            screen.blit(health_text, (20, ui_y_position))

            wave_text = font.render(f"Wave: {wave_system.current_wave}", True, (255, 255, 255))
            screen.blit(wave_text, (200, ui_y_position))

            if gun.current_gun == "ak":
                ammo_color = (255, 220, 100) if gun.ak_ammo > 0 else (255, 100, 100)
                ammo_text = font.render(f"AK: {gun.ak_ammo}", True, ammo_color)
            elif gun.current_gun == "shotgun":
                ammo_color = (255, 140, 0) if gun.shotgun_ammo > 0 else (255, 100, 100)
                ammo_text = font.render(f"SHOTGUN: {gun.shotgun_ammo}", True, ammo_color)
            else:
                ammo_text = font.render("PISTOL: infinite", True, (200, 200, 255))
            screen.blit(ammo_text, (350, ui_y_position))

            enemies_left = max(0, (wave_system.wave_enemies_total - wave_system.wave_enemies_spawned) + 
                            len(ground_enemy_group) + len(flying_enemy_group))
            enemy_text = font.render(f"Enemies: {enemies_left}/{wave_system.wave_enemies_total}", True, (255, 255, 255))
            screen.blit(enemy_text, (WIDTH - 220, ui_y_position))

            if DEBUG_START_WAVE > 1:
                debug_text = small_font.render(f"DEBUG: Started from wave {DEBUG_START_WAVE}", True, (255, 255, 0))
                screen.blit(debug_text, (WIDTH - debug_text.get_width() - 10, 50))

            if wave_system.wave_state == "break":
                break_time_left = (wave_system.break_duration - wave_system.break_timer) // 60 + 1
                
                # Make the rectangle wider to fit the text better
                countdown_bg = pygame.Surface((400, 80))  # Increased from 300 to 400
                countdown_bg.set_alpha(180)
                countdown_bg.fill((0, 0, 0))
                screen.blit(countdown_bg, (WIDTH//2 - 200, HEIGHT//2 - 40))  # Adjusted center position
                
                large_font = CUSTOM_FONT_TITLE
                state_text = large_font.render(f"Next Wave: {break_time_left}", True, (255, 255, 0))
                screen.blit(state_text, (WIDTH//2 - state_text.get_width()//2, HEIGHT//2 - 20))
                
                if wave_system.is_boss_wave():
                    preview_text = font.render(f"BOSS INCOMING!", True, (255, 50, 50))
                    screen.blit(preview_text, (WIDTH//2 - preview_text.get_width()//2, HEIGHT//2 - 80))
                else:
                    preview_text = font.render("Get Ready!", True, (0, 255, 255))  # Changed to cyan color
                    screen.blit(preview_text, (WIDTH//2 - preview_text.get_width()//2, HEIGHT//2 - 80))
                        
            elif wave_system.is_boss_wave():
                boss_text = font.render("BOSS WAVE!", True, (255, 50, 50))
                screen.blit(boss_text, (WIDTH//2 - boss_text.get_width()//2, 20))

            if show_stats:
                stats_bg = pygame.Surface((200, 160))
                stats_bg.set_alpha(180)
                stats_bg.fill((0, 0, 0))
                screen.blit(stats_bg, (10, 10))
                
                stats_y = 15
                ground_count_text = small_font.render(f"Ground: {len(ground_enemy_group)}", True, (255, 255, 255))
                screen.blit(ground_count_text, (15, stats_y))
                
                stats_y += 25
                flying_count_text = small_font.render(f"Flying: {len(flying_enemy_group)}", True, (255, 255, 255))
                screen.blit(flying_count_text, (15, stats_y))
                
                stats_y += 25
                ally_status = f"Ally: {ally.combo_state.upper()}"
                ally_text = small_font.render(ally_status, True, (100, 255, 100))
                screen.blit(ally_text, (15, stats_y))
                
                stats_y += 25
                platform_text = small_font.render(f"Platform: {'ON' if player.on_platform else 'OFF'}", True, (200, 200, 100))
                screen.blit(platform_text, (15, stats_y))
                
                stats_y += 25
                god_mode_text = small_font.render(f"GOD MODE: {'ON' if player.god_mode else 'OFF'}", True, (255, 255, 0) if player.god_mode else (255, 255, 255))
                screen.blit(god_mode_text, (15, stats_y))
                
                stats_y += 25
                stats_hint = small_font.render("Press M to hide stats", True, (150, 150, 150))
                screen.blit(stats_hint, (15, stats_y))
            

            escape_hint = small_font.render("Press ESC to return to menu", True, (150, 150, 150))
            screen.blit(escape_hint, (WIDTH - escape_hint.get_width() - 15, 15))

            if show_hitboxes:
                for sprite in list(all_sprites) + list(bullet_group) + list(enemy_projectile_group):
                    if hasattr(sprite, "mask") and sprite.mask:
                        outline = sprite.mask.outline()
                        if outline and len(outline) >= 2:
                            outline_points = [(p[0] + sprite.rect.left + screen_offset_x, p[1] + sprite.rect.top + screen_offset_y)
                                              for p in outline]
                            pygame.draw.lines(screen, (255, 0, 0), True, outline_points, 2)
                    pygame.draw.rect(screen, (0, 255, 0), (sprite.rect.x + screen_offset_x, sprite.rect.y + screen_offset_y, sprite.rect.width, sprite.rect.height), 1)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())