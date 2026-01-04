// Configuration - update these values for your environment
const CONFIG = {
  // API URL - update when deploying
  API_URL: 'http://localhost:8000',

  // Supabase credentials - get from your Supabase project
  SUPABASE_URL: 'https://idjloeyjwjeqcqinowph.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_6veWyU7qhpSXdKuEsJZEVQ_ci_nN4Sq',

  // Default loan duration in days
  DEFAULT_LOAN_DAYS: 14,
};

// Make config globally available
window.CONFIG = CONFIG;
