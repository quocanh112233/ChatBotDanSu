import axiosClient from './axiosClient';

export const authApi = {
    loginGoogle: (credential: string) => {
        return axiosClient.post('/auth/login/google', { credential });
    },

    logout: () => {
        return axiosClient.post('/auth/logout');
    }
};
