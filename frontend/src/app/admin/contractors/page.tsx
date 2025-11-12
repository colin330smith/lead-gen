/**
 * Admin contractors management page.
 * Comprehensive interface for managing contractors and territories.
 */

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Contractor } from '@/lib/api-client';
import { formatDate } from '@/lib/utils';
import { ContractorsTable } from '@/components/admin/ContractorsTable';
import { CreateContractorModal } from '@/components/admin/CreateContractorModal';
import { ContractorDetailModal } from '@/components/admin/ContractorDetailModal';

export default function AdminContractorsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedContractor, setSelectedContractor] = useState<Contractor | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['contractors'],
    queryFn: () => api.listContractors({ limit: 100 }),
  });

  const handleContractorClick = (contractor: Contractor) => {
    setSelectedContractor(contractor);
    setIsDetailModalOpen(true);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading contractors. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Contractors</h1>
          <p className="text-gray-600 mt-2">Manage contractors and territories</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 font-medium"
        >
          + Add Contractor
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading contractors...</div>
        ) : (
          <ContractorsTable
            contractors={data?.contractors || []}
            onContractorClick={handleContractorClick}
          />
        )}
      </div>

      {isCreateModalOpen && (
        <CreateContractorModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}

      {isDetailModalOpen && selectedContractor && (
        <ContractorDetailModal
          contractor={selectedContractor}
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setSelectedContractor(null);
          }}
        />
      )}
    </div>
  );
}

