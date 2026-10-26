/**
 * Brofessor Core Interactive Utilities
 * Minimal, fast vanilla JavaScript for notifications, modals, and responsive shell.
 */

// CSRF helper for Django POST requests
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

window.getCsrfToken = function() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');
  return getCookie('csrftoken') || '';
};

// Toast Notifications System
window.BrofessorToast = {
  show: function(message, type = 'info', duration = 3500) {
    const container = document.getElementById('brofessor-toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg border text-sm shadow-md transition-all duration-200 transform translate-y-2 opacity-0 select-none`;

    // Type styles
    let typeClasses = 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 border-zinc-200 dark:border-zinc-800';
    let iconSvg = '';

    if (type === 'success') {
      typeClasses = 'bg-white dark:bg-zinc-900 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60';
      iconSvg = `<svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
    } else if (type === 'error' || type === 'danger') {
      typeClasses = 'bg-white dark:bg-zinc-900 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800/60';
      iconSvg = `<svg class="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
    } else if (type === 'warning') {
      typeClasses = 'bg-white dark:bg-zinc-900 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800/60';
      iconSvg = `<svg class="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`;
    } else {
      iconSvg = `<svg class="w-4 h-4 text-indigo-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
    }

    toast.className += ` ${typeClasses}`;
    toast.innerHTML = `
      ${iconSvg}
      <span class="flex-1 font-medium">${message}</span>
      <button onclick="this.parentElement.remove()" class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 ml-2">
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Auto dismiss
    if (duration > 0) {
      setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 250);
      }, duration);
    }
  }
};

// Modal System
window.BrofessorModal = {
  open: function(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
    const backdrop = modal.querySelector('[data-modal-backdrop]');
    const content = modal.querySelector('[data-modal-content]');
    if (backdrop) backdrop.classList.remove('opacity-0');
    if (content) content.classList.remove('scale-95', 'opacity-0');
  },
  close: function(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    const backdrop = modal.querySelector('[data-modal-backdrop]');
    const content = modal.querySelector('[data-modal-content]');
    if (backdrop) backdrop.classList.add('opacity-0');
    if (content) content.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
      modal.classList.add('hidden');
      document.body.classList.remove('overflow-hidden');
    }, 150);
  }
};

// Toggle mobile navigation sidebar drawer
window.toggleMobileNav = function() {
  const drawer = document.getElementById('mobile-sidebar');
  const backdrop = document.getElementById('mobile-sidebar-backdrop');
  if (!drawer) return;

  const isHidden = drawer.classList.contains('-translate-x-full');
  if (isHidden) {
    drawer.classList.remove('-translate-x-full');
    if (backdrop) backdrop.classList.remove('hidden');
  } else {
    drawer.classList.add('-translate-x-full');
    if (backdrop) backdrop.classList.add('hidden');
  }
};

// Close mobile nav on escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const mobileDrawer = document.getElementById('mobile-sidebar');
    if (mobileDrawer && !mobileDrawer.classList.contains('-translate-x-full')) {
      window.toggleMobileNav();
    }
    // Close open modals
    document.querySelectorAll('[data-modal-dialog]:not(.hidden)').forEach(modal => {
      window.BrofessorModal.close(modal.id);
    });
  }
});
