'use client';

/**
 * Lead detail modal component.
 * Displays comprehensive lead information and actions.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Lead } from '@/lib/api-client';
import { formatDate, formatCurrency, formatNumber, getScoreColor, getStatusColor, cn } from '@/lib/utils';

interface LeadDetailModalProps {
  lead: Lead;
  isOpen: boolean;
  onClose: () => void;
}

export function LeadDetailModal({ lead, isOpen, onClose }: LeadDetailModalProps) {
  const queryClient = useQueryClient();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const assignMutation = useMutation({
    mutationFn: (contractorId: number) => api.assignLead(lead.id, contractorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setActionLoading(null);
    },
  });

  const deliverMutation = useMutation({
    mutationFn: () => api.deliverLead(lead.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setActionLoading(null);
    },
  });

  const convertMutation = useMutation({
    mutationFn: (value?: number) => api.convertLead(lead.id, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setActionLoading(null);
    },
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border-2 border-gray-100">
        <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-5 flex items-center justify-between rounded-t-2xl">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🎯</span>
            <h2 className="text-2xl font-bold text-white">Lead Details</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-3xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/20 transition-colors"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6 bg-gray-50">
          {/* Lead Info */}
          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <span>📋</span>
              <span>Lead Information</span>
            </h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Lead ID</h4>
                <p className="text-xl font-bold text-gray-900">#{lead.id}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Trade</h4>
                <p className="text-xl font-bold text-gray-900 capitalize">{lead.trade}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Intent Score</h4>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className={cn(
                        "h-3 rounded-full",
                        lead.intent_score >= 0.8 ? "bg-green-500" :
                        lead.intent_score >= 0.6 ? "bg-blue-500" :
                        lead.intent_score >= 0.4 ? "bg-yellow-500" : "bg-red-500"
                      )}
                      style={{ width: `${lead.intent_score * 100}%` }}
                    ></div>
                  </div>
                  <p className={cn('text-lg font-bold min-w-[60px]', getScoreColor(lead.intent_score))}>
                    {(lead.intent_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Quality Score</h4>
                <p className="text-xl font-bold text-gray-900">
                  {lead.quality_score ? `${(lead.quality_score * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Status</h4>
                <span className={cn('inline-flex px-4 py-2 text-sm font-bold rounded-full shadow-sm', getStatusColor(lead.status))}>
                  {lead.status}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">ZIP Code</h4>
                <p className="text-xl font-bold text-gray-900">{lead.zip_code || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Signal Summary */}
          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <span>📊</span>
              <span>Signal Summary</span>
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-5 rounded-xl border border-blue-200">
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">Total Signals</p>
                <p className="text-3xl font-bold text-blue-900">{formatNumber(lead.signal_count)}</p>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 p-5 rounded-xl border border-red-200">
                <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">Violations</p>
                <p className="text-3xl font-bold text-red-900">{formatNumber(lead.violation_count)}</p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-5 rounded-xl border border-purple-200">
                <p className="text-xs font-semibold text-purple-700 uppercase tracking-wide mb-2">311 Requests</p>
                <p className="text-3xl font-bold text-purple-900">{formatNumber(lead.request_count)}</p>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <span>⏱️</span>
              <span>Timeline</span>
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center bg-gray-50 rounded-lg p-3">
                <span className="text-sm font-semibold text-gray-600">Generated:</span>
                <span className="text-sm font-bold text-gray-900">{formatDate(lead.generated_at)}</span>
              </div>
              {lead.assigned_at && (
                <div className="flex justify-between items-center bg-blue-50 rounded-lg p-3">
                  <span className="text-sm font-semibold text-blue-600">Assigned:</span>
                  <span className="text-sm font-bold text-blue-900">{formatDate(lead.assigned_at)}</span>
                </div>
              )}
              {lead.delivered_at && (
                <div className="flex justify-between items-center bg-green-50 rounded-lg p-3">
                  <span className="text-sm font-semibold text-green-600">Delivered:</span>
                  <span className="text-sm font-bold text-green-900">{formatDate(lead.delivered_at)}</span>
                </div>
              )}
              {lead.converted_at && (
                <div className="flex justify-between items-center bg-purple-50 rounded-lg p-3">
                  <span className="text-sm font-semibold text-purple-600">Converted:</span>
                  <span className="text-sm font-bold text-purple-900">{formatDate(lead.converted_at)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <span>⚡</span>
              <span>Actions</span>
            </h3>
            <div className="flex space-x-3">
              {lead.status === 'generated' && (
                <button
                  onClick={() => {
                    const contractorId = prompt('Enter Contractor ID:');
                    if (contractorId) {
                      setActionLoading('assign');
                      assignMutation.mutate(parseInt(contractorId));
                    }
                  }}
                  disabled={actionLoading !== null}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-semibold shadow-md hover:shadow-lg transition-all"
                >
                  {actionLoading === 'assign' ? 'Assigning...' : 'Assign to Contractor'}
                </button>
              )}
              {lead.status === 'assigned' && (
                <button
                  onClick={() => {
                    setActionLoading('deliver');
                    deliverMutation.mutate();
                  }}
                  disabled={actionLoading !== null}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-semibold shadow-md hover:shadow-lg transition-all"
                >
                  {actionLoading === 'deliver' ? 'Delivering...' : 'Deliver Lead'}
                </button>
              )}
              {lead.status === 'delivered' && (
                <button
                  onClick={() => {
                    const value = prompt('Enter conversion value (optional):');
                    setActionLoading('convert');
                    convertMutation.mutate(value ? parseFloat(value) : undefined);
                  }}
                  disabled={actionLoading !== null}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-semibold shadow-md hover:shadow-lg transition-all"
                >
                  {actionLoading === 'convert' ? 'Converting...' : 'Mark as Converted'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

