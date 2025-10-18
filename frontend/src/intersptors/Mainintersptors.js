// frontend/src/services/userInterceptor.js
import axios from "axios";

// Base URL for local backend
const BASE_URL = "http://localhost:8000/api/";

// Create Axios instance
const apiAxios = axios.create({
    baseURL: BASE_URL,
});

// Token management
const getAccessToken = () => localStorage.getItem("access_token");
const getRefreshToken = () => localStorage.getItem("refresh_token");

const setTokens = (accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
};

const clearTokens = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
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

// Response interceptor for token refresh
apiAxios.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                console.log("🔑 Access token expired, attempting refresh...");

                const refreshResponse = await refreshToken();
                if (refreshResponse.status === 200) {
                    const newAccess = refreshResponse.data.access;
                    const newRefresh = refreshResponse.data.refresh;

                    setTokens(newAccess, newRefresh);

                    apiAxios.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;
                    originalRequest.headers["Authorization"] = `Bearer ${newAccess}`;

                    return apiAxios(originalRequest);
                }
            } catch (refreshError) {
                console.error("❌ Token refresh failed:", refreshError);
                clearTokens();
                delete apiAxios.defaults.headers.common["Authorization"];
                window.location.href = "/login";
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export { setTokens, clearTokens, getAccessToken, getRefreshToken };
export default apiAxios;
