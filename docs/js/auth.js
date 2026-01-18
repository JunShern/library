// Authentication utilities using Supabase

class Auth {
  constructor() {
    this.supabase = null;
    this.user = null;
    this.session = null;
    this.listeners = [];
  }

  async init() {
    // Initialize Supabase client
    const { createClient } = supabase;
    this.supabase = createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

    // Check for existing session
    try {
      const { data: { session }, error } = await this.supabase.auth.getSession();
      if (error) {
        console.warn('Session error, clearing auth state:', error.message);
        await this.signOut();
      } else if (session) {
        this.session = session;
        await this.fetchUser();
      }
    } catch (e) {
      console.warn('Failed to get session, clearing auth state:', e.message);
      await this.signOut();
    }

    // Listen for auth changes
    this.supabase.auth.onAuthStateChange(async (event, session) => {
      // Handle token refresh failures
      if (event === 'TOKEN_REFRESHED' && !session) {
        console.warn('Token refresh failed, signing out');
        await this.signOut();
        return;
      }

      this.session = session;
      if (session) {
        await this.fetchUser();
      } else {
        this.user = null;
      }
      this.notifyListeners();
    });

    this.notifyListeners();
  }

  async fetchUser() {
    if (!this.session) return;

    try {
      const { data, error } = await this.supabase
        .from('profiles')
        .select('*')
        .eq('id', this.session.user.id)
        .single();

      if (data) {
        this.user = {
          id: this.session.user.id,
          email: this.session.user.email,
          ...data,
        };
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
    }
  }

  async signUp(email, password, name) {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: { name },
      },
    });

    if (error) throw error;
    return data;
  }

  async signIn(email, password) {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;
    return data;
  }

  async signOut() {
    // Call Supabase signOut (ignore errors - session may already be gone)
    try {
      await this.supabase.auth.signOut();
    } catch (e) {
      // Ignore network errors etc.
    }

    // Force clear Supabase localStorage in case signOut API failed
    const storageKey = `sb-${new URL(CONFIG.SUPABASE_URL).hostname.split('.')[0]}-auth-token`;
    localStorage.removeItem(storageKey);

    // Always clear local state and notify UI
    this.user = null;
    this.session = null;
    this.notifyListeners();
  }

  getAccessToken() {
    return this.session?.access_token || null;
  }

  isAuthenticated() {
    return !!this.session;
  }

  isAdmin() {
    return this.user?.role === 'admin';
  }

  isBranchOwner() {
    return this.user?.role === 'branch_owner' || this.isAdmin();
  }

  onAuthChange(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== callback);
    };
  }

  notifyListeners() {
    this.listeners.forEach((callback) => callback(this.user));
  }
}

// Global auth instance
const auth = new Auth();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  auth.init();
});
