// API client for the Home Library backend

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async request(method, path, data = null, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth header if available
    const token = auth.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers,
    };

    if (data && method !== 'GET') {
      config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  // Books
  async getBooks(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/books${query ? `?${query}` : ''}`);
  }

  async getBook(id) {
    return this.request('GET', `/books/${id}`);
  }

  async lookupISBN(isbn) {
    return this.request('GET', `/books/lookup?isbn=${encodeURIComponent(isbn)}`);
  }

  async createBook(book) {
    return this.request('POST', '/books', book);
  }

  // Copies
  async getCopies(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/copies${query ? `?${query}` : ''}`);
  }

  async getCopy(id) {
    return this.request('GET', `/copies/${id}`);
  }

  async createCopy(copy) {
    return this.request('POST', '/copies', copy);
  }

  async updateCopy(id, data) {
    return this.request('PUT', `/copies/${id}`, data);
  }

  async deleteCopy(id) {
    return this.request('DELETE', `/copies/${id}`);
  }

  // Branches
  async getBranches() {
    return this.request('GET', '/branches');
  }

  async getBranch(id) {
    return this.request('GET', `/branches/${id}`);
  }

  async createBranch(branch) {
    return this.request('POST', '/branches', branch);
  }

  async updateBranch(id, data) {
    return this.request('PUT', `/branches/${id}`, data);
  }

  // Loans
  async getLoans(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/loans${query ? `?${query}` : ''}`);
  }

  async getLoan(id) {
    return this.request('GET', `/loans/${id}`);
  }

  async createLoan(loan) {
    return this.request('POST', '/loans', loan);
  }

  async returnLoan(id, notes = null) {
    return this.request('PUT', `/loans/${id}/return`, notes ? { notes } : {});
  }

  // Users
  async getCurrentUser() {
    return this.request('GET', '/users/me');
  }

  async updateProfile(data) {
    return this.request('PUT', '/users/me', data);
  }

  async getUsers(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/users${query ? `?${query}` : ''}`);
  }

  async updateUserRole(userId, role) {
    return this.request('PUT', `/users/${userId}/role`, { role });
  }
}

// Global API instance
const api = new ApiClient(CONFIG.API_URL);

// Utility functions
function showMessage(text, type = 'error') {
  const container = document.getElementById('messages') || document.body;
  const msg = document.createElement('div');
  msg.className = `message message-${type}`;
  msg.textContent = text;
  container.prepend(msg);
  setTimeout(() => msg.remove(), 5000);
}

function showLoading(element) {
  element.innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>
  `;
}

function showEmpty(element, message = 'Nothing to display') {
  element.innerHTML = `
    <div class="empty-state">
      <h3>${message}</h3>
    </div>
  `;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString();
}

function isOverdue(dueDateStr) {
  if (!dueDateStr) return false;
  const dueDate = new Date(dueDateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return dueDate < today;
}
