/**
 * Contractor leads page.
 * Displays leads assigned to the contractor.
 */

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Lead } from '@/lib/api-client';
import { formatDate, formatNumber, getScoreColor, cn } from '@/lib/utils';

export default function ContractorLeadsPage() {
  const contractorId = 1; // Placeholder - would come from auth
  const queryClient = useQueryClient();
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['contractor-leads', contractorId],
    queryFn: () => api.listLeads({ contractor_id: contractorId, limit: 100 }),
  });

  const submitFeedbackMutation = useMutation({
    mutationFn: (data: {
      lead_id: number;
      outcome: string;
      converted: boolean;
      conversion_value?: number;
    }) =>
      api.submitFeedback({
        lead_id: data.lead_id,
        contractor_id: contractorId,
        outcome: data.outcome,
        converted: data.converted,
        conversion_value: data.conversion_value,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contractor-leads', contractorId] });
      setSelectedLead(null);
    },
  });

  const handleSubmitFeedback = (lead: Lead, outcome: string, converted: boolean, value?: number) => {
    submitFeedbackMutation.mutate({
      lead_id: lead.id,
      outcome,
      converted,
      conversion_value: value,
    });
  };

  if (isLoading) {
    return <div className="text-center text-gray-500 py-8">Loading leads...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Leads</h1>
        <p className="text-gray-600 mt-2">Leads assigned to you</p>
      </div>

      <div className="bg-white rounded-lg shadow">
        {data && data.leads.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trade</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ZIP</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lead.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{lead.trade}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={cn('font-semibold', getScoreColor(lead.intent_score))}>
                        {(lead.intent_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {lead.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.zip_code || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedLead(lead)}
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        View / Feedback
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">No leads assigned</div>
        )}
      </div>

      {/* Feedback Modal */}
      {selectedLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Submit Feedback - Lead #{selectedLead.id}</h2>
              <button
                onClick={() => setSelectedLead(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Trade</p>
                  <p className="font-medium">{selectedLead.trade}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Intent Score</p>
                  <p className="font-medium">{(selectedLead.intent_score * 100).toFixed(1)}%</p>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm font-medium text-gray-700 mb-3">Outcome</p>
                <div className="grid grid-cols-2 gap-3">
                  {['won', 'lost', 'no_response', 'not_interested', 'wrong_lead'].map((outcome) => (
                    <button
                      key={outcome}
                      onClick={() => {
                        const converted = outcome === 'won';
                        const value = converted
                          ? prompt('Enter conversion value (optional):')
                          : undefined;
                        handleSubmitFeedback(
                          selectedLead,
                          outcome,
                          converted,
                          value ? parseFloat(value) : undefined
                        );
                      }}
                      disabled={submitFeedbackMutation.isPending}
                      className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 text-sm capitalize"
                    >
                      {outcome.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

