// ===== GAMES DATABASE =====
const gamesDatabase = [
    {
        id: 'inscriptionReloaded',
        name: 'Inscription Reloaded',
        description: 'Defeat the enemy for every wave be the longest survivor to be the Top of the Leaderboard',
        icon: 'gameIcon/inscriptionReloaded_icon.png',
        banner: 'gameBanners/inscriptionReloaded_Banner.png',
        instructions: 'WASD to move, Left Click to Shoot',
        category: 'Arcade',
        file: 'gamePages/inscriptionReloaded/inscriptionReloadedframe.html'
    },
    {
        id: 'cappuciNyaa',
        name: 'CappuciNyaa~',
        description: 'Serve with loving paws. Open the Cafe and test your skills. Make all your Cats Customers leave satisfied. ',
        icon: 'gameIcon/cappuciNyaa_Icon.png',
        banner: 'gameBanners/cappuciNyaa_Banner.png',
        instructions: 'Press Left Click for everything. Hold Click to Drag, release to Drop.',
        category: 'Cafe Simulator',
        file: 'gamePages/gameTwo/gameTwoFrame.html'
    }
];

// ===== SEARCH AND FILTER FUNCTIONALITY =====
let currentSearchTerm = '';
let selectedCategories = [];
let searchTimeout = null;

function initializeSearch() {
    const searchInput = document.getElementById('gameSearch');
    const clearSearchBtn = document.getElementById('clearSearch');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const resultsInfo = document.getElementById('searchResultsInfo');

    if (!searchInput || !clearSearchBtn || !clearFiltersBtn || !resultsInfo) return;

    // Search input event with debouncing
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.trim().toLowerCase();
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Add loading state
        addSearchLoadingState();
        
        // Set new timeout for smooth filtering
        searchTimeout = setTimeout(() => {
            currentSearchTerm = searchTerm;
            filterGamesWithAnimation();
            updateClearButton();
            updateResultsInfo();
        }, 300);
    });

    // Clear search button
    clearSearchBtn.addEventListener('click', function() {
        searchInput.value = '';
        currentSearchTerm = '';
        filterGamesWithAnimation();
        updateClearButton();
        updateResultsInfo();
        searchInput.focus();
        addClearAnimation();
    });

    // Clear all filters button
    clearFiltersBtn.addEventListener('click', function() {
        selectedCategories = [];
        updateFilterChips();
        filterGamesWithAnimation();
        updateResultsInfo();
        addClearAnimation();
    });

    // Escape key to clear search
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            searchInput.value = '';
            currentSearchTerm = '';
            filterGamesWithAnimation();
            updateClearButton();
            updateResultsInfo();
            addClearAnimation();
        }
    });

    // Focus effects
    searchInput.addEventListener('focus', function() {
        document.querySelector('.search-box').classList.add('search-focused');
    });
    
    searchInput.addEventListener('blur', function() {
        document.querySelector('.search-box').classList.remove('search-focused');
    });

    // Initialize filter chips
    initializeFilterChips();

    // Initial state
    updateClearButton();
}

function initializeFilterChips() {
    const filterChipsContainer = document.getElementById('filterChips');
    if (!filterChipsContainer) return;

    // Get unique categories from games database
    const categories = [...new Set(gamesDatabase.map(game => game.category))];
    
    // Sort categories alphabetically, but put "TBA" at the end
    categories.sort((a, b) => {
        if (a === 'TBA') return 1;
        if (b === 'TBA') return -1;
        return a.localeCompare(b);
    });

    // Generate filter chips
    filterChipsContainer.innerHTML = categories.map(category => `
        <button class="filter-chip" data-category="${category}" aria-label="Filter by ${category}">
            <span class="chip-text">${category}</span>
            <span class="chip-count" id="count-${category.replace(/\s+/g, '-').toLowerCase()}">0</span>
        </button>
    `).join('');

    // Add event listeners to filter chips
    const filterChips = filterChipsContainer.querySelectorAll('.filter-chip');
    filterChips.forEach(chip => {
        chip.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            toggleCategoryFilter(category);
            filterGamesWithAnimation();
            updateResultsInfo();
        });
    });

    // Update chip counts
    updateFilterChipCounts();
}

