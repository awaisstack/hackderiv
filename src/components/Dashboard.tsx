'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import ParticleDots from '@/components/ParticleDots';
import HudOverlay from '@/components/HudOverlay';

interface Agent {
    id: string;
    icon: string;
    name: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    logs: string[];
    thinkingText: string;
}

interface AnalysisResult {
    risk_score: number;
    verdict: string;
    flags: Array<{
        layer: string;
        severity: string;
        description: string;
        confidence: number;
    }>;
    explanation: string;
    software_detected?: string;
    is_edited: boolean;
    font_consistency_score: number;
    alignment_score: number;
}

const AGENT_THINKING = {
    meta: [
        "Extracting EXIF metadata...",
        "Checking for editing software signatures...",
        "Analyzing device information...",
        "Verifying image authenticity markers...",
        "Scanning for Photoshop/GIMP traces..."
    ],
    privacy: [
        "Running OCR text extraction...",
        "Detecting sensitive information patterns...",
        "Identifying account numbers...",
        "Applying privacy redaction...",
        "Preparing sanitized image..."
    ],
    vision: [
        "Connecting to Gemini AI...",
        "Analyzing font consistency...",
        "Checking text alignment patterns...",
        "Detecting visual artifacts...",
        "Evaluating receipt authenticity..."
    ]
};

const API_URL = '/api/py';

