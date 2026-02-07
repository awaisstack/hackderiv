'use client';

import { useEffect, useState } from 'react';

export default function HudOverlay() {
    const [time, setTime] = useState('');
    const [coordinate, setCoordinate] = useState({ x: 0, y: 0 });

    useEffect(() => {
        // Time update
        const updateTime = () => {
            const now = new Date();
            setTime(now.toISOString().split('T')[1].split('.')[0] + ' UTC');
        };
        const timeInterval = setInterval(updateTime, 1000);
        updateTime();

        // Mouse follow only for subtle decor effect
        const handleMouseMove = (e: MouseEvent) => {
            setCoordinate({
                x: Math.round((e.clientX / window.innerWidth) * 1000),
                y: Math.round((e.clientY / window.innerHeight) * 1000)
            });
        };
        window.addEventListener('mousemove', handleMouseMove);

        return () => {
            clearInterval(timeInterval);
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, []);

    return (
        <div className="fixed inset-0 pointer-events-none z-50 select-none overflow-hidden">
            {/* Top Left Bracket */}
            <div className="absolute top-8 left-8 w-32 h-32 border-l-2 border-t-2 border-black/20" />
            <div className="absolute top-8 left-8 mt-2 ml-2 text-[10px] font-mono tracking-widest opacity-40">
                SYS.RDY // {time}
            </div>

            {/* Top Right Bracket */}
            <div className="absolute top-8 right-8 w-32 h-32 border-r-2 border-t-2 border-black/20" />
            <div className="absolute top-8 right-8 mt-2 mr-2 text-[10px] font-mono tracking-widest opacity-40 text-right">
                COORDS: {coordinate.x}.{coordinate.y}
            </div>

            {/* Bottom Left Bracket */}
            <div className="absolute bottom-8 left-8 w-32 h-32 border-l-2 border-b-2 border-black/20" />
            <div className="absolute bottom-8 left-8 mb-2 ml-2 text-[10px] font-mono tracking-widest opacity-40">
                LINK: SECURE
            </div>

            {/* Bottom Right Bracket */}
            <div className="absolute bottom-8 right-8 w-32 h-32 border-r-2 border-b-2 border-black/20" />
            <div className="absolute bottom-8 right-8 mb-2 mr-2 text-[10px] font-mono tracking-widest opacity-40 text-right">
                VER: 2.4.0-ALPHA
            </div>

            {/* Center Crosshair */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 opacity-20">
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-black" />
                <div className="absolute left-1/2 top-0 h-full w-[1px] bg-black" />
            </div>

            {/* Scanning Line Animation */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/[0.03] to-transparent animate-scan pointer-events-none"
                style={{ height: '20%', animation: 'scan 8s linear infinite' }} />

            {/* Decorative Grid Lines */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:100px_100px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />
        </div>
    );
}
