'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Loader2, ShieldCheck, Lock } from 'lucide-react';
import { useToast } from '@/app/components/ErrorToast';

export default function LoginPage() {
    const router = useRouter();
    const { showToast, ToastContainer } = useToast();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            await api.login(username, password);
            showToast('Login successful', 'success');
            setTimeout(() => {
                router.push('/incidents');
            }, 500);
        } catch (error) {
            console.error('Login failed:', error);
            showToast('Login failed. Please check your credentials.', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
            <ToastContainer />

            <div className="w-full max-w-md">
                <div className="flex justify-center mb-8">
                    <div className="bg-blue-500/10 p-4 rounded-2xl border border-blue-500/20">
                        <ShieldCheck className="h-12 w-12 text-blue-500" />
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
                    <div className="text-center mb-8">
                        <h1 className="text-2xl font-bold text-white mb-2">Welcome Back</h1>
                        <p className="text-slate-400">Sign in to WardenXT Incident Commander</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">Username</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pl-10"
                                    placeholder="admin"
                                    required
                                />
                                <ShieldCheck className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">Password</label>
                            <div className="relative">
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pl-10"
                                    placeholder="••••••••"
                                    required
                                />
                                <Lock className="absolute left-3 top-3.5 h-5 w-5 text-slate-500" />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-xs text-slate-500">
                        Powered by Gemini 2.0 Flash
                    </div>
                </div>
            </div>
        </div>
    );
}