function toggleCategoryFilter(category) {
    const chip = document.querySelector(`.filter-chip[data-category="${category}"]`);
    
    if (selectedCategories.includes(category)) {
        // Remove category
        selectedCategories = selectedCategories.filter(cat => cat !== category);
        chip.classList.remove('active');
    } else {
        // Add category
        selectedCategories.push(category);
        chip.classList.add('active');
    }
    
    // Update clear filters button visibility
    updateClearFiltersButton();
}

function updateFilterChips() {
    const filterChips = document.querySelectorAll('.filter-chip');
    filterChips.forEach(chip => {
        const category = chip.getAttribute('data-category');
        if (selectedCategories.includes(category)) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
    updateClearFiltersButton();
}

function updateFilterChipCounts() {
    const categories = [...new Set(gamesDatabase.map(game => game.category))];
    
    categories.forEach(category => {
        const count = gamesDatabase.filter(game => game.category === category).length;
        const countElement = document.getElementById(`count-${category.replace(/\s+/g, '-').toLowerCase()}`);
        if (countElement) {
            countElement.textContent = count;
        }
    });
}

function updateClearFiltersButton() {
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        if (selectedCategories.length > 0) {
            clearFiltersBtn.style.display = 'block';
            clearFiltersBtn.style.animation = 'bounceIn 0.3s ease forwards';
        } else {
            clearFiltersBtn.style.animation = 'fadeOut 0.2s ease forwards';
            setTimeout(() => {
                clearFiltersBtn.style.display = 'none';
            }, 200);
        }
    }
}

function filterGamesWithAnimation() {
    const gamesGrid = document.getElementById('gamesGrid');
    if (!gamesGrid) return;

    const filteredGames = gamesDatabase.filter(game => {
        // Text search filter
        const matchesSearch = !currentSearchTerm || 
            game.name.toLowerCase().includes(currentSearchTerm) ||
            game.description.toLowerCase().includes(currentSearchTerm) ||
            game.category.toLowerCase().includes(currentSearchTerm);
        
        // Category filter
        const matchesCategory = selectedCategories.length === 0 || 
            selectedCategories.includes(game.category);
        
        return matchesSearch && matchesCategory;
    });

    // Add transition class for smooth animations
    gamesGrid.classList.add('grid-transitioning');
    
    // Small delay to allow CSS transition to start
    setTimeout(() => {
        safeGenerateGameCardsWithAnimation(filteredGames);
    }, 50);
}

function safeGenerateGameCardsWithAnimation(gamesToShow = null) {
    try {
        const grid = document.getElementById('gamesGrid');
        if (!grid) return;

        console.log('🎮 Generating game cards with animation...');
        
        // Store current scroll position to maintain it after animation
        const scrollPos = window.scrollY;
        
        // Add fade out effect to existing cards
        const existingCards = grid.querySelectorAll('.features__card');
        existingCards.forEach((card, index) => {
            card.style.animation = `slideOutLeft 0.3s ease forwards ${index * 0.05}s`;
        });

        // Wait for fade out to complete before updating content
        setTimeout(() => {
            grid.innerHTML = '';
            
            const games = gamesToShow || gamesDatabase;
            
            if (games.length === 0) {
                grid.innerHTML = `
                    <div class="no-games-found" style="grid-column: 1 / -1; text-align: center; padding: 3rem; animation: fadeInUp 0.5s ease forwards;">
                        <i class="fas fa-gamepad" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                        <h3 style="color: var(--text-secondary); font-family: 'Press Start 2P', cursive; margin-bottom: 1rem;">No Games Found</h3>
                        <p style="color: var(--text-secondary);">Try adjusting your search terms or filters</p>
                    </div>
                `;
            } else {
                games.forEach((game, index) => {
                    const cardLink = document.createElement('a');
                    cardLink.href = game.file;
                    cardLink.className = 'features__card';
                    cardLink.style.animation = `slideInUp 0.5s ease forwards ${index * 0.1}s`;
                    cardLink.style.opacity = '0';
                    cardLink.style.transform = 'translateY(20px)';
                    
                    cardLink.innerHTML = `
                        <img src="${game.icon}" alt="${game.name}" onerror="console.log('❌ Icon failed to load:', this.src)">
                        <h2>${game.name}</h2>
                        <p>${game.description}</p>
                        <div class="game-category">${game.category}</div>
                    `;
                    grid.appendChild(cardLink);
                });
            }
            
            // Remove transitioning class after animation completes
            setTimeout(() => {
                grid.classList.remove('grid-transitioning');
                // Restore scroll position
                window.scrollTo(0, scrollPos);
            }, games.length * 100 + 500);
            
            console.log('✅ Game cards generated with animation');
        }, existingCards.length * 50 + 200);
        
    } catch (error) {
        console.error('💥 Game cards error:', error);
        grid.classList.remove('grid-transitioning');
    }
}

function addSearchLoadingState() {
    const searchBox = document.querySelector('.search-box');
    if (searchBox && !searchBox.classList.contains('search-loading')) {
        searchBox.classList.add('search-loading');
        
        setTimeout(() => {
            searchBox.classList.remove('search-loading');
        }, 300);
    }
}

function addClearAnimation() {
    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        searchBox.classList.add('search-cleared');
        setTimeout(() => {
            searchBox.classList.remove('search-cleared');
        }, 500);
    }
}

