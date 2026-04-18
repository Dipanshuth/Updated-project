/**
 * Shared frontend runtime config.
 *
 * Behavior:
 * - If frontend is served by backend on :8000 -> use same-origin API paths.
 * - If frontend is served from another port/file -> default API to http://<hostname>:8000.
 * - Optional override via localStorage key: apiBaseUrl (e.g. http://localhost:8000).
 */
(function () {
  function getApiBaseUrl() {
    const override = (localStorage.getItem('apiBaseUrl') || '').trim();
    if (override) {
      return override.replace(/\/$/, '');
    }

    const isHttp = window.location.protocol === 'http:' || window.location.protocol === 'https:';
    const isBackendPort = window.location.port === '8000';

    if (isHttp && isBackendPort) {
      return '';
    }

    const host = window.location.hostname || 'localhost';
    return `http://${host}:8000`;
  }

  window.getApiBaseUrl = getApiBaseUrl;
  window.API_BASE = getApiBaseUrl();
})();
