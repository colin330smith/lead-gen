/**
 * Contractor territories page.
 * View assigned territories.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatDate } from '@/lib/utils';

export default function ContractorTerritoriesPage() {
  const contractorId = 1; // Placeholder

  const { data: territories, isLoading } = useQuery({
    queryKey: ['contractor-territories', contractorId],
    queryFn: () => api.getContractorTerritories(contractorId),
  });

  if (isLoading) {
    return <div className="text-center text-gray-500 py-8">Loading territories...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Territories</h1>
        <p className="text-gray-600 mt-2">Your exclusive territory assignments</p>
      </div>

      <div className="bg-white rounded-lg shadow">
        {territories && territories.territories.length > 0 ? (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {territories.territories.map((territory: any) => (
                <div
                  key={territory.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">ZIP {territory.zip_code}</h3>
                    {territory.is_exclusive && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Exclusive
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 capitalize">{territory.trade}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Assigned: {formatDate(territory.assigned_at)}
                  </p>
                  <p className="text-xs text-gray-500">Status: {territory.status}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">No territories assigned</div>
        )}
      </div>
    </div>
  );
}

