'use client';

/**
 * Admin dashboard sidebar navigation.
 * Provides access to all admin features.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/admin', icon: '📊' },
  { name: 'Leads', href: '/admin/leads', icon: '🎯' },
  { name: 'Contractors', href: '/admin/contractors', icon: '👷' },
  { name: 'Territories', href: '/admin/territories', icon: '🗺️' },
  { name: 'Scoring', href: '/admin/scoring', icon: '⭐' },
  { name: 'Analytics', href: '/admin/analytics', icon: '📈' },
  { name: 'Model Refinement', href: '/admin/model', icon: '🔧' },
  { name: 'Data Ingestion', href: '/admin/ingestion', icon: '📥' },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gradient-to-b from-gray-50 to-white border-r border-gray-200 min-h-screen shadow-sm">
      <nav className="p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group',
                isActive
                  ? 'bg-primary-600 text-white font-semibold shadow-md transform scale-[1.02]'
                  : 'text-gray-700 hover:bg-gray-100 hover:shadow-sm'
              )}
            >
              <span className={cn(
                'text-xl transition-transform group-hover:scale-110',
                isActive ? 'drop-shadow-sm' : ''
              )}>{item.icon}</span>
              <span className={isActive ? 'text-white' : ''}>{item.name}</span>
              {isActive && (
                <div className="ml-auto w-2 h-2 bg-white rounded-full"></div>
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