function updateClearButton() {
    const clearSearchBtn = document.getElementById('clearSearch');
    if (clearSearchBtn) {
        if (currentSearchTerm) {
            clearSearchBtn.style.display = 'flex';
            clearSearchBtn.style.animation = 'bounceIn 0.3s ease forwards';
        } else {
            clearSearchBtn.style.animation = 'fadeOut 0.2s ease forwards';
            setTimeout(() => {
                clearSearchBtn.style.display = 'none';
            }, 200);
        }
    }
}

function updateResultsInfo() {
    const resultsInfo = document.getElementById('searchResultsInfo');
    if (!resultsInfo) return;

    const totalGames = gamesDatabase.length;
    const filteredGames = getFilteredGames().length;

    // Add animation
    resultsInfo.style.animation = 'textPulse 0.3s ease';
    
    setTimeout(() => {
        if (currentSearchTerm || selectedCategories.length > 0) {
            if (filteredGames === 0) {
                let message = 'No games found';
                if (currentSearchTerm && selectedCategories.length > 0) {
                    message = `No games found for "${currentSearchTerm}" in selected categories`;
                } else if (currentSearchTerm) {
                    message = `No games found for "${currentSearchTerm}"`;
                } else if (selectedCategories.length > 0) {
                    message = 'No games found in selected categories';
                }
                resultsInfo.textContent = message;
                resultsInfo.classList.add('no-results');
            } else {
                let message = `Showing ${filteredGames} of ${totalGames} games`;
                if (currentSearchTerm && selectedCategories.length > 0) {
                    message = `Showing ${filteredGames} of ${totalGames} games for "${currentSearchTerm}" in selected categories`;
                } else if (currentSearchTerm) {
                    message = `Showing ${filteredGames} of ${totalGames} games for "${currentSearchTerm}"`;
                } else if (selectedCategories.length > 0) {
                    message = `Showing ${filteredGames} of ${totalGames} games in selected categories`;
                }
                resultsInfo.textContent = message;
                resultsInfo.classList.remove('no-results');
            }
        } else {
            resultsInfo.textContent = `Showing all ${totalGames} games`;
            resultsInfo.classList.remove('no-results');
        }
        
        setTimeout(() => {
            resultsInfo.style.animation = '';
        }, 300);
    }, 150);
}

function getFilteredGames() {
    return gamesDatabase.filter(game => {
        const matchesSearch = !currentSearchTerm || 
            game.name.toLowerCase().includes(currentSearchTerm) ||
            game.description.toLowerCase().includes(currentSearchTerm) ||
            game.category.toLowerCase().includes(currentSearchTerm);
        
        const matchesCategory = selectedCategories.length === 0 || 
            selectedCategories.includes(game.category);
        
        return matchesSearch && matchesCategory;
    });
}

