// frontend/src/services/userInterceptor.js
import axios from "axios";

// Base URL for local backend
const BASE_URL = "http://localhost:8000/api/";

// Create Axios instance
const apiAxios = axios.create({
    baseURL: BASE_URL,
});

// Token management - FIXED: Use consistent key names
const getAccessToken = () => localStorage.getItem("access");
const getRefreshToken = () => localStorage.getItem("refresh");

const setTokens = (accessToken, refreshToken) => {
    localStorage.setItem("access", accessToken);
    if (refreshToken) localStorage.setItem("refresh", refreshToken);
};

const clearTokens = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user");
};

// Initialize Authorization header if token exists
const initializeAuth = () => {
    const token = getAccessToken();
    if (token) {
        apiAxios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    }
};
initializeAuth();

// Refresh token function
export const refreshToken = async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new Error("No refresh token available");

    return axios.post(`${BASE_URL}users/token/refresh/`, { refresh: refreshToken });
};

// Request interceptor
apiAxios.interceptors.request.use(
    (config) => {
        const token = getAccessToken();
        if (token && !config.headers["Authorization"]) {
            config.headers["Authorization"] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for token refresh - FIXED: Handle both 401 and 403
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

apiAxios.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // FIXED: Handle both 401 AND 403 errors
        if (
            (error.response?.status === 401 || error.response?.status === 403) &&
            !originalRequest._retry
        ) {
            if (isRefreshing) {
                // Queue this request if already refreshing
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        originalRequest.headers["Authorization"] = `Bearer ${token}`;
                        return apiAxios(originalRequest);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                console.log("🔑 Access token expired, attempting refresh...");

                const refreshResponse = await refreshToken();
                if (refreshResponse.status === 200) {
                    const newAccess = refreshResponse.data.access;
                    const newRefresh = refreshResponse.data.refresh;

                    setTokens(newAccess, newRefresh);

                    apiAxios.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;
                    originalRequest.headers["Authorization"] = `Bearer ${newAccess}`;

                    processQueue(null, newAccess);
                    isRefreshing = false;

                    console.log("✅ Token refreshed successfully");
                    return apiAxios(originalRequest);
                }
            } catch (refreshError) {
                console.error("❌ Token refresh failed:", refreshError);
                processQueue(refreshError, null);
                isRefreshing = false;

                clearTokens();
                delete apiAxios.defaults.headers.common["Authorization"];
                window.location.href = "/";
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export { setTokens, clearTokens, getAccessToken, getRefreshToken };
export default apiAxios;