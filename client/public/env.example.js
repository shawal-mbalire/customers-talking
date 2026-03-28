// Runtime environment — injected at container start or edited here.
// apiUrl: '' means same-origin (Angular + Flask co-deployed on Cloud Run).
// For local dev, override with: window.__env = { apiUrl: 'http://localhost:8080', neonAuthUrl: '...' }
window.__env = {
  apiUrl: '',
  neonAuthUrl: 'https://your-neon-auth-url',
};
