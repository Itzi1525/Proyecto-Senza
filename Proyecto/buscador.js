document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const productCards = document.querySelectorAll('.product-card');

  // Si estamos en la página de Inicio
  if (searchInput && window.location.pathname.includes('Inicio.html')) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
          window.location.href = `03-productos.html?search=${encodeURIComponent(searchTerm)}`;
        }
      }
    });
  }

  // Si estamos en la página de Productos
  if (searchInput && window.location.pathname.includes('03-productos.html')) {
    // Filtrado mientras escribes
    searchInput.addEventListener('keyup', () => {
      const searchTerm = searchInput.value.toLowerCase();
      productCards.forEach(card => {
        const productName = card.dataset.name.toLowerCase();
        card.classList.toggle('hidden', !productName.includes(searchTerm));
      });
    });

    // Filtrado automático si viene de Inicio con parámetro
    const params = new URLSearchParams(window.location.search);
    const term = params.get('search');
    if (term) {
      searchInput.value = term;
      searchInput.dispatchEvent(new Event('keyup'));
    }
  }
});



