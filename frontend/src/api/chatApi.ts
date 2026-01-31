
import axiosClient from './axiosClient';

export interface ChatResponse {
    answer: string;
    sources: string[];
}

export const chatApi = {
    sendMessage: async (message: string): Promise<ChatResponse> => {
        // Gọi POST /api/v1/chat
        const response = await axiosClient.post('/chat', { message });
        return response.data;
    },
};
