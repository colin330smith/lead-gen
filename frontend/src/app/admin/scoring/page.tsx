/**
 * Admin scoring page.
 * Score properties, view high-intent leads, batch operations.
 */

'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatNumber, getScoreColor, cn } from '@/lib/utils';

export default function AdminScoringPage() {
  const [selectedTrade, setSelectedTrade] = useState<string>('');
  const [minScore, setMinScore] = useState<number>(0.6);

  const { data: highIntentLeads, isLoading } = useQuery({
    queryKey: ['high-intent-leads', selectedTrade, minScore],
    queryFn: () => api.getHighIntentProperties(minScore, selectedTrade || undefined, 100),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Scoring System</h1>
          <p className="text-gray-600 mt-2">Property scoring and high-intent lead identification</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Trade</label>
            <select
              value={selectedTrade}
              onChange={(e) => setSelectedTrade(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Trades</option>
              <option value="roofing">Roofing</option>
              <option value="hvac">HVAC</option>
              <option value="siding">Siding</option>
              <option value="electrical">Electrical</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Score</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={minScore}
              onChange={(e) => setMinScore(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      </div>

      {/* High Intent Leads */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            High Intent Properties (Score ≥ {(minScore * 100).toFixed(0)}%)
          </h2>
        </div>
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : highIntentLeads && highIntentLeads.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prop ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trade</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ZIP</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {highIntentLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lead.prop_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{lead.trade || 'N/A'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={cn('font-semibold', getScoreColor(lead.intent_score))}>
                        {(lead.intent_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.zip_code || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button className="text-primary-600 hover:text-primary-800 font-medium">
                        Generate Lead
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">No high-intent properties found</div>
        )}
      </div>
    </div>
  );
}

