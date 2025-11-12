'use client';

/**
 * Comprehensive leads table component.
 * Optimized for performance with large datasets.
 */

import { Lead } from '@/lib/api-client';
import { formatDate, formatNumber, getScoreColor, getStatusColor, cn } from '@/lib/utils';

interface LeadsTableProps {
  leads: Lead[];
  onLeadClick: (lead: Lead) => void;
  total: number;
  limit: number;
  offset: number;
  onPageChange: (offset: number) => void;
}

export function LeadsTable({
  leads,
  onLeadClick,
  total,
  limit,
  offset,
  onPageChange,
}: LeadsTableProps) {
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  if (leads.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No leads found matching your criteria
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                ID
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Trade
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Intent Score
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Quality Score
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Status
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                ZIP Code
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Signals
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Generated
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {leads.map((lead, index) => (
              <tr
                key={lead.id}
                className={cn(
                  "hover:bg-gradient-to-r hover:from-primary-50 hover:to-blue-50 cursor-pointer transition-all duration-150",
                  index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                )}
                onClick={() => onLeadClick(lead)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-bold text-gray-900">#{lead.id}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 capitalize">
                    {lead.trade}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[60px]">
                      <div
                        className={cn(
                          "h-2 rounded-full transition-all",
                          lead.intent_score >= 0.8 ? "bg-green-500" :
                          lead.intent_score >= 0.6 ? "bg-blue-500" :
                          lead.intent_score >= 0.4 ? "bg-yellow-500" : "bg-red-500"
                        )}
                        style={{ width: `${lead.intent_score * 100}%` }}
                      ></div>
                    </div>
                    <span className={cn('text-sm font-bold min-w-[50px]', getScoreColor(lead.intent_score))}>
                      {(lead.intent_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-700">
                  {lead.quality_score ? (
                    <span className="text-gray-600">{(lead.quality_score * 100).toFixed(1)}%</span>
                  ) : (
                    <span className="text-gray-400">N/A</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={cn(
                      'inline-flex px-3 py-1 text-xs font-bold rounded-full shadow-sm',
                      getStatusColor(lead.status)
                    )}
                  >
                    {lead.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-medium text-gray-700">{lead.zip_code || 'N/A'}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600 font-medium">{formatNumber(lead.signal_count)}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600">{formatDate(lead.generated_at)}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onLeadClick(lead);
                    }}
                    className="px-4 py-1.5 bg-primary-600 text-white text-sm font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-sm hover:shadow"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm font-medium text-gray-700">
            Showing <span className="font-bold">{offset + 1}</span> to <span className="font-bold">{Math.min(offset + limit, total)}</span> of <span className="font-bold">{total}</span> leads
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-5 py-2 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 hover:border-primary-500 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              ← Previous
            </button>
            <span className="px-5 py-2 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-lg">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(offset + limit)}
              disabled={offset + limit >= total}
              className="px-5 py-2 border-2 border-gray-300 rounded-lg text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 hover:border-primary-500 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

