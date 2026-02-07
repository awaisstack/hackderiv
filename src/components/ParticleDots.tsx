'use client';

import { useEffect, useRef } from 'react';

interface Particle {
    x: number;
    y: number;
    baseX: number;
    baseY: number;
    size: number;
    opacity: number;
    speed: number;
}

export default function ParticleDots() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const mouseRef = useRef({ x: -1000, y: -1000 });
    const particlesRef = useRef<Particle[]>([]);
    const animationRef = useRef<number>(0);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initParticles();
        };

        const initParticles = () => {
            particlesRef.current = [];
            const spacing = 70;
            const cols = Math.ceil(canvas.width / spacing);
            const rows = Math.ceil(canvas.height / spacing);

            for (let i = 0; i < cols; i++) {
                for (let j = 0; j < rows; j++) {
                    particlesRef.current.push({
                        x: i * spacing + spacing / 2,
                        y: j * spacing + spacing / 2,
                        baseX: i * spacing + spacing / 2,
                        baseY: j * spacing + spacing / 2,
                        size: 1.2,
                        opacity: 0.08 + Math.random() * 0.04,
                        speed: 0.02 + Math.random() * 0.02,
                    });
                }
            }
        };

        const handleMouseMove = (e: MouseEvent) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        };

        const handleMouseLeave = () => {
            mouseRef.current = { x: -1000, y: -1000 };
        };

        const animate = () => {
            const particleRgb = getComputedStyle(document.documentElement)
                .getPropertyValue('--particle-rgb')
                .trim() || '18, 18, 18';

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particlesRef.current.forEach((particle) => {
                const dx = mouseRef.current.x - particle.x;
                const dy = mouseRef.current.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const maxDistance = 150;

                // Calculate glow based on cursor proximity
                let glowIntensity = 0;
                let sizeMultiplier = 1;

                if (distance < maxDistance) {
                    const proximity = 1 - distance / maxDistance;
                    glowIntensity = proximity * 0.8;
                    sizeMultiplier = 1 + proximity * 1.5;

                    // Push particles away from cursor slightly
                    const angle = Math.atan2(dy, dx);
                    const pushDistance = (maxDistance - distance) * 0.1;
                    particle.x = particle.baseX - Math.cos(angle) * pushDistance;
                    particle.y = particle.baseY - Math.sin(angle) * pushDistance;
                } else {
                    // Return to base position smoothly
                    particle.x += (particle.baseX - particle.x) * 0.1;
                    particle.y += (particle.baseY - particle.y) * 0.1;
                }

                // Draw glow effect
                if (glowIntensity > 0) {
                    const gradient = ctx.createRadialGradient(
                        particle.x, particle.y, 0,
                        particle.x, particle.y, particle.size * sizeMultiplier * 4
                    );
                    gradient.addColorStop(0, `rgba(${particleRgb}, ${glowIntensity * 0.35})`);
                    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                    ctx.fillStyle = gradient;
                    ctx.beginPath();
                    ctx.arc(particle.x, particle.y, particle.size * sizeMultiplier * 4, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Draw particle
                ctx.fillStyle = `rgba(${particleRgb}, ${particle.opacity + glowIntensity * 0.2})`;
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size * sizeMultiplier, 0, Math.PI * 2);
                ctx.fill();
            });

            animationRef.current = requestAnimationFrame(animate);
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseleave', handleMouseLeave);
        animate();

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseleave', handleMouseLeave);
            cancelAnimationFrame(animationRef.current);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ background: 'transparent' }}
        />
    );
}