// SAFE banner generation - UPDATED WITH DIRECT ONCLICK
function safeGenerateBanners() {
    try {
        const carousel = document.getElementById('bannerCarousel');
        if (!carousel) {
            console.error('❌ Banner carousel element not found!');
            return;
        }
        
        console.log('🖼️ Safely generating banners...');
        carousel.innerHTML = '';
        
        gamesDatabase.forEach((game, index) => {
            const slide = document.createElement('div');
            slide.className = `banner-slide ${index === 0 ? 'active' : ''}`;
            
            slide.innerHTML = `
                <div class="banner-content">
                    <div class="banner-text">
                        <h2>${game.name}</h2>
                        <p>${game.description}</p>
                        <button class="banner-btn pixel-button" onclick="window.location.href='${game.file}'">
                            Play Now
                        </button>
                    </div>
                    <div class="banner-image">
                        <img src="${game.banner}" alt="${game.name}" onerror="console.log('❌ Banner image failed to load:', this.src)">
                    </div>
                </div>
            `;
            carousel.appendChild(slide);
        });
        
        console.log('✅ Banners generated with onclick handlers');
    } catch (error) {
        console.error('💥 Banner generation error:', error);
    }
}

// SAFE banner carousel
let safeBannerInterval;
function safeStartBannerCarousel() {
    if (safeBannerInterval) clearInterval(safeBannerInterval);
    
    safeBannerInterval = setInterval(() => {
        const slides = document.querySelectorAll('.banner-slide');
        if (slides.length > 0) {
            const currentIndex = Array.from(slides).findIndex(slide => slide.classList.contains('active'));
            const nextIndex = (currentIndex + 1) % slides.length;
            
            slides.forEach(slide => slide.classList.remove('active'));
            slides[nextIndex].classList.add('active');
        }
    }, 5000);
}

// SAFE game cards
function safeGenerateGameCards(gamesToShow = null) {
    try {
        const grid = document.getElementById('gamesGrid');
        if (!grid) return;
        
        console.log('🎮 Safely generating game cards...');
        grid.innerHTML = '';
        
        const games = gamesToShow || gamesDatabase;
        
        if (games.length === 0) {
            grid.innerHTML = `
                <div class="no-games-found" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <i class="fas fa-gamepad" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <h3 style="color: var(--text-secondary); font-family: 'Press Start 2P', cursive; margin-bottom: 1rem;">No Games Found</h3>
                    <p style="color: var(--text-secondary);">Try adjusting your search terms or filters</p>
                </div>
            `;
            return;
        }
        
        games.forEach(game => {
            const cardLink = document.createElement('a');
            cardLink.href = game.file;
            cardLink.className = 'features__card';
            
            cardLink.innerHTML = `
                <img src="${game.icon}" alt="${game.name}" onerror="console.log('❌ Icon failed to load:', this.src)">
                <h2>${game.name}</h2>
                <p>${game.description}</p>
                <div class="game-category">${game.category}</div>
            `;
            grid.appendChild(cardLink);
        });
        
        console.log('✅ Game cards generated safely');
    } catch (error) {
        console.error('💥 Game cards error:', error);
    }
}

// SAFE navbar initialization
function safeInitializeNavbar() {
    const userProfileNav = document.getElementById('userProfileNav');
    if (userProfileNav && !window.location.pathname.includes('profile.html')) {
        userProfileNav.innerHTML = `
            <a href="profile.html" class="navbar__links user-profile-link">
                <i class="fas fa-user"></i> PROFILE
            </a>
        `;
        console.log("✅ Navbar updated safely");
    }
}

// THEME MANAGEMENT
function initializeTheme() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (!themeToggle) return;

    const themeIcon = themeToggle.querySelector('i');
    const savedTheme = localStorage.getItem('gamersDen_theme');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
    }
    
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        
        if (document.body.classList.contains('dark-theme')) {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            localStorage.setItem('gamersDen_theme', 'dark');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            localStorage.setItem('gamersDen_theme', 'light');
        }
    });
}

// UTILITY FUNCTIONS
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// DEBUG FUNCTION - Check if banners are working
function debugBanners() {
    console.log('=== BANNER DEBUG INFO ===');
    console.log('Banner carousel exists:', !!document.getElementById('bannerCarousel'));
    console.log('Banner slides:', document.querySelectorAll('.banner-slide').length);
    console.log('Play Now buttons:', document.querySelectorAll('.banner-btn').length);
    
    const buttons = document.querySelectorAll('.banner-btn');
    buttons.forEach((btn, index) => {
        console.log(`Button ${index}:`, {
            text: btn.textContent,
            onclick: btn.getAttribute('onclick')
        });
    });
    console.log('=== END DEBUG ===');
}

