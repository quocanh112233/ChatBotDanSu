import axiosClient from './axiosClient';

export const authApi = {
    loginGoogle: (credential: string) => {
        return axiosClient.post('/auth/login/google', { credential });
    },

    logout: (refreshToken: string) => {
        return axiosClient.post('/auth/logout', { refresh_token: refreshToken });
    }
};
