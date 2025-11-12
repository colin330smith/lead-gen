/**
 * Admin territories management page.
 * View and manage contractor territory assignments.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatDate } from '@/lib/utils';

export default function AdminTerritoriesPage() {
  const { data: contractors, isLoading } = useQuery({
    queryKey: ['contractors'],
    queryFn: () => api.listContractors({ limit: 100 }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Territory Management</h1>
        <p className="text-gray-600 mt-2">Manage contractor territory assignments and exclusivity</p>
      </div>

      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading territories...</div>
        ) : (
          <div className="p-6">
            <p className="text-gray-600 mb-4">
              Select a contractor from the contractors page to view and manage their territories.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {contractors?.contractors.map((contractor) => (
                <div
                  key={contractor.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                  <h3 className="font-semibold text-gray-900">{contractor.company_name}</h3>
                  <p className="text-sm text-gray-500 mt-1">ID: {contractor.id}</p>
                  <p className="text-sm text-gray-500">Trades: {contractor.trades}</p>
                  <a
                    href={`/admin/contractors?view=${contractor.id}`}
                    className="text-primary-600 hover:text-primary-800 text-sm font-medium mt-2 inline-block"
                  >
                    View Territories →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

