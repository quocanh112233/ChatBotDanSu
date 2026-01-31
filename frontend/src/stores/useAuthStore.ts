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
    isAuthenticated: boolean;

    login: (user: User) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isAuthenticated: false,

            login: (user) =>
                set({ user, isAuthenticated: true }),

            logout: () =>
                set({ user: null, isAuthenticated: false }),
        }),
        {
            name: 'auth-storage', // key in localStorage
        }
    )
);
