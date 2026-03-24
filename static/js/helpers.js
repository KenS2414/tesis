// Small helpers used across the app

// Clear a form inputs (only text/select/textarea) without submitting
function clearFilters(formSelector){
  const form = document.querySelector(formSelector);
  if(!form) return;
  Array.from(form.elements).forEach(el => {
    if(el.tagName === 'INPUT'){
      const t = el.type.toLowerCase();
      if(t === 'text' || t === 'search' || t === 'email' || t === 'number' || t === 'hidden') el.value = '';
      if(t === 'checkbox' || t === 'radio') el.checked = false;
    } else if(el.tagName === 'SELECT'){
      el.selectedIndex = 0;
    } else if(el.tagName === 'TEXTAREA'){
      el.value = '';
    }
  });
  // visual feedback: briefly highlight the form
  form.classList.add('filter-cleared');
  setTimeout(() => form.classList.remove('filter-cleared'), 1000);
}

// Attach clear handler to elements with data-clear-target attribute
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-clear-target]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const selector = btn.getAttribute('data-clear-target');
      // optional confirmation
      const confirmMsg = btn.getAttribute('data-clear-confirm');
      if(confirmMsg){
        if(!window.confirm(confirmMsg)) return;
      }
      clearFilters(selector);
      // announce via ARIA live region if present
      const live = document.getElementById('aria-live');
      if(live){
        live.textContent = btn.getAttribute('data-clear-announcement') || 'Filtros borrados';
      }
    });
  });
});

// Compatibility fix: ensure legacy brand text is replaced
document.addEventListener('DOMContentLoaded', () => {
  try {
    const brandEls = document.querySelectorAll('.brand, .navbar-brand');
    brandEls.forEach(el => {
      if (el.textContent && el.textContent.trim().toLowerCase() === 'colegio') {
        el.textContent = 'La Salle Tienda Honda';
      }
    });
  } catch (e) {
    // no-op
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const hideFlash = (flash) => {
    if (!flash || flash.classList.contains('is-hiding')) return;
    flash.classList.add('is-hiding');
    window.setTimeout(() => flash.remove(), 250);
  };

  document.querySelectorAll('[data-flash]').forEach((flash) => {
    const closeButton = flash.querySelector('[data-flash-close]');
    if (closeButton) {
      closeButton.addEventListener('click', () => hideFlash(flash));
    }

    window.setTimeout(() => hideFlash(flash), 2000);
  });
});
