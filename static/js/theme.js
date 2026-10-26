/**
 * Brofessor Theme Manager
 * Fast, anti-flash theme toggling with localStorage persistence & system preference support.
 */
(function() {
  const STORAGE_KEY = 'brofessor-theme';

  function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function applyTheme(theme) {
    const root = document.documentElement;
    const isDark = theme === 'dark' || (theme === 'system' && getSystemTheme() === 'dark') || (!theme && getSystemTheme() === 'dark');

    if (isDark) {
      root.classList.add('dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.style.colorScheme = 'light';
    }

    // Update icons if buttons exist
    updateToggleIcons(isDark);
  }

  function updateToggleIcons(isDark) {
    document.querySelectorAll('[data-theme-icon-sun]').forEach(el => {
      el.classList.toggle('hidden', !isDark);
    });
    document.querySelectorAll('[data-theme-icon-moon]').forEach(el => {
      el.classList.toggle('hidden', isDark);
    });
  }

  window.BrofessorTheme = {
    get: function() {
      return getSavedTheme() || 'system';
    },
    isDark: function() {
      return document.documentElement.classList.contains('dark');
    },
    set: function(theme) {
      try {
        localStorage.setItem(STORAGE_KEY, theme);
      } catch (e) {}
      applyTheme(theme);
    },
    toggle: function() {
      const currentIsDark = document.documentElement.classList.contains('dark');
      const nextTheme = currentIsDark ? 'light' : 'dark';
      this.set(nextTheme);
      return nextTheme;
    }
  };

  // Listen to system preference changes if user hasn't set an explicit override
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (!getSavedTheme() || getSavedTheme() === 'system') {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });

  // Apply on DOMContentLoaded to sync icons
  document.addEventListener('DOMContentLoaded', function() {
    updateToggleIcons(document.documentElement.classList.contains('dark'));
  });
})();
