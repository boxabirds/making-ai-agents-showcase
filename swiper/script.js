// Swiper functionality
let currentIndex = 0;
let totalCards = 0;
let isScrolling = false;
let touchStartY = 0;
let touchEndY = 0;

function initSwiper() {
    const track = document.getElementById('swiperTrack');
    const cards = document.querySelectorAll('.card');
    totalCards = cards.length;
    
    // Generate navigation dots
    generateNavDots();
    
    // Set initial state
    updateActiveCard(0);
    
    // Scroll event handling
    let scrollTimeout;
    track.addEventListener('scroll', () => {
        isScrolling = true;
        clearTimeout(scrollTimeout);
        
        scrollTimeout = setTimeout(() => {
            isScrolling = false;
            snapToNearestCard();
        }, 150);
        
        updateProgressBar();
    });
    
    // Touch events for swipe detection
    track.addEventListener('touchstart', handleTouchStart, { passive: true });
    track.addEventListener('touchend', handleTouchEnd, { passive: true });
    
    // Keyboard navigation
    document.addEventListener('keydown', handleKeyboard);
    
    // Click on dots
    document.getElementById('navDots').addEventListener('click', (e) => {
        if (e.target.classList.contains('nav-dot')) {
            const index = parseInt(e.target.dataset.index);
            scrollToCard(index);
        }
    });
    
    // Smooth scroll behavior
    track.style.scrollBehavior = 'smooth';
    
    // Add loading placeholders for images
    cards.forEach((card, index) => {
        const img = card.querySelector('.card-image img');
        if (img && index > 0) { // Skip intro card
            img.addEventListener('load', () => {
                img.parentElement.classList.remove('loading');
            });
            img.parentElement.classList.add('loading');
        }
    });
}

function generateNavDots() {
    const dotsContainer = document.getElementById('navDots');
    const dotsHTML = Array.from({ length: totalCards }, (_, i) => 
        `<div class="nav-dot" data-index="${i}"></div>`
    ).join('');
    dotsContainer.innerHTML = dotsHTML;
}

function updateActiveCard(index) {
    currentIndex = index;
    
    // Update dots
    document.querySelectorAll('.nav-dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
    
    // Update progress
    updateProgressBar();
}

function updateProgressBar() {
    const track = document.getElementById('swiperTrack');
    const scrollPercentage = track.scrollTop / (track.scrollHeight - track.clientHeight);
    const progressFill = document.getElementById('progressFill');
    progressFill.style.width = `${scrollPercentage * 100}%`;
    
    // Update current index based on scroll
    const cardHeight = window.innerHeight;
    const newIndex = Math.round(track.scrollTop / cardHeight);
    if (newIndex !== currentIndex) {
        updateActiveCard(newIndex);
    }
}

function snapToNearestCard() {
    const track = document.getElementById('swiperTrack');
    const cardHeight = window.innerHeight;
    const scrollPosition = track.scrollTop;
    const nearestCard = Math.round(scrollPosition / cardHeight);
    
    if (Math.abs(scrollPosition - nearestCard * cardHeight) > 5) {
        scrollToCard(nearestCard);
    }
}

function scrollToCard(index) {
    if (index < 0 || index >= totalCards) return;
    
    const track = document.getElementById('swiperTrack');
    const cardHeight = window.innerHeight;
    
    track.scrollTo({
        top: index * cardHeight,
        behavior: 'smooth'
    });
    
    updateActiveCard(index);
}

function handleTouchStart(e) {
    touchStartY = e.touches[0].clientY;
}

function handleTouchEnd(e) {
    touchEndY = e.changedTouches[0].clientY;
    handleSwipe();
}

function handleSwipe() {
    const swipeDistance = touchStartY - touchEndY;
    const threshold = 50; // Minimum swipe distance
    
    if (Math.abs(swipeDistance) > threshold) {
        if (swipeDistance > 0) {
            // Swiped up
            scrollToCard(currentIndex + 1);
        } else {
            // Swiped down
            scrollToCard(currentIndex - 1);
        }
    }
}

function handleKeyboard(e) {
    switch(e.key) {
        case 'ArrowDown':
        case ' ': // Spacebar
            e.preventDefault();
            scrollToCard(currentIndex + 1);
            break;
        case 'ArrowUp':
            e.preventDefault();
            scrollToCard(currentIndex - 1);
            break;
        case 'Home':
            e.preventDefault();
            scrollToCard(0);
            break;
        case 'End':
            e.preventDefault();
            scrollToCard(totalCards - 1);
            break;
        case 'PageDown':
            e.preventDefault();
            scrollToCard(Math.min(currentIndex + 5, totalCards - 1));
            break;
        case 'PageUp':
            e.preventDefault();
            scrollToCard(Math.max(currentIndex - 5, 0));
            break;
        default:
            // Number keys for quick navigation
            if (e.key >= '0' && e.key <= '9') {
                const num = parseInt(e.key);
                if (num > 0 && num <= totalCards) {
                    scrollToCard(num - 1);
                } else if (num === 0 && totalCards >= 10) {
                    scrollToCard(9); // 0 goes to card 10
                }
            }
    }
}

// Smooth scroll physics enhancement
let lastScrollTop = 0;
let scrollVelocity = 0;
let animationFrame;

function enhanceScrollPhysics() {
    const track = document.getElementById('swiperTrack');
    
    track.addEventListener('scroll', () => {
        const currentScrollTop = track.scrollTop;
        scrollVelocity = currentScrollTop - lastScrollTop;
        lastScrollTop = currentScrollTop;
        
        // Cancel any ongoing animation
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        
        // Apply momentum when scroll stops
        if (!isScrolling && Math.abs(scrollVelocity) > 5) {
            applyMomentum();
        }
    }, { passive: true });
}

function applyMomentum() {
    const track = document.getElementById('swiperTrack');
    const friction = 0.95;
    const minVelocity = 0.5;
    
    function animate() {
        if (Math.abs(scrollVelocity) > minVelocity) {
            track.scrollTop += scrollVelocity;
            scrollVelocity *= friction;
            animationFrame = requestAnimationFrame(animate);
        } else {
            snapToNearestCard();
        }
    }
    
    animate();
}

// Initialize enhanced physics after swiper is ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(enhanceScrollPhysics, 100);
});