declare global {
  interface Window {
    __env: { apiUrl: string; neonAuthUrl: string };
  }
}

export const env = {
  get apiUrl(): string {
    return window.__env?.apiUrl ?? 'http://localhost:5000';
  },
  get neonAuthUrl(): string {
    return window.__env?.neonAuthUrl ?? '';
  },
};
