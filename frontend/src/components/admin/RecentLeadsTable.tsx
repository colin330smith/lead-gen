'use client';

/**
 * Table component for displaying recent leads.
 * Optimized for performance and clarity.
 */

import Link from 'next/link';
import { Lead } from '@/lib/api-client';
import { formatDate, formatNumber, getScoreColor, getStatusColor, cn } from '@/lib/utils';

interface RecentLeadsTableProps {
  leads: Lead[];
}

export function RecentLeadsTable({ leads }: RecentLeadsTableProps) {
  if (leads.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        No leads found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-100">
        <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
          <tr>
            <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
              ID
            </th>
            <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
              Trade
            </th>
            <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
              Score
            </th>
            <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
              Status
            </th>
            <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-200">
              ZIP
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
            <tr key={lead.id} className={cn(
              "hover:bg-gradient-to-r hover:from-primary-50 hover:to-blue-50 transition-all duration-150",
              index % 2 === 0 ? "bg-white" : "bg-gray-50/30"
            )}>
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
                  <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[50px]">
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
                  <span className={cn('text-sm font-bold', getScoreColor(lead.intent_score))}>
                    {(lead.intent_score * 100).toFixed(1)}%
                  </span>
                </div>
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
                <span className="text-sm text-gray-600">{formatDate(lead.generated_at)}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Link
                  href={`/admin/leads/${lead.id}`}
                  className="px-3 py-1.5 bg-primary-600 text-white text-xs font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

