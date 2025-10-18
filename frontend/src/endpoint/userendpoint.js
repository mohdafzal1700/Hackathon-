import apiAxios from "../interceptors/MainInterceptors";


export const register = (data) => apiAxios.post("users/register/", data);

export const login = (data) => apiAxios.post("users/login/", data);

export const refreshToken = (refresh) => apiAxios.post("users/token/refresh/", { refresh });

export const logout = () => apiAxios.post("users/logout/");

export const googleLogin = (id_token) =>
    apiAxios.post("users/auth/google/", { id_token });
