document.addEventListener('DOMContentLoaded', function() {
    // 디바운스 함수
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

    // 테마 관리 모듈
    const ThemeManager = {
        init() {
            try {
                this.themeToggle = document.getElementById('themeToggle');
                if (!this.themeToggle) {
                    console.warn('Theme toggle button not found');
                    return;
                }
                this.setupEventListeners();
                this.loadSavedTheme();
            } catch (error) {
                console.error('Error initializing theme manager:', error);
            }
        },

        setupEventListeners() {
            if (this.themeToggle) {
                this.themeToggle.addEventListener('click', 
                    debounce(() => this.toggleTheme(), 250)
                );
            }

            // 시스템 테마 변경 감지
            try {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                mediaQuery.addEventListener('change', e => this.handleSystemThemeChange(e));
            } catch (error) {
                console.warn('System theme detection not supported:', error);
            }
        },

        loadSavedTheme() {
            try {
                const savedTheme = localStorage.getItem('theme');
                const theme = savedTheme || 'dark';
                this.applyTheme(theme);
            } catch (error) {
                console.error('Error loading saved theme:', error);
            }
        },

        handleSystemThemeChange(e) {
            try {
                if (!localStorage.getItem('theme')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            } catch (error) {
                console.warn('Error handling system theme change:', error);
            }
        },

        toggleTheme() {
            try {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                this.applyTheme(newTheme);
                localStorage.setItem('theme', newTheme);
            } catch (error) {
                console.error('Error toggling theme:', error);
            }
        },

        applyTheme(theme) {
            try {
                document.documentElement.setAttribute('data-theme', theme);
                document.documentElement.style.colorScheme = theme;
                this.updateThemeIcon(theme === 'dark');
            } catch (error) {
                console.error('Error applying theme:', error);
            }
        },

        updateThemeIcon(isDark) {
            try {
                if (this.themeToggle) {
                    const icon = this.themeToggle.querySelector('i');
                    if (icon) {
                        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
                    }
                }
            } catch (error) {
                console.error('Error updating theme icon:', error);
            }
        }
    };

    // 테마 매니저 초기화
    try {
        ThemeManager.init();
    } catch (error) {
        console.error('Failed to initialize theme manager:', error);
    }
}); 