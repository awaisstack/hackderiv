'use client';

import { useState } from 'react';
import Onboarding from '@/components/Onboarding';
import Dashboard from '@/components/Dashboard';

export default function Home() {
  const [showDashboard, setShowDashboard] = useState(false);

  if (!showDashboard) {
    return <Onboarding onComplete={() => setShowDashboard(true)} />;
  }

  return <Dashboard />;
}
