
import React, { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { authApi } from '../api/authApi';
import { useNavigate } from 'react-router-dom';
import { Send, LogOut, MessageSquare, User as UserIcon, BookOpen } from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'bot';
    content: string;
    sources?: string[];
}

const ChatPage: React.FC = () => {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();

    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'bot',
            content: `Xin chào ${user?.full_name || 'bạn'}! Tôi là Trợ lý Luật sư ảo chuyên về Bộ Luật Dân Sự 2015. Bạn có thắc mắc gì về pháp luật không?`
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleLogout = async () => {
        try {
            await authApi.logout();
        } catch (error) {
            console.error("Logout error", error);
        } finally {
            logout();
            navigate('/login');
        }
    };

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input
        };

        const botId = (Date.now() + 1).toString();
        // Placeholder bot message
        const botMessage: Message = {
            id: botId,
            role: 'bot',
            content: '',
            sources: []
        };

        setMessages(prev => [...prev, userMessage, botMessage]);
        const question = input;
        setInput('');
        setIsLoading(true);

        try {
            // Use Fetch API for Stream support
            // Get base URL from axios client config or hardcode it. 
            // Better to match axiosClient baseURL. 
            // Assuming default vite proxy or full url.
            const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

            const response = await fetch(`${baseURL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Important for sending cookies
                body: JSON.stringify({ message: question })
            });

            if (!response.ok || !response.body) {
                throw new Error(response.statusText);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedAnswer = "";
            let accumulatedSources: string[] = [];

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // Split by new line because backend sends NDJSON
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const json = JSON.parse(line);

                        if (json.type === 'sources') {
                            accumulatedSources = json.data;
                            // Update UI with sources
                            setMessages(prev => prev.map(msg =>
                                msg.id === botId ? { ...msg, sources: accumulatedSources } : msg
                            ));
                        } else if (json.type === 'content') {
                            accumulatedAnswer += json.data;
                            // Update UI with token
                            setMessages(prev => prev.map(msg =>
                                msg.id === botId ? { ...msg, content: accumulatedAnswer } : msg
                            ));
                        } else if (json.type === 'error') {
                            throw new Error(json.data);
                        }
                    } catch (err) {
                        console.warn("Parse Error:", err);
                    }
                }
            }

        } catch (error) {
            console.error("Chat Stream Error:", error);
            setMessages(prev => prev.map(msg =>
                msg.id === botId
                    ? { ...msg, content: msg.content + "\n\n[Lỗi kết nối hoặc mất mạng. Vui lòng thử lại]" }
                    : msg
            ));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50 font-sans">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200 px-6 py-3 flex justify-between items-center fixed top-0 w-full z-10 transition-all">
                <div className="flex items-center gap-2">
                    <div className="bg-primary-600 p-2 rounded-lg shadow-lg shadow-primary-200">
                        <MessageSquare className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-primary-600 to-indigo-600 bg-clip-text text-transparent">
                        ChatBot Dân Sự
                    </h1>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-full border border-gray-200">
                        {user?.avatar_url ? (
                            <img
                                src={user.avatar_url}
                                alt="Avatar"
                                className="w-6 h-6 rounded-full"
                            />
                        ) : (
                            <div className="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
                                <UserIcon className="w-3 h-3 text-primary-600" />
                            </div>
                        )}
                        <span className="text-sm font-medium text-gray-700 truncate max-w-[150px]">
                            {user?.full_name || user?.email}
                        </span>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 hover:bg-red-50 text-gray-500 hover:text-red-500 rounded-full transition-all duration-200"
                        title="Đăng xuất"
                    >
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </header>

            {/* Chat Area */}
            <main className="flex-1 pt-20 pb-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full overflow-y-auto custom-scrollbar">
                <div className="space-y-6">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div
                                    className={`px-5 py-3.5 rounded-2xl shadow-sm text-base leading-relaxed break-words relative group ${msg.role === 'user'
                                        ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-tr-sm'
                                        : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'
                                        }`}
                                >
                                    {msg.content}
                                </div>

                                {/* Sources display for Bot */}
                                {msg.role === 'bot' && msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-2 ml-1 text-xs text-gray-500 flex flex-wrap gap-2 animate-fadeIn">
                                        <div className="flex items-center gap-1 font-medium text-gray-400">
                                            <BookOpen className="w-3 h-3" />
                                            Nguồn:
                                        </div>
                                        {msg.sources.map((src, idx) => (
                                            <span key={idx} className="bg-gray-100 px-2 py-0.5 rounded border border-gray-200 hover:bg-gray-200 transition-colors">
                                                {src.replace(/_/g, ' ')}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Loading Bubble */}
                    {isLoading && (
                        <div className="flex justify-start w-full">
                            <div className="bg-white px-5 py-4 rounded-2xl rounded-tl-sm border border-gray-100 shadow-sm flex items-center gap-2">
                                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"></div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* Input Area */}
            <div className="fixed bottom-0 left-0 w-full bg-white border-t border-gray-200 px-4 py-4 z-10">
                <div className="max-w-4xl mx-auto w-full">
                    <form
                        onSubmit={handleSendMessage}
                        className="relative flex items-center gap-2 group"
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Nhập câu hỏi pháp lý của bạn..."
                            disabled={isLoading}
                            className="w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-xl focus:ring-primary-500 focus:border-primary-500 block p-4 pr-12 shadow-sm focus:shadow-md transition-all outline-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="absolute right-2 p-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:hover:bg-primary-600 hover:scale-105 active:scale-95"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </form>
                    <p className="text-center text-xs text-gray-400 mt-2">
                        ChatBot có thể mắc sai sót. Vui lòng kiểm tra lại thông tin quan trọng.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ChatPage;
