export const getApiUrl = () => {
    // 1. Check user manual override in localStorage
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved && saved.trim() !== '') return saved.trim().replace(/\/$/, '');
    } catch (e) { }

    // 2. Check window runtime context
    if (typeof window !== 'undefined') {
        const host = window.location.hostname;
        const protocol = window.location.protocol;

        // For Vercel (*.vercel.app) and Public Tunnels (*.trycloudflare.com),
        // always return "" so relative fetch('/api/...') uses the same-origin proxy (vercel.json / Vite proxy).
        if (host.endsWith('.vercel.app') || host.endsWith('.trycloudflare.com')) {
            return '';
        }

        // Check explicitly provided VITE_API_URL
        if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.startsWith('http')) {
            const envUrl = import.meta.env.VITE_API_URL.trim().replace(/\/$/, '');
            // If page is loaded over HTTPS (e.g. Cloudflare tunnel or Vercel),
            // NEVER return HTTP url (like http://localhost:8000) because modern browsers block HTTP calls from HTTPS pages (Mixed Content Error).
            if (!(protocol === 'https:' && envUrl.startsWith('http:'))) {
                return envUrl;
            }
        }

        // If local desktop app (localhost/127.0.0.1)
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://127.0.0.1:8000';
        }

        // For LAN access (192.168.x.x, 10.x.x.x) and Public Tunnels (*.trycloudflare.com),
        // returning "" (empty string) routes relative fetch(`${API_URL}/api/...`) to origin on port 5173,
        // which Vite's reverse proxy automatically forwards to backend port 8000!
        // This avoids cross-origin CORS, port 8000 router blocking, and HTTPS Mixed Content errors completely.
        return '';
    }

    return (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.startsWith('http'))
        ? import.meta.env.VITE_API_URL.replace(/\/$/, '')
        : 'http://127.0.0.1:8000';
};

export const API_URL = getApiUrl();

