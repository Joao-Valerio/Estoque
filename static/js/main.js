// StockBot - Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// ==================== APP ====================

function initializeApp() {

    initializeSidebar();

    initializeTooltips();

    initializeNotifications();

    initializeSearch();

    initializeAnimations();

    initializeHeader();

}

// ==================== SIDEBAR ====================

function syncSidebarMenuButton() {
    const sidebar = document.getElementById('sidebar');
    const btn = document.getElementById('sidebar-menu-btn');
    if (!btn || !sidebar) return;
    const closed = sidebar.classList.contains('-translate-x-full');
    btn.setAttribute('aria-expanded', closed ? 'false' : 'true');
}

function initializeSidebar() {
    const overlay = document.getElementById('sidebar-overlay');
    const menuBtn = document.getElementById('sidebar-menu-btn');

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    if (menuBtn) {
        menuBtn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleSidebar();
        });
    }

    document.querySelectorAll('.sidebar-link').forEach((link) => {
        link.addEventListener('click', () => {
            closeSidebar();
        });
    });

    syncSidebarMenuButton();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    sidebar.classList.toggle('-translate-x-full');
    document.getElementById('sidebar-overlay')?.classList.toggle('hidden');

    syncSidebarMenuButton();
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    sidebar.classList.add('-translate-x-full');
    document.getElementById('sidebar-overlay')?.classList.add('hidden');

    syncSidebarMenuButton();
}

// ==================== HEADER ====================

function initializeHeader() {
    const header = document.getElementById('dashboard-header');
    const scrollRoot = document.getElementById('main-scroll-region');
    if (!header || !scrollRoot) return;

    let lastScrollTop = scrollRoot.scrollTop;
    let ticking = false;

    const apply = () => {
        ticking = false;
        const current = scrollRoot.scrollTop;
        const hide =
            current > lastScrollTop && current > 48;
        if (hide) {
            header.style.maxHeight = '0';
            header.style.opacity = '0';
            header.style.pointerEvents = 'none';
            header.style.borderColor = 'transparent';
        } else {
            header.style.maxHeight = '';
            header.style.opacity = '';
            header.style.pointerEvents = '';
            header.style.borderColor = '';
        }
        lastScrollTop = current;
    };

    scrollRoot.addEventListener(
        'scroll',
        () => {
            if (!ticking) {
                ticking = true;
                requestAnimationFrame(apply);
            }
        },
        { passive: true }
    );
}

// ==================== TOOLTIPS ====================

function initializeTooltips() {

    // Tooltips via CSS

}

// ==================== NOTIFICATIONS ====================

function initializeNotifications() {

    const notificationBtn =
        document.querySelector(
            'button:has(ion-icon[name="notifications"])'
        );

    if (!notificationBtn) return;

    notificationBtn.addEventListener(
        'click',
        showNotifications
    );

}

function showNotifications() {

    console.log('Notificações clicadas');

}

// ==================== SEARCH ====================

function initializeSearch() {

    const searchInput =
        document.querySelector(
            'input[placeholder*="Buscar"]'
        );

    if (!searchInput) return;

    searchInput.addEventListener(
        'input',
        debounce(handleSearch, 300)
    );

}

function handleSearch(e) {

    const query = e.target.value.toLowerCase();

    if (query.length < 2) {

        clearSearchResults();

        return;

    }

    console.log('Buscando:', query);

}

function clearSearchResults() {

    console.log('Limpar busca');

}

// ==================== ANIMATIONS ====================

function initializeAnimations() {

    const cards = document.querySelectorAll('.card');

    cards.forEach((card, index) => {

        card.style.animationDelay = `${index * 0.1}s`;

        card.classList.add('animate-fade-in');

    });

}

// ==================== UTILS ====================

function debounce(func, wait) {

    let timeout;

    return function executedFunction(...args) {

        const later = () => {

            clearTimeout(timeout);

            func(...args);

        };

        clearTimeout(timeout);

        timeout = setTimeout(later, wait);

    };

}

function showToast(message, type = 'info', duration = 3000) {

    const toast = document.createElement('div');

    toast.className = `
        fixed bottom-4 right-4
        z-50 rounded-xl px-6 py-3
        text-white shadow-lg
        animate-slide-up
    `;

    switch (type) {

        case 'success':
            toast.classList.add('bg-green-600');
            break;

        case 'error':
            toast.classList.add('bg-red-600');
            break;

        case 'warning':
            toast.classList.add('bg-yellow-600');
            break;

        default:
            toast.classList.add('bg-blue-600');

    }

    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.classList.remove('animate-slide-up');

        toast.classList.add('animate-fade-out');

        setTimeout(() => {

            toast.remove();

        }, 300);

    }, duration);

}

function confirmAction(message, callback) {

    if (confirm(message)) {

        callback();

    }

}

function formatCurrency(value) {

    return new Intl.NumberFormat('pt-BR', {

        style: 'currency',

        currency: 'BRL'

    }).format(value);

}

function formatDate(date) {

    return new Intl.DateTimeFormat('pt-BR', {

        year: 'numeric',

        month: 'long',

        day: 'numeric'

    }).format(new Date(date));

}

// ==================== EXPORT ====================

window.toggleSidebar = toggleSidebar;

window.closeSidebar = closeSidebar;

window.StockBot = {

    toggleSidebar,

    closeSidebar,

    showToast,

    confirmAction,

    formatCurrency,

    formatDate

};