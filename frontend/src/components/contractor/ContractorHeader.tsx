'use client';

/**
 * Contractor portal header.
 */

export function ContractorHeader() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">Local Lift</h1>
            <span className="text-sm text-gray-500">Contractor Portal</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">Contractor Dashboard</div>
          </div>
        </div>
      </div>
    </header>
  );
}

