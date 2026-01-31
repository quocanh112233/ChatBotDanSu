import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../stores/useAuthStore';

// Component để bảo vệ các route cần đăng nhập
export const ProtectedRoute = () => {
    const isAuth = useAuthStore((state) => state.isAuthenticated);

    // Nếu chưa login thì đá về trang login
    return isAuth ? <Outlet /> : <Navigate to="/login" replace />;
};

// Component để chuyển hướng nếu đã login rồi (dùng cho trang login)
export const PublicRoute = () => {
    const isAuth = useAuthStore((state) => state.isAuthenticated);

    // Nếu đã login rồi thì đá về trang chủ
    return isAuth ? <Navigate to="/" replace /> : <Outlet />;
};
