/**
 * Contractor portal layout.
 * Provides navigation and structure for contractor interface.
 */

import { ContractorSidebar } from '@/components/contractor/ContractorSidebar';
import { ContractorHeader } from '@/components/contractor/ContractorHeader';

export default function ContractorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <ContractorHeader />
      <div className="flex">
        <ContractorSidebar />
        <main className="flex-1 p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

