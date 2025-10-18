import apiAxios from "../intersptors/Mainintersptors";


export const register = (data) => apiAxios.post("users/register/", data);

export const login = (data) => apiAxios.post("users/login/", data);

export const refreshToken = (refresh) => apiAxios.post("users/token/refresh/", { refresh });

export const logout = () => {
  const refreshToken = localStorage.getItem('refresh');
  return apiAxios.post("users/logout/", { refresh: refreshToken });
};

export const googleLogin = (id_token) =>
    apiAxios.post("users/auth/google/", { id_token });