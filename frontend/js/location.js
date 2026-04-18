(function () {
  const API_BASE = window.API_BASE || (window.getApiBaseUrl ? window.getApiBaseUrl() : `http://${window.location.hostname || 'localhost'}:8000`);

  async function fetchLocationResolution(latitude, longitude) {
    if (latitude === undefined || longitude === undefined || latitude === '' || longitude === '') {
      return null;
    }

    try {
      const response = await fetch(
        `${API_BASE}/resolve-location?lat=${encodeURIComponent(latitude)}&lng=${encodeURIComponent(longitude)}`
      );

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch {
      return null;
    }
  }

  window.fetchLocationResolution = fetchLocationResolution;
})();
