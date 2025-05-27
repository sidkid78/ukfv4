import { AxisDisplayTable } from '@/components/AxisDisplayTable';

export default function AxisExplorerPage() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Axis Explorer</h1>
        <p className="text-gray-600">
          Explore and understand the available axes in the system. Each axis represents a dimension
          that can be used for analysis and visualization.
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <AxisDisplayTable />
      </div>
    </main>
  );
}
