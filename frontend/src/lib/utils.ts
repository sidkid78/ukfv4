// frontend/src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(timestamp: string | Date): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export function getConfidenceColor(score: number): string {
  if (score >= 0.995) return 'bg-green-500';
  if (score >= 0.95) return 'bg-yellow-500';
  if (score >= 0.9) return 'bg-orange-500';
  return 'bg-red-500';
}

export function getConfidenceTextColor(score: number): string {
  if (score >= 0.995) return 'text-green-600';
  if (score >= 0.95) return 'text-yellow-600';
  if (score >= 0.9) return 'text-orange-600';
  return 'text-red-600';
}

export function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
}

export function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}