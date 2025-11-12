/**
 * Contractor dashboard home page.
 * Displays contractor-specific metrics and leads.
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatNumber, formatPercent, formatCurrency } from '@/lib/utils';
import { DashboardStatsCard } from '@/components/admin/DashboardStatsCard';

export default function ContractorDashboardPage() {
  // In production, contractor_id would come from auth context
  const contractorId = 1; // Placeholder

  const { data: stats, isLoading } = useQuery({
    queryKey: ['contractor-dashboard-stats', contractorId],
    queryFn: () => api.getDashboardStats(contractorId),
  });

  const { data: performance } = useQuery({
    queryKey: ['contractor-performance', contractorId],
    queryFn: () => api.getContractorPerformance(contractorId, 30),
    enabled: !isLoading,
  });

  const { data: recentLeads } = useQuery({
    queryKey: ['contractor-leads', contractorId],
    queryFn: () => api.listLeads({ contractor_id: contractorId, limit: 10 }),
    enabled: !isLoading,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Your leads and performance overview</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardStatsCard
          title="Total Leads"
          value={formatNumber(stats?.total_leads)}
          subtitle="All time"
        />
        <DashboardStatsCard
          title="Conversion Rate"
          value={formatPercent(performance?.conversion_rate)}
          subtitle="Last 30 days"
        />
        <DashboardStatsCard
          title="Leads Delivered"
          value={formatNumber(performance?.leads_delivered)}
          subtitle="Last 30 days"
        />
        <DashboardStatsCard
          title="Total Revenue"
          value={formatCurrency(performance?.total_revenue)}
          subtitle="Last 30 days"
        />
      </div>

      {/* Recent Leads */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Leads</h2>
        </div>
        <div className="p-6">
          {recentLeads && recentLeads.leads.length > 0 ? (
            <div className="space-y-3">
              {recentLeads.leads.map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">Lead #{lead.id}</p>
                    <p className="text-sm text-gray-500">{lead.trade} • Score: {(lead.intent_score * 100).toFixed(1)}%</p>
                  </div>
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full ${
                      lead.status === 'delivered'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {lead.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No recent leads</p>
          )}
        </div>
      </div>
    </div>
  );
}

