// Обработчик темы
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.querySelector('.theme-toggle');
    const html = document.documentElement;
    
    // Установка начальной темы
    const currentTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', currentTheme);
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
});

// Добавление индексов для анимации элементов выпадающего меню
document.addEventListener('DOMContentLoaded', () => {
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const items = dropdown.querySelectorAll('.dropdown-item');
        items.forEach((item, index) => {
            item.style.setProperty('--item-index', index);
        });
    });
});


// Функция переключения мобильного меню
function toggleMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const menuButton = document.querySelector('.mobile-menu-toggle');
    
    if (mobileMenu.classList.contains('active')) {
        mobileMenu.classList.remove('active');
        menuButton.querySelector('svg').style.transform = 'rotate(0deg)';
    } else {
        mobileMenu.classList.add('active');
        menuButton.querySelector('svg').style.transform = 'rotate(0deg)';
    }
}

// Закрытие меню при клике вне его области
document.addEventListener('click', (e) => {
    const mobileMenu = document.querySelector('.mobile-menu');
    const menuButton = document.querySelector('.mobile-menu-toggle');
    
    if (!e.target.closest('.mobile-menu') && 
        !e.target.closest('.mobile-menu-toggle') && 
        mobileMenu.classList.contains('active')) {
        mobileMenu.classList.remove('active');
        menuButton.querySelector('svg').style.transform = 'rotate(0deg)';
    }
});

// Инициализация индексов для анимации
document.addEventListener('DOMContentLoaded', () => {
    const menuItems = document.querySelectorAll('.mobile-menu-item');
    menuItems.forEach((item, index) => {
        item.style.setProperty('--item-index', index);
    });
});