import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

// Tạo axios instance
const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor: Gắn token vào header của mọi request
axiosClient.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Interceptor: Xử lý lỗi 401 (Token hết hạn) => Refresh Token
axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Nếu lỗi 401 và chưa retry lần nào
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = useAuthStore.getState().refreshToken;

            if (refreshToken) {
                try {
                    // Gọi API refresh token
                    const { data } = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh`, {
                        refresh_token: refreshToken
                    });

                    // Cập nhật token mới vào store
                    useAuthStore.getState().updateAccessToken(data.access_token);

                    // Gắn token mới vào request cũ và gọi lại
                    originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                    return axiosClient(originalRequest);
                } catch (refreshError) {
                    // Nếu refresh fail thì logout luôn
                    useAuthStore.getState().logout();
                    window.location.href = '/login';
                    return Promise.reject(refreshError);
                }
            } else {
                // Không có refresh token -> Logout
                useAuthStore.getState().logout();
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default axiosClient;
