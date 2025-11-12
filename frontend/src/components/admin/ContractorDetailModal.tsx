'use client';

/**
 * Contractor detail modal.
 * Displays contractor information, territories, and performance.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Contractor } from '@/lib/api-client';
import { formatDate, formatPercent, formatCurrency } from '@/lib/utils';

interface ContractorDetailModalProps {
  contractor: Contractor;
  isOpen: boolean;
  onClose: () => void;
}

export function ContractorDetailModal({
  contractor,
  isOpen,
  onClose,
}: ContractorDetailModalProps) {
  const queryClient = useQueryClient();
  const [newTerritory, setNewTerritory] = useState({ zip_code: '', trade: '', is_exclusive: true });

  const { data: territories } = useQuery({
    queryKey: ['contractor-territories', contractor.id],
    queryFn: () => api.getContractorTerritories(contractor.id),
    enabled: isOpen,
  });

  const { data: performance } = useQuery({
    queryKey: ['contractor-performance', contractor.id],
    queryFn: () => api.getContractorPerformance(contractor.id, 30),
    enabled: isOpen,
  });

  const assignTerritoryMutation = useMutation({
    mutationFn: () =>
      api.assignTerritory(contractor.id, newTerritory.zip_code, newTerritory.trade, newTerritory.is_exclusive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contractor-territories', contractor.id] });
      setNewTerritory({ zip_code: '', trade: '', is_exclusive: true });
    },
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">{contractor.company_name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Contractor Info */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Contact Name</h3>
              <p className="text-lg text-gray-900">{contractor.contact_name || 'N/A'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Email</h3>
              <p className="text-lg text-gray-900">{contractor.email || 'N/A'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Trades</h3>
              <p className="text-lg text-gray-900">{contractor.trades}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Subscription Tier</h3>
              <p className="text-lg text-gray-900 capitalize">{contractor.subscription_tier}</p>
            </div>
          </div>

          {/* Performance Metrics */}
          {performance && (
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance (Last 30 Days)</h3>
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Leads Assigned</p>
                  <p className="text-2xl font-bold text-gray-900">{performance.leads_assigned}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Leads Delivered</p>
                  <p className="text-2xl font-bold text-gray-900">{performance.leads_delivered}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Conversion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatPercent(performance.conversion_rate)}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(performance.total_revenue)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Territories */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Territories</h3>
            {territories && territories.territories.length > 0 ? (
              <div className="space-y-2">
                {territories.territories.map((territory: any) => (
                  <div
                    key={territory.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <span className="font-medium">{territory.zip_code}</span>
                      <span className="text-gray-500 ml-2">• {territory.trade}</span>
                      {territory.is_exclusive && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          Exclusive
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">{territory.status}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No territories assigned</p>
            )}

            {/* Add Territory Form */}
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Assign New Territory</h4>
              <div className="grid grid-cols-3 gap-3">
                <input
                  type="text"
                  placeholder="ZIP Code"
                  value={newTerritory.zip_code}
                  onChange={(e) => setNewTerritory({ ...newTerritory, zip_code: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <select
                  value={newTerritory.trade}
                  onChange={(e) => setNewTerritory({ ...newTerritory, trade: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">Select Trade</option>
                  <option value="roofing">Roofing</option>
                  <option value="hvac">HVAC</option>
                  <option value="siding">Siding</option>
                  <option value="electrical">Electrical</option>
                </select>
                <button
                  onClick={() => {
                    if (newTerritory.zip_code && newTerritory.trade) {
                      assignTerritoryMutation.mutate();
                    }
                  }}
                  disabled={!newTerritory.zip_code || !newTerritory.trade || assignTerritoryMutation.isPending}
                  className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm"
                >
                  {assignTerritoryMutation.isPending ? 'Assigning...' : 'Assign'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