// PAGE INITIALIZATION
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM loaded on:', window.location.pathname);
    
    setTimeout(() => {
        initializePageSafely();
    }, 500);
});

function initializePageSafely() {
    const currentPage = window.location.pathname.split('/').pop();
    console.log('🏠 Initializing page:', currentPage);
    
    initializeTheme();
    safeNavbarFix();
    
    if (currentPage === 'index.html' || currentPage === '') {
        console.log('🏠 Home page - initializing home features');
        initializeHomePage();
    }
    else if (currentPage === 'profile.html') {
        console.log('👤 Profile page - minimal initialization');
    }
    else if (currentPage === 'about.html') {
        console.log('📖 About page - minimal initialization');
    }
    else if (currentPage === 'login.html') {
        console.log('🔐 Login page - minimal initialization');
        initializeLoginPage();
    }
    
    console.log('✅ main.js: Page initialization completed');
}

// SAFE navbar fix (no observers, no nuclear option)
function safeNavbarFix() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.style.backgroundColor = 'var(--dark)';
        navbar.style.background = 'var(--dark)';
        navbar.style.opacity = '1';
        console.log('✅ Navbar safely fixed');
    }
}

// HOME PAGE ONLY
function initializeHomePage() {
    console.log('🏠 Initializing home page features...');
    
    if (document.getElementById('bannerCarousel')) {
        console.log('🖼️ Initializing banner carousel');
        safeGenerateBanners();
        safeStartBannerCarousel();
        
        // Debug: Log all button onclick functions
        setTimeout(() => {
            const buttons = document.querySelectorAll('.banner-btn');
            console.log('🔍 Final check - banner buttons:', buttons.length);
            buttons.forEach((btn, i) => {
                console.log(`Button ${i} onclick:`, btn.getAttribute('onclick'));
            });
        }, 1000);
    }
    
    if (document.getElementById('gamesGrid')) {
        console.log('🎮 Initializing games grid');
        safeGenerateGameCardsWithAnimation();
        initializeSearch();
    }
    
    safeInitializeNavbar();
}

// LOGIN PAGE ONLY
function initializeLoginPage() {
    console.log('🔐 Initializing login page features...');
    
    const authTabs = document.querySelectorAll('.auth-tab');
    const switchLinks = document.querySelectorAll('.switch-link');
    
    authTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchAuthTab(targetTab);
        });
    });
    
    switchLinks.forEach(link => {
        link.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchAuthTab(targetTab);
        });
    });

    const inputs = document.querySelectorAll('.pixel-input');
    inputs.forEach(input => {
        input.addEventListener('focus', addPixelTypingEffect);
        input.addEventListener('blur', removePixelTypingEffect);
        input.addEventListener('input', playTypingSound);
    });
}

// AUTH UI MANAGEMENT
function switchAuthTab(targetTab) {
    const authTabs = document.querySelectorAll('.auth-tab');
    const authForms = document.querySelectorAll('.auth-form');
    
    authTabs.forEach(t => t.classList.remove('active'));
    authForms.forEach(form => form.classList.remove('active'));
    
    document.querySelector(`.auth-tab[data-tab="${targetTab}"]`).classList.add('active');
    document.getElementById(`${targetTab}Form`).classList.add('active');
}

// PIXEL TYPING EFFECTS
function addPixelTypingEffect(e) {
    const input = e.target;
    input.style.fontFamily = "'Press Start 2P', cursive";
    input.style.fontSize = '0.7rem';
    input.style.letterSpacing = '1px';
}

function removePixelTypingEffect(e) {
    const input = e.target;
    if (!input.value) {
        input.style.fontFamily = "'Silkscreen', cursive";
        input.style.fontSize = '';
        input.style.letterSpacing = '';
    }
}

function playTypingSound() {
    console.log('Typing sound would play here');
}

// Call debug after page loads
setTimeout(debugBanners, 2000);