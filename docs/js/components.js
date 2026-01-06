// Shared UI Components for Buku-Buka

/**
 * Initialize the page header and navigation
 * @param {Object} options
 * @param {string} options.activePage - Current page: 'browse' | 'branches' | 'add-book' | 'my-loans' | 'branch-loans' | 'login'
 * @param {Function} options.onAuthChange - Optional callback when auth state changes
 */
function initHeader(options = {}) {
  const { activePage = '', onAuthChange } = options;

  // Inject header HTML
  const headerHTML = `
    <header>
      <div class="container">
        <a href="index.html" class="logo">
          <img src="assets/logo_icon.png" alt="Buku-Buka">
          <span>Buku-Buka</span>
        </a>
        <nav>
          <a href="index.html" ${activePage === 'browse' ? 'class="active"' : ''}>Browse</a>
          <a href="branches.html" ${activePage === 'branches' ? 'class="active"' : ''}>Branches</a>
          <span id="nav-add-book"></span>
          <span id="nav-auth"></span>
        </nav>
        <button class="nav-toggle" onclick="toggleMobileMenu()" aria-label="Menu">
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </header>
  `;

  // Inject mobile menu HTML
  const mobileMenuHTML = `
    <div id="mobile-menu" class="mobile-menu" onclick="closeMobileMenu(event)">
      <div class="mobile-menu-content" onclick="event.stopPropagation()">
        <button class="mobile-menu-close" onclick="closeMobileMenu()">&times;</button>
        <nav>
          <a href="index.html">Browse</a>
          <a href="branches.html">Branches</a>
          <a href="my-loans.html">My Loans</a>
          <span id="mobile-nav-add-book"></span>
          <span id="mobile-nav-auth"></span>
        </nav>
      </div>
    </div>
  `;

  // Insert at the beginning of body
  document.body.insertAdjacentHTML('afterbegin', mobileMenuHTML);
  document.body.insertAdjacentHTML('afterbegin', headerHTML);

  // Set up auth change listener
  auth.onAuthChange(() => {
    updateNav();
    if (onAuthChange) {
      onAuthChange();
    }
  });
}

/**
 * Toggle mobile menu open
 */
function toggleMobileMenu() {
  document.getElementById('mobile-menu').classList.add('open');
  document.body.style.overflow = 'hidden';
}

/**
 * Close mobile menu
 */
function closeMobileMenu(event) {
  if (event && event.target !== event.currentTarget) return;
  document.getElementById('mobile-menu').classList.remove('open');
  document.body.style.overflow = '';
}

/**
 * Update navigation based on auth state
 */
function updateNav() {
  const navAuth = document.getElementById('nav-auth');
  const mobileNavAuth = document.getElementById('mobile-nav-auth');
  const navAddBook = document.getElementById('nav-add-book');
  const mobileNavAddBook = document.getElementById('mobile-nav-add-book');

  if (auth.isAuthenticated()) {
    navAuth.innerHTML = `
      <div class="user-menu">
        <a href="my-loans.html">My Loans</a>
        <span class="user-name">${auth.user?.name || auth.user?.email}</span>
        <button class="btn btn-secondary btn-sm" onclick="handleSignOut()">Sign Out</button>
      </div>
    `;
    mobileNavAuth.innerHTML = `
      <a href="#" onclick="handleSignOut(); return false;">Sign Out</a>
    `;

    // Show Add Books in nav if user is branch owner
    if (auth.isBranchOwner()) {
      navAddBook.innerHTML = '<a href="add-book.html">Add Books</a>';
      mobileNavAddBook.innerHTML = '<a href="add-book.html">Add Books</a>';
    } else {
      navAddBook.innerHTML = '';
      mobileNavAddBook.innerHTML = '';
    }
  } else {
    navAuth.innerHTML = '<a href="login.html" class="btn btn-primary btn-sm">Sign In</a>';
    mobileNavAuth.innerHTML = '<a href="login.html">Sign In</a>';
    navAddBook.innerHTML = '';
    mobileNavAddBook.innerHTML = '';
  }
}

/**
 * Sign out handler
 */
async function handleSignOut() {
  try {
    await auth.signOut();
    window.location.href = 'index.html';
  } catch (err) {
    showMessage(err.message);
  }
}
