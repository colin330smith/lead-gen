'use client';

/**
 * Admin dashboard header.
 * Displays system status and navigation.
 */

export function AdminHeader() {
  return (
    <header className="bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg sticky top-0 z-50">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🚀</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Local Lift</h1>
                <span className="text-sm text-primary-100">Admin Dashboard</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 bg-white/10 px-4 py-2 rounded-lg">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">System Operational</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

