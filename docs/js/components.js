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
          <a href="index.html" ${activePage === 'browse' ? 'class="active"' : ''}>Discover</a>
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
        <div id="mobile-welcome" class="mobile-welcome"></div>
        <nav>
          <a href="index.html">Discover</a>
          <a href="branches.html">Branches</a>
          <a href="my-loans.html">My Loans</a>
          <span id="mobile-nav-add-book"></span>
        </nav>
        <div id="mobile-nav-auth" class="mobile-menu-footer"></div>
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

  // Initialize nav state immediately
  updateNav();
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
  const mobileWelcome = document.getElementById('mobile-welcome');
  const navAddBook = document.getElementById('nav-add-book');
  const mobileNavAddBook = document.getElementById('mobile-nav-add-book');

  if (auth.isAuthenticated()) {
    const userName = auth.user?.name || auth.user?.email?.split('@')[0] || 'User';
    navAuth.innerHTML = `
      <div class="user-menu">
        <a href="my-loans.html">My Loans</a>
        <span class="user-name">${userName}</span>
        <button class="btn btn-secondary btn-sm" onclick="handleSignOut()">Sign Out</button>
      </div>
    `;
    mobileWelcome.innerHTML = `<img src="assets/logo_icon.png" alt="" class="welcome-logo"><br><span class="welcome-label">Welcome back,</span><br>${userName}!`;
    mobileNavAuth.innerHTML = `
      <a href="#" onclick="handleSignOut(); return false;">Sign Out</a>
    `;

    // Show admin links if user is branch owner
    if (auth.isBranchOwner()) {
      navAddBook.innerHTML = '<a href="add-book.html">Add Books</a><a href="branch-loans.html">Manage Loans</a>';
      mobileNavAddBook.innerHTML = `
        <div class="mobile-nav-separator">ADMIN ONLY</div>
        <a href="add-book.html">Add Books</a>
        <a href="branch-loans.html">Manage Loans</a>
      `;
    } else {
      navAddBook.innerHTML = '';
      mobileNavAddBook.innerHTML = '';
    }
  } else {
    navAuth.innerHTML = '<a href="login.html" class="btn btn-primary btn-sm">Sign In</a>';
    mobileWelcome.innerHTML = '';
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