export default function Dashboard() {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [agents, setAgents] = useState<Agent[]>([
        { id: 'meta', icon: '🕵️', name: 'Agent Meta', status: 'pending', logs: [], thinkingText: '' },
        { id: 'privacy', icon: '🔒', name: 'Agent Privacy', status: 'pending', logs: [], thinkingText: '' },
        { id: 'vision', icon: '🧠', name: 'Agent Vision', status: 'pending', logs: [], thinkingText: '' },
    ]);
    const [allLogs, setAllLogs] = useState<string[]>([]);
    const [claimedAmount, setClaimedAmount] = useState<string>('');
    const [expectedBank, setExpectedBank] = useState<string>('unknown');
    const [currentAgentIndex, setCurrentAgentIndex] = useState<number>(-1);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logs
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [allLogs]);

    // Cycle through thinking texts for active agent
    useEffect(() => {
        if (currentAgentIndex < 0 || currentAgentIndex >= agents.length) return;

        const agentId = agents[currentAgentIndex].id as keyof typeof AGENT_THINKING;
        const thoughts = AGENT_THINKING[agentId];
        let thoughtIndex = 0;

        const interval = setInterval(() => {
            setAgents(prev => prev.map((a, idx) =>
                idx === currentAgentIndex
                    ? { ...a, thinkingText: thoughts[thoughtIndex % thoughts.length] }
                    : a
            ));
            thoughtIndex++;
        }, 800);

        return () => clearInterval(interval);
    }, [currentAgentIndex]);

    const handleFileSelect = useCallback((selectedFile: File) => {
        setFile(selectedFile);
        setResult(null);
        setAllLogs([]);
        setCurrentAgentIndex(-1);
        setAgents(prev => prev.map(a => ({ ...a, status: 'pending', logs: [], thinkingText: '' })));

        const reader = new FileReader();
        reader.onload = (e) => {
            setPreview(e.target?.result as string);
        };
        reader.readAsDataURL(selectedFile);
    }, []);

    // Load pre-stored sample receipts for judges
    const loadSampleReceipt = useCallback(async (type: 'original' | 'edited') => {
        const filename = type === 'original' ? '/original_receipt.png' : '/edited_receipt.png';
        try {
            const response = await fetch(filename);
            const blob = await response.blob();
            const file = new File([blob], `${type}_receipt.png`, { type: 'image/png' });
            handleFileSelect(file);
        } catch (error) {
            console.error('Error loading sample receipt:', error);
        }
    }, [handleFileSelect]);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.type.startsWith('image/')) {
            handleFileSelect(droppedFile);
        }
    }, [handleFileSelect]);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const isAnalyzingRef = useRef(false);

    const simulateAgentProgress = async () => {
        for (let i = 0; i < agents.length; i++) {
            if (!isAnalyzingRef.current) break; // Stop if analysis stopped/failed

            setCurrentAgentIndex(i);
            setAgents(prev => prev.map((a, idx) =>
                idx === i ? { ...a, status: 'running' } : a
            ));

            // Add initial log
            const agentNames = { 'meta': 'Agent Meta', 'privacy': 'Agent Privacy', 'vision': 'Agent Vision' };
            const agentId = agents[i].id;
            const name = agentNames[agentId as keyof typeof agentNames];

            setAllLogs(prev => [...prev, `${agents[i].icon} ${name} initialized...`]);

            // Wait with check
            const waitTime = 2000 + Math.random() * 1000;
            const start = Date.now();
            while (Date.now() - start < waitTime) {
                if (!isAnalyzingRef.current) break;
                await new Promise(r => setTimeout(r, 100));
            }

            if (!isAnalyzingRef.current) break;

            setAgents(prev => prev.map((a, idx) =>
                idx === i ? { ...a, status: 'complete', thinkingText: '✓ Analysis Complete' } : a
            ));
            setAllLogs(prev => [...prev, `${agents[i].icon} ${name} task completed.`]);
        }
        setCurrentAgentIndex(-1);
    };

    const handleAnalyze = async () => {
        if (!file || !claimedAmount) return;

        setIsAnalyzing(true);
        isAnalyzingRef.current = true;
        setResult(null);
        setAllLogs([]);
        setAgents(prev => prev.map(a => ({ ...a, status: 'pending', logs: [], thinkingText: '' })));

        // Start agent animation
        simulateAgentProgress();

        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('claimed_amount', claimedAmount);
            formData.append('expected_bank', expectedBank);

            const response = await fetch(`${API_URL}/scan`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
                try {
                    const clonedResponse = response.clone();
                    const errorData = await clonedResponse.json();
                    if (errorData.detail) errorMessage = errorData.detail;
                } catch (e) {
                    const text = await response.text();
                    if (text) errorMessage = text;
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();

            // Analysis success - stop simulation and show real data
            isAnalyzingRef.current = false;

            // Update agents with real data
            if (data.agents) {
                setAgents(prev => prev.map(a => {
                    const backendAgent = data.agents.find((ba: any) => ba.name.toLowerCase().includes(a.id));
                    return backendAgent ? {
                        ...a,
                        status: 'complete',
                        logs: backendAgent.logs || [],
                        thinkingText: '✓ Analysis Complete'
                    } : a;
                }));
            }

            if (data.logs) {
                setAllLogs(data.logs);
            }

            setResult(data.analysis);
        } catch (error) {
            console.error('Analysis error:', error);
            isAnalyzingRef.current = false; // Stop simulation
            setAllLogs(prev => [...prev, `❌ Error: ${error instanceof Error ? error.message : String(error)}`]);
            setAgents(prev => prev.map(a => ({
                ...a,
                status: 'error',
                thinkingText: 'Analysis Failed',
                logs: [...a.logs, '❌ Agent process terminated unexpectedly.']
            })));
        } finally {
            setIsAnalyzing(false);
            isAnalyzingRef.current = false;
        }
    };

    const getRiskColor = (score: number) => {
        if (score <= 20) return 'border-green-500 text-green-600 bg-green-50';
        if (score <= 75) return 'border-amber-500 text-amber-600 bg-amber-50';
        return 'border-red-500 text-red-600 bg-red-50';
    };

    const getAgentStatusColor = (status: string) => {
        switch (status) {
            case 'pending': return 'border-slate-200 bg-white opacity-60 grayscale';
            case 'running': return 'border-blue-500 bg-blue-50 shadow-md ring-2 ring-blue-200 scale-[1.02] z-10 agent-card-active';
            case 'complete': return 'border-green-500 bg-white shadow-sm agent-card-complete';
            case 'error': return 'border-red-500 bg-red-50';
            default: return 'border-slate-200';
        }
    };

    return (
        <div className="min-h-screen bg-white p-6 font-sans text-slate-800 relative scanlines">
            {/* Animated Particle Background */}
            <ParticleDots />
            <HudOverlay />

            {/* Header */}
            <header className="max-w-7xl mx-auto mb-6 flex items-center justify-between relative z-10">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        🛡️ <span className="text-slate-900">P2P Sentinel</span>
                    </h1>
                    <p className="text-sm text-slate-500">Autonomous Fraud Detection System</p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full border border-black/10 shadow-sm text-xs font-semibold text-slate-700">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        System Online
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 pb-20 relative z-10">

                {/* LEFT COLUMN: Input & Upload (4 Cols) */}
                <div className="lg:col-span-4 flex flex-col gap-6">

                    {/* Upload Zone */}
                    <div className="bg-white shadow-sm border-2 border-slate-200 p-1">
                        <div
                            className={`
                                relative rounded-lg border-2 border-dashed p-8 text-center transition-all cursor-pointer h-72 flex flex-col items-center justify-center
                                ${preview ? 'border-slate-300 bg-slate-50' : 'border-blue-300 bg-blue-50 hover:bg-blue-100'}
                            `}
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                className="hidden"
                                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                            />

                            {preview ? (
                                <div className="relative group w-full h-full flex items-center justify-center overflow-hidden">
                                    <img
                                        src={preview}
                                        alt="Receipt preview"
                                        className="max-h-full max-w-full rounded shadow-sm object-contain"
                                    />
                                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded">
                                        <p className="text-white font-medium">Click to Change</p>
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    <div className="text-4xl mb-3">📤</div>
                                    <h3 className="font-semibold text-slate-700">Upload Receipt</h3>
                                    <p className="text-sm text-slate-500 mt-1">Drag & drop or click to browse</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sample Receipt Buttons for Judges */}
                    <div className="bg-slate-50 border border-dashed border-slate-300 rounded-lg p-3">
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-2 text-center">
                            🧪 Demo Samples for Testing
                        </p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => loadSampleReceipt('original')}
                                className="flex-1 px-3 py-2 text-xs font-medium rounded-lg border border-green-200 bg-green-50 text-green-700 hover:bg-green-100 transition-colors flex items-center justify-center gap-1.5"
                                disabled={isAnalyzing}
                            >
                                <span className="text-sm">✅</span> Legit Receipt
                            </button>
                            <button
                                onClick={() => loadSampleReceipt('edited')}
                                className="flex-1 px-3 py-2 text-xs font-medium rounded-lg border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 transition-colors flex items-center justify-center gap-1.5"
                                disabled={isAnalyzing}
                            >
                                <span className="text-sm">🚨</span> Fake Receipt
                            </button>
                        </div>
                    </div>

                    {/* Transaction Form */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex-1">
                        <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            💰 Transaction Details
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    Claimed Amount (PKR)
                                </label>
                                <input
                                    type="number"
                                    value={claimedAmount}
                                    onChange={(e) => setClaimedAmount(e.target.value)}
                                    placeholder="e.g. 5000"
                                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all font-mono text-lg"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    Target Wallet/Bank
                                </label>
                                <select
                                    value={expectedBank}
                                    onChange={(e) => setExpectedBank(e.target.value)}
                                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                                >
                                    <option value="unknown">Select Provider</option>
                                    <option value="jazzcash">JazzCash</option>
                                    <option value="easypaisa">EasyPaisa</option>
                                    <option value="sadapay">SadaPay</option>
                                    <option value="nayapay">NayaPay</option>
                                </select>
                            </div>

                            <button
                                onClick={handleAnalyze}
                                disabled={!file || !claimedAmount || isAnalyzing}
                                className={`
                                    w-full mt-6 py-4 rounded-none font-bold text-lg text-white shadow-lg transition-all transform
                                    ${!file || !claimedAmount || isAnalyzing
                                        ? 'bg-slate-300 cursor-not-allowed shadow-none'
                                        : 'bg-slate-900 hover:bg-slate-800 hover:scale-[1.02] active:scale-[0.98] shadow-slate-300/50'
                                    }
                                `}
                            >
                                {isAnalyzing ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Running Forensics...
                                    </span>
                                ) : '🔍 Analyze Receipt'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN: Agents & Results (8 Cols) */}
                <div className="lg:col-span-8 flex flex-col gap-6">

                    {/* Agent Grid */}
                    <div className="grid grid-cols-3 gap-4">
                        {agents.map((agent) => (
                            <div
                                key={agent.id}
                                className={`
                                    relative p-4 rounded-xl border-2 transition-all duration-300 flex flex-col min-h-[140px]
                                    ${getAgentStatusColor(agent.status)}
                                `}
                            >
                                <div className="flex items-center gap-3 mb-3">
                                    <div className={`
                                        w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-white shadow-sm border border-slate-100 transition-transform
                                        ${agent.status === 'running' ? 'scale-110' : ''}
                                    `}>
                                        {agent.icon}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-slate-800 text-sm leading-tight">{agent.name}</h4>
                                        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
                                            {agent.id === 'meta' ? 'Metadata Filter' : agent.id === 'privacy' ? 'Redaction Layer' : 'Vision Engine'}
                                        </p>
                                        <p className="text-[9px] text-slate-400 mt-1 leading-snug">
                                            {agent.id === 'meta' && 'Extracts EXIF data, timestamps, and device info from images.'}
                                            {agent.id === 'privacy' && 'Detects and redacts PII like names, accounts, and phone numbers.'}
                                            {agent.id === 'vision' && 'Analyzes visual inconsistencies and detects tampering.'}
                                        </p>
                                    </div>
                                </div>

                                {/* Live Agent Log */}
                                <div className="mt-auto bg-white/50 rounded-lg px-3 py-2 border border-black/5 min-h-[48px] flex items-center">
                                    <p className="text-xs font-mono text-slate-700 leading-tight w-full">
                                        {agent.status === 'pending' && <span className="opacity-40 italic">Standby...</span>}
                                        {agent.status === 'running' && (
                                            <span className="flex items-center gap-2 text-blue-700 font-medium">
                                                <span className="animate-spin text-blue-500">⟳</span>
                                                {agent.thinkingText}
                                            </span>
                                        )}
                                        {agent.status === 'complete' && <span className="text-green-700 font-bold flex items-center gap-1">✓ Complete</span>}
                                        {agent.status === 'error' && <span className="text-red-600 font-bold">✕ Failed</span>}
                                    </p>
                                </div>

                                {agent.status === 'running' && (
                                    <div className="absolute top-0 right-0 p-2">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping" />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Central Terminal (Consolidated Logs) */}
                    <div className="bg-slate-900 rounded-xl p-0 shadow-lg border border-slate-700 flex flex-col overflow-hidden terminal-glow">
                        <div className="bg-slate-800 px-4 py-2 flex items-center justify-between border-b border-slate-700">
                            <span className="text-xs font-mono text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                                Live Execution Log
                            </span>
                            <div className="flex gap-1.5 opacity-50">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                                <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
                            </div>
                        </div>
                        <div className="p-4 font-mono text-xs overflow-y-auto max-h-[120px] custom-scrollbar bg-slate-900/95">
                            {allLogs.length === 0 && (
                                <div className="text-slate-600 italic py-2">Waiting for analysis trigger...</div>
                            )}
                            {allLogs.map((log, i) => (
                                <div key={i} className="text-slate-300 flex gap-3 py-0.5 border-l-2 border-slate-800 pl-2 hover:bg-white/5 hover:border-slate-600 transition-colors">
                                    <span className="text-slate-600 select-none min-w-[60px]">{`[${String(i).padStart(3, '0')}]`}</span>
                                    <span>{log}</span>
                                </div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>
                    </div>

                    {/* Analysis Results (Shows when ready) */}
                    {result && (
                        <div className="bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden animate-slideUp">
                            <div className="bg-white border-b border-slate-100 p-6 flex items-center justify-between">
                                <div>
                                    <h3 className="font-bold text-xl text-slate-900">Analysis Result</h3>
                                    <p className="text-sm text-slate-500">Forensic confidence breakdown</p>
                                </div>
                                <span className={`px-5 py-2 rounded-full text-base font-bold border ${getRiskColor(result.risk_score)} shadow-sm`}>
                                    {result.verdict}
                                </span>
                            </div>

                            <div className="p-8 grid grid-cols-1 md:grid-cols-12 gap-8">
                                {/* Score Circle (4 cols) */}
                                <div className="md:col-span-4 flex flex-col items-center justify-center border-r border-slate-100 pr-4">
                                    <div className="relative">
                                        <div className={`
                                            w-40 h-40 rounded-full border-[10px] flex items-center justify-center shrink-0
                                            ${result.risk_score > 75 ? 'border-red-100' : result.risk_score > 20 ? 'border-amber-100' : 'border-green-100'}
                                        `}>
                                            <div className="text-center">
                                                <div className={`text-5xl font-black ${result.risk_score > 75 ? 'text-red-500' : result.risk_score > 20 ? 'text-amber-500' : 'text-green-500'}`}>
                                                    {result.risk_score}
                                                </div>
                                                <div className="text-[10px] uppercase font-bold text-slate-400 mt-1 tracking-widest">Risk Score</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-6 flex justify-between w-full px-4">
                                        <div className="text-center">
                                            <div className="text-xl font-bold text-slate-700">{result.font_consistency_score}%</div>
                                            <div className="text-[9px] text-slate-400 uppercase tracking-tight">Font Check</div>
                                        </div>
                                        <div className="w-px bg-slate-200 h-8 self-center" />
                                        <div className="text-center">
                                            <div className="text-xl font-bold text-slate-700">{result.alignment_score}%</div>
                                            <div className="text-[9px] text-slate-400 uppercase tracking-tight">Layout</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Findings List (8 cols) */}
                                <div className="md:col-span-8 flex flex-col gap-5">
                                    <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                                            🧠 AI Conclusion
                                        </h4>
                                        <p className="text-sm text-slate-700 leading-relaxed font-medium">
                                            {result.explanation}
                                        </p>
                                    </div>

                                    {result.flags.length > 0 ? (
                                        <div className="space-y-3 pl-1">
                                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Detected Issues</h4>
                                            {result.flags.map((flag, idx) => (
                                                <div key={idx} className={`
                                                    p-4 rounded-xl border border-l-4 text-sm flex gap-4 transition-all hover:translate-x-1 hover:shadow-md bg-white
                                                    ${flag.severity === 'HIGH' ? 'border-slate-100 border-l-red-500' :
                                                        flag.severity === 'MEDIUM' ? 'border-slate-100 border-l-amber-500' : 'border-slate-100 border-l-blue-500'}
                                                `}>
                                                    <div className="text-2xl pt-0.5 outline-none">
                                                        {flag.severity === 'HIGH' ? '🚫' : flag.severity === 'MEDIUM' ? '⚠️' : 'ℹ️'}
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className="font-bold text-slate-800">{flag.layer}</span>
                                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${flag.severity === 'HIGH' ? 'bg-red-100 text-red-600' :
                                                                flag.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-600' :
                                                                    'bg-blue-100 text-blue-600'
                                                                }`}>
                                                                {flag.severity}
                                                            </span>
                                                        </div>
                                                        <p className="text-slate-600 leading-snug">{flag.description}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-4 p-6 bg-green-50 text-green-800 rounded-xl border border-green-200 mt-2">
                                            <div className="w-10 h-10 bg-green-200 rounded-full flex items-center justify-center text-xl shrink-0">✓</div>
                                            <div>
                                                <h5 className="font-bold text-lg">Clean Receipt</h5>
                                                <p className="text-sm opacity-80">This document passed all forensic checks.</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background-color: #cbd5e1;
                    border-radius: 20px;
                }
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-slideUp {
                    animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }
            `}</style>
        </div>
    );
}
