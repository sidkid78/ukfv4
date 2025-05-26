'use client';

import { fetchAxesMetadata } from '@/lib/api';
import { AxisMetadata } from '@/types/axis';
import React, { useState, useEffect } from 'react';

// Subcomponents for better organization
const LoadingSpinner = () => (
  <div className="flex justify-center items-center h-32">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500" />
    <p className="ml-4 text-gray-700">Loading Axis Metadata...</p>
  </div>
);

const ErrorDisplay = ({ error }: { error: string }) => (
  <div className="p-4 my-4 text-sm text-red-700 bg-red-100 rounded-lg shadow" role="alert">
    <span className="font-medium">Error:</span> {error}
    <p className="mt-2 text-xs">Please ensure the backend API is running and accessible.</p>
  </div>
);

const AxisTable = ({ axes }: { axes: AxisMetadata[] }) => (
  <div className="overflow-x-auto shadow-md rounded-lg">
    <table className="min-w-full text-sm text-left text-gray-700 bg-white">
      <thead className="text-xs text-gray-700 uppercase bg-gray-100">
        <tr>
          <th scope="col" className="px-6 py-3">Index</th>
          <th scope="col" className="px-6 py-3">Key</th>
          <th scope="col" className="px-6 py-3">Name</th>
          <th scope="col" className="px-6 py-3">Description</th>
          <th scope="col" className="px-6 py-3">Formula</th>
          <th scope="col" className="px-6 py-3">Coordinate Rule</th>
        </tr>
      </thead>
      <tbody>
        {axes.map((axis) => (
          <tr key={axis.index} className="bg-white border-b hover:bg-gray-50">
            <td className="px-6 py-4 font-medium text-gray-900">{axis.index}</td>
            <td className="px-6 py-4 text-blue-600 font-semibold">{axis.key}</td>
            <td className="px-6 py-4">{axis.name}</td>
            <td className="px-6 py-4 text-xs">{axis.description}</td>
            <td className="px-6 py-4 font-mono text-xs text-purple-700">{axis.formula}</td>
            <td className="px-6 py-4 text-xs">{axis.coordinate_rule}</td>
          </tr>
        ))}
      </tbody>
    </table>
    {axes.length === 0 && (
      <p className="p-4 text-center text-gray-500">No axis metadata found.</p>
    )}
  </div>
);

export const AxisDisplayTable: React.FC = () => {
  const [axes, setAxes] = useState<AxisMetadata[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAxes = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchAxesMetadata();
        setAxes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred.");
        console.error("Failed to load axes:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadAxes();
  }, []);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;
  return <AxisTable axes={axes} />;
};
