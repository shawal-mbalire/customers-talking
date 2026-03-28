declare global {
  interface Window {
    __env: { apiUrl: string; neonAuthUrl: string };
  }
}

export const env = {
  get apiUrl(): string {
    // Empty string = same origin (production, co-deployed with Flask).
    // Set window.__env.apiUrl = 'http://localhost:8080' for local dev.
    return window.__env?.apiUrl ?? '';
  },
  get neonAuthUrl(): string {
    return window.__env?.neonAuthUrl ?? '';
  },
};
