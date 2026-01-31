import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

// Tạo axios instance
const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // QUAN TRỌNG: Để gửi/nhận Cookie HttpOnly
});

// Interceptor: Xử lý lỗi 401 (Token hết hạn) => Refresh Token TỰ ĐỘNG bằng Cookie
axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // Gọi Refresh Token (Backend tự đọc Cookie Refresh)
                await axiosClient.post('/auth/refresh');

                // Retry request ban đầu (Cookie mới đã được browser tự động lưu)
                return axiosClient(originalRequest);
            } catch (refreshError) {
                // Refresh fail -> Logout
                useAuthStore.getState().logout();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default axiosClient;
