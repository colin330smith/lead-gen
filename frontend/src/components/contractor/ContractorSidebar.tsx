'use client';

/**
 * Contractor portal sidebar navigation.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/contractor', icon: '📊' },
  { name: 'My Leads', href: '/contractor/leads', icon: '🎯' },
  { name: 'Territories', href: '/contractor/territories', icon: '🗺️' },
  { name: 'Performance', href: '/contractor/performance', icon: '📈' },
  { name: 'Settings', href: '/contractor/settings', icon: '⚙️' },
];

export function ContractorSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <nav className="p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700 font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
              )}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

