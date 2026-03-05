import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

/** Inject JWT bearer token and request_id into every outgoing request. */
apiClient.interceptors.request.use((config) => {
  // Inject a unique request ID for traceability
  config.headers["X-Request-ID"] = crypto.randomUUID();

  // Attach JWT token from localStorage if available
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

/** Centralised error handling. */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;

      if (status === 401) {
        // Token expired or invalid - clear and redirect to login if needed
        localStorage.removeItem("access_token");
        // Could dispatch a global event or redirect here
        console.warn("[api] Unauthorised - token cleared");
      }

      if (status === 403) {
        console.warn("[api] Forbidden - insufficient permissions");
      }

      // Extract server error message when available
      const serverMessage =
        error.response?.data?.message ?? error.response?.data?.error;

      if (serverMessage) {
        error.message = serverMessage;
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;
