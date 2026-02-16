import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scan, Lock, Fingerprint, CheckCircle, User, Mail, ShieldAlert, Key, ChevronLeft } from 'lucide-react';
import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendPasswordResetEmail
} from 'firebase/auth';
import { auth } from '../firebase';
import ScrambleText from './ui/ScrambleText';

const LoginModal = ({ isOpen, onClose, onLogin, onGuestLogin }) => {
    const [step, setStep] = useState('scan'); // scan, input, signup, forgot, verifying, success, error
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState(null);
    const [isScanning, setIsScanning] = useState(true);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        if (isOpen) {
            setStep('scan');
            setIsScanning(true);
            setError(null);
            setMessage(null);
            setEmail('');
            setPassword('');
            setConfirmPassword('');
            // Simulate Biometric Scan
            setTimeout(() => {
                setIsScanning(false);
                setStep('input');
            }, 2000);
        }
    }, [isOpen]);

    const handleAuthenticate = async (e) => {
        e.preventDefault();
        setError(null);
        setStep('verifying');

        try {
            if (!auth || auth?.config?.apiKey?.includes("DummyKey")) {
                console.warn("Using Mock Auth Bypass (Firebase not configured)");
                setTimeout(() => {
                    onLogin("mock-token-123-local-bypass");
                    setStep('success');
                    setTimeout(onClose, 800);
                }, 1500);
                return;
            }

            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            const token = await user.getIdToken();

            console.log("Firebase Login Success:", user.uid);
            onLogin(token);
            setStep('success');
            setTimeout(onClose, 800);
        } catch (err) {
            console.error("Auth Error:", err);
            setStep('input');
            setError(err.message.includes('auth/invalid-credential') ? "Invalid Operator ID or Secure Key" : err.message);
        }
    };

    const handleSignUp = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        setError(null);
        setStep('verifying');

        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            const token = await user.getIdToken();

            console.log("Firebase Signup Success:", user.uid);
            onLogin(token);
            setStep('success');
            setTimeout(onClose, 800);
        } catch (err) {
            console.error("Signup Error:", err);
            setStep('signup');
            setError(err.message);
        }
    };

    const handleForgotPassword = async (e) => {
        e.preventDefault();
        setError(null);
        setStep('verifying');

        try {
            await sendPasswordResetEmail(auth, email);
            setMessage("Secure Key reset link dispatched to your Operator ID email.");
            setStep('input');
        } catch (err) {
            console.error("Reset Error:", err);
            setStep('forgot');
            setError(err.message);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />

            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] shadow-2xl border-indigo-500/20 bg-black/60 overflow-hidden"
            >
                {/* Background Grid Animation */}
                <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f46e5_1px,transparent_1px),linear-gradient(to_bottom,#4f46e5_1px,transparent_1px)] bg-[size:2rem_2rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
                </div>

                <div className="relative z-10 flex flex-col items-center">

                    {/* Header Icon */}
                    <div className="mb-8">
                        <div className={`w-20 h-20 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${step === 'scan' ? 'border-indigo-500/50 bg-indigo-500/10' :
                            step === 'success' ? 'border-emerald-500/50 bg-emerald-500/10' :
                                'border-white/10 bg-white/5'
                            }`}>
                            <AnimatePresence mode='wait'>
                                {step === 'scan' && (
                                    <motion.div
                                        key="scan"
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                        className="relative"
                                    >
                                        <Scan className="w-10 h-10 text-indigo-400 animate-pulse" />
                                        <motion.div
                                            className="absolute inset-0 bg-indigo-500/20 blur-xl"
                                            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.2, 0.5] }}
                                            transition={{ duration: 2, repeat: Infinity }}
                                        />
                                    </motion.div>
                                )}
                                {(step === 'input' || step === 'signup' || step === 'forgot') && (
                                    <motion.div key="lock" initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                                        {step === 'forgot' ? <ShieldAlert className="w-10 h-10 text-amber-500" /> : <Lock className="w-10 h-10 text-slate-400" />}
                                    </motion.div>
                                )}
                                {step === 'verifying' && (
                                    <motion.div key="verifying" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                        <Fingerprint className="w-10 h-10 text-indigo-400" />
                                    </motion.div>
                                )}
                                {step === 'success' && (
                                    <motion.div key="success" initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                                        <CheckCircle className="w-10 h-10 text-emerald-400" />
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="w-full text-center space-y-6">
                        <div className="space-y-2">
                            <h3 className="text-2xl font-black tracking-tighter text-white uppercase">
                                {step === 'scan' ? <ScrambleText text="IDENTITY SCAN..." /> :
                                    step === 'success' ? "ACCESS GRANTED" :
                                        step === 'signup' ? "ACCOUNT SETUP" :
                                            step === 'forgot' ? "SECURE KEY RECOVERY" :
                                                "SYSTEM LOGIN"}
                            </h3>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">
                                {step === 'scan' ? "Verifying Biometric Signature" :
                                    step === 'signup' ? "Initialize Operator Credentials" :
                                        step === 'forgot' ? "Validation Required" :
                                            "Secure Tradeverse Terminal"}
                            </p>
                        </div>

                        {error && (
                            <div className="p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                                <p className="text-[9px] font-bold text-red-400 uppercase text-center">{error}</p>
                            </div>
                        )}

                        {message && (
                            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                                <p className="text-[9px] font-bold text-emerald-400 uppercase text-center">{message}</p>
                            </div>
                        )}

                        {(step === 'input' || step === 'verifying' || step === 'signup' || step === 'forgot') && (
                            <motion.form
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-4 w-full"
                                onSubmit={step === 'signup' ? handleSignUp : step === 'forgot' ? handleForgotPassword : handleAuthenticate}
                            >
                                <div className="space-y-3 text-left">
                                    <div>
                                        <label className="text-[9px] font-black uppercase text-indigo-400 ml-1 tracking-widest">Operator ID</label>
                                        <div className="relative">
                                            <input
                                                type="email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                placeholder="user@tradeverse.ai"
                                                required
                                                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-xs font-mono tracking-wide text-white focus:outline-none focus:border-indigo-500/50 focus:bg-indigo-500/5 transition-all placeholder:text-slate-700"
                                            />
                                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                        </div>
                                    </div>

                                    {step !== 'forgot' && (
                                        <div>
                                            <label className="text-[9px] font-black uppercase text-indigo-400 ml-1 tracking-widest">Secure Key</label>
                                            <div className="relative">
                                                <input
                                                    type="password"
                                                    value={password}
                                                    onChange={(e) => setPassword(e.target.value)}
                                                    placeholder="••••••••"
                                                    required
                                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-xs font-mono tracking-widest text-white focus:outline-none focus:border-indigo-500/50 focus:bg-indigo-500/5 transition-all placeholder:text-slate-700"
                                                />
                                                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            </div>
                                        </div>
                                    )}

                                    {step === 'signup' && (
                                        <div>
                                            <label className="text-[9px] font-black uppercase text-indigo-400 ml-1 tracking-widest">Confirm Secure Key</label>
                                            <div className="relative">
                                                <input
                                                    type="password"
                                                    value={confirmPassword}
                                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                                    placeholder="••••••••"
                                                    required
                                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-xs font-mono tracking-widest text-white focus:outline-none focus:border-indigo-500/50 focus:bg-indigo-500/5 transition-all placeholder:text-slate-700"
                                                />
                                                <ShieldAlert className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <button
                                    type="submit"
                                    disabled={step === 'verifying'}
                                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-4 rounded-xl font-black text-[10px] uppercase tracking-[0.3em] transition-all shadow-lg shadow-indigo-900/20 active:scale-[0.98] group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                                    {step === 'verifying' ? 'PROCESSING...' :
                                        step === 'signup' ? 'INITIALIZE OPERATOR' :
                                            step === 'forgot' ? 'REQUEST RESET' :
                                                'INITIALIZE SESSION'}
                                </button>

                                <div className="pt-2 flex flex-col gap-3">
                                    <div className="flex items-center justify-between px-2">
                                        {step === 'input' ? (
                                            <>
                                                <button type="button" onClick={() => setStep('forgot')} className="text-[9px] font-bold text-slate-500 hover:text-white uppercase tracking-wider transition-colors">
                                                    Forgot Key?
                                                </button>
                                                <button type="button" onClick={() => setStep('signup')} className="text-[9px] font-bold text-indigo-400 hover:text-indigo-300 uppercase tracking-wider transition-colors">
                                                    Setup Account
                                                </button>
                                            </>
                                        ) : (
                                            <button type="button" onClick={() => { setStep('input'); setError(null); setMessage(null); }} className="flex items-center gap-1 text-[9px] font-bold text-slate-500 hover:text-white uppercase tracking-wider transition-colors">
                                                <ChevronLeft className="w-3 h-3" /> Back to Login
                                            </button>
                                        )}
                                    </div>

                                    <div className="flex items-center justify-between px-2 border-t border-white/5 pt-3">
                                        <button type="button" onClick={onGuestLogin} className="text-[9px] font-bold text-slate-500 hover:text-white uppercase tracking-wider transition-colors">
                                            Guest Access
                                        </button>
                                        <span className="text-[9px] font-bold text-slate-700 uppercase tracking-wider">v3.1.0-SECURE</span>
                                    </div>
                                </div>
                            </motion.form>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default LoginModal;
