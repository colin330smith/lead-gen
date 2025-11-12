/**
 * Admin leads management page.
 * Comprehensive interface for managing all leads.
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, Lead } from '@/lib/api-client';
import { formatDate, formatNumber, getScoreColor, getStatusColor, cn } from '@/lib/utils';
import { LeadsFilterBar } from '@/components/admin/LeadsFilterBar';
import { LeadsTable } from '@/components/admin/LeadsTable';
import { LeadDetailModal } from '@/components/admin/LeadDetailModal';

export default function AdminLeadsPage() {
  const [filters, setFilters] = useState({
    trade: '',
    status: '',
    contractor_id: '',
    min_score: 0.0,
    limit: 100,
    offset: 0,
  });

  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['leads', filters],
    queryFn: async () => {
      try {
        // Clean filters - remove empty strings
        const cleanFilters: any = {
          limit: filters.limit,
          offset: filters.offset,
          min_score: filters.min_score,
        };
        
        if (filters.trade) cleanFilters.trade = filters.trade;
        if (filters.status) cleanFilters.status = filters.status;
        if (filters.contractor_id) cleanFilters.contractor_id = parseInt(filters.contractor_id);
        
        console.log('Fetching leads with filters:', cleanFilters);
        const result = await api.listLeads(cleanFilters);
        console.log('Leads fetched successfully:', result?.total || 0, 'leads');
        return result;
      } catch (err: any) {
        console.error('Error fetching leads:', err);
        console.error('Error details:', err.response?.data || err.message);
        throw err;
      }
    },
    retry: 1,
    retryDelay: 1000,
    staleTime: 30000,
  });

  const handleLeadClick = (lead: Lead) => {
    setSelectedLead(lead);
    setIsModalOpen(true);
  };

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, offset: 0 }));
  };

  const handlePageChange = (newOffset: number) => {
    setFilters((prev) => ({ ...prev, offset: newOffset }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 border border-primary-100">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <span className="text-4xl">🎯</span>
            <span>Leads Management</span>
          </h1>
          <p className="text-gray-600 mt-2 font-medium">Manage and track all generated leads</p>
        </div>
        <div className="bg-white px-6 py-3 rounded-lg shadow-md border border-gray-200">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Leads</div>
          <div className="text-2xl font-bold text-primary-600 mt-1">
            {isLoading ? '...' : formatNumber(data?.total || 0)}
          </div>
        </div>
      </div>

      <LeadsFilterBar filters={filters} onFilterChange={handleFilterChange} />

      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
            <p className="text-gray-600 font-medium">Loading leads...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 inline-block max-w-md">
              <div className="text-4xl mb-3">⚠️</div>
              <p className="text-red-800 font-semibold mb-2">Error loading leads</p>
              <p className="text-red-600 text-sm mb-4">Please try again</p>
              <button
                onClick={() => refetch()}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold shadow-md transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <LeadsTable
            leads={data?.leads || []}
            onLeadClick={handleLeadClick}
            total={data?.total || 0}
            limit={filters.limit}
            offset={filters.offset}
            onPageChange={handlePageChange}
          />
        )}
      </div>

      {isModalOpen && selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedLead(null);
          }}
        />
      )}
    </div>
  );
}
