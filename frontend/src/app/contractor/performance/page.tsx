/**
 * Contractor performance page.
 * Displays contractor-specific performance metrics.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatNumber, formatPercent, formatCurrency } from '@/lib/utils';
import { DashboardStatsCard } from '@/components/admin/DashboardStatsCard';

export default function ContractorPerformancePage() {
  const contractorId = 1; // Placeholder

  const { data: performance, isLoading } = useQuery({
    queryKey: ['contractor-performance', contractorId],
    queryFn: () => api.getContractorPerformance(contractorId, 30),
  });

  const { data: feedbackStats } = useQuery({
    queryKey: ['contractor-feedback-stats', contractorId],
    queryFn: () => api.getFeedbackStats({ contractor_id: contractorId }),
  });

  if (isLoading) {
    return <div className="text-center text-gray-500 py-8">Loading performance data...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Performance</h1>
        <p className="text-gray-600 mt-2">Your lead performance and conversion metrics</p>
      </div>

      {performance && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <DashboardStatsCard
            title="Leads Assigned"
            value={formatNumber(performance.leads_assigned)}
            subtitle="Last 30 days"
          />
          <DashboardStatsCard
            title="Leads Delivered"
            value={formatNumber(performance.leads_delivered)}
            subtitle="Last 30 days"
          />
          <DashboardStatsCard
            title="Conversion Rate"
            value={formatPercent(performance.conversion_rate)}
            subtitle="Last 30 days"
          />
          <DashboardStatsCard
            title="Total Revenue"
            value={formatCurrency(performance.total_revenue)}
            subtitle="Last 30 days"
          />
        </div>
      )}

      {feedbackStats && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Feedback Summary</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">Total Feedback</p>
              <p className="text-2xl font-bold text-gray-900">{feedbackStats.total_feedback}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatPercent(feedbackStats.conversion_rate)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Quality Rating</p>
              <p className="text-2xl font-bold text-gray-900">
                {feedbackStats.avg_ratings.lead_quality?.toFixed(1) || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

