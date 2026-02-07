'use client';

import { useState } from 'react';
import ParticleDots from '@/components/ParticleDots';
import HudOverlay from '@/components/HudOverlay';

interface OnboardingProps {
    onComplete: () => void;
}

const slides = [
    {
        title: "Deriv P2P Sentinel",
        subtitle: "AI-Powered Receipt Fraud Detection",
        description: "Protect your P2P trades with multi-agent intelligence.",
        icon: "🛡️"
    },
    {
        title: "The Problem",
        subtitle: "Fake Screenshots Are Everywhere",
        description: "Scammers upload photoshopped bank receipts to steal your money. Manual review is slow and error-prone.",
        icon: "⚠️"
    },
    {
        title: "Meet the Agents",
        subtitle: "Three Specialized AI Investigators",
        description: "Each agent analyzes a different aspect of the receipt — metadata, privacy, and visual forensics.",
        agents: [
            { icon: "🕵️", name: "Agent Meta", role: "Metadata Forensics" },
            { icon: "🔒", name: "Agent Privacy", role: "PII Redaction" },
            { icon: "🧠", name: "Agent Vision", role: "Visual Analysis" }
        ]
    },
    {
        title: "Try It Now",
        subtitle: "Upload a Receipt to Analyze",
        description: "See real-time forensic analysis with risk scoring.",
        icon: "🚀",
        isFinal: true
    }
];

export default function Onboarding({ onComplete }: OnboardingProps) {
    const [currentSlide, setCurrentSlide] = useState(0);
    const slide = slides[currentSlide];

    const nextSlide = () => {
        if (currentSlide < slides.length - 1) {
            setCurrentSlide(currentSlide + 1);
        } else {
            onComplete();
        }
    };

    const prevSlide = () => {
        if (currentSlide > 0) {
            setCurrentSlide(currentSlide - 1);
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-8 relative scanlines">
            {/* Animated Particle Background */}
            <ParticleDots />
            <HudOverlay />

            {/* Progress Dots */}
            <div className="flex gap-2 mb-12 relative z-10">
                {slides.map((_, idx) => (
                    <div
                        key={idx}
                        className={`w-2 h-2 rounded-full transition-all ${idx === currentSlide
                            ? 'w-8 bg-[var(--foreground)] progress-dot-active'
                            : idx < currentSlide
                                ? 'bg-[var(--foreground)]'
                                : 'bg-[var(--border-light)]'
                            }`}
                    />
                ))}
            </div>

            {/* Slide Content */}
            <div className="max-w-2xl text-center animate-fadeIn relative z-10" key={currentSlide}>
                {/* Icon or Agents */}
                {slide.agents ? (
                    <div className="flex justify-center gap-6 mb-8">
                        {slide.agents.map((agent, idx) => (
                            <div
                                key={idx}
                                className="tech-border flex flex-col items-center p-6 min-w-[160px] cursor-pointer glitch-hover"
                                style={{ animationDelay: `${idx * 0.1}s` }}
                            >
                                <span className="text-4xl mb-3">{agent.icon}</span>
                                <span className="font-semibold text-sm">{agent.name}</span>
                                <span className="text-xs text-[var(--muted)]">{agent.role}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-7xl mb-8">{slide.icon}</div>
                )}

                {/* Title */}
                <h1 className="text-4xl font-bold mb-3">{slide.title}</h1>
                <h2 className="text-xl text-[var(--muted)] mb-4">{slide.subtitle}</h2>
                <p className="text-[var(--muted)] mb-12 max-w-md mx-auto">
                    {slide.description}
                </p>

                {/* Navigation */}
                <div className="flex items-center justify-center gap-4">
                    {currentSlide > 0 && (
                        <button onClick={prevSlide} className="btn">
                            ← Back
                        </button>
                    )}
                    <button onClick={nextSlide} className="btn btn-primary">
                        {slide.isFinal ? "Start Analysis →" : "Next →"}
                    </button>
                </div>
            </div>

            {/* Skip Link */}
            {!slide.isFinal && (
                <button
                    onClick={onComplete}
                    className="mt-12 text-sm text-[var(--muted)] hover:text-[var(--foreground)] transition-colors relative z-10"
                >
                    Skip intro →
                </button>
            )}
        </div>
    );
}
