import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
    id: string;
    email: string;
    full_name: string;
    avatar_url: string;
}

interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;

    login: (user: User, accessToken: string, refreshToken: string) => void;
    logout: () => void;
    updateAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            login: (user, accessToken, refreshToken) =>
                set({ user, accessToken, refreshToken, isAuthenticated: true }),

            logout: () =>
                set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),

            updateAccessToken: (token) =>
                set({ accessToken: token }),
        }),
        {
            name: 'auth-storage', // key in localStorage
        }
    )
);
