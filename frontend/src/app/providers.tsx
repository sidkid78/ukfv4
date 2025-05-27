'use client';

import { ReactNode } from 'react';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from 'sonner';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ErrorBoundary>
      {children}
      <Toaster position="top-right" richColors />
    </ErrorBoundary>
  );
}