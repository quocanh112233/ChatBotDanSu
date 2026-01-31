import React from 'react';
import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../stores/useAuthStore';

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useAuthStore();
    const [error, setError] = React.useState('');

    const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
        try {
            if (credentialResponse.credential) {
                // Remove console.log for security
                const { data } = await authApi.loginGoogle(credentialResponse.credential);

                // Lưu thông tin vào store (Token đã được lưu trong Cookie HttpOnly)
                // API trả về trực tiếp User object, không còn wrapper {user, access_token...} nữa
                login(data);

                // Chuyển hướng
                navigate('/');
            }
        } catch (err) {
            console.error("Login Failed:", err);
            setError('Đăng nhập thất bại. Vui lòng thử lại.');
        }
    };

    const handleGoogleError = () => {
        console.error('Google Login Error');
        setError('Không thể kết nối tới Google.');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden">
            {/* Background decorations */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-primary-200/30 blur-3xl"></div>
                <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-primary-300/20 blur-3xl"></div>
            </div>

            <div className="bg-white/80 backdrop-blur-lg p-8 rounded-2xl shadow-xl z-10 w-full max-w-md border border-white">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">Chào mừng trở lại</h1>
                    <p className="text-gray-500">Đăng nhập để tiếp tục sử dụng ChatBot Dân Sự</p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                        {error}
                    </div>
                )}

                <div className="flex justify-center">
                    <div className="w-full">
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={handleGoogleError}
                            useOneTap
                            theme="filled_blue"
                            shape="pill"
                            width="100%"
                        />
                    </div>
                </div>

                <div className="mt-8 text-center text-sm text-gray-400">
                    <p>© 2024 ChatBot DanSu. All rights reserved.</p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
