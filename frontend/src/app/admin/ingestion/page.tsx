/**
 * Admin data ingestion monitoring page.
 * Monitor ingestion pipelines and data quality.
 */

'use client';

export default function AdminIngestionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Ingestion</h1>
        <p className="text-gray-600 mt-2">Monitor data ingestion pipelines and quality</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Property Universe</h3>
            <p className="text-sm text-gray-600">TCAD property data ingestion</p>
            <p className="text-xs text-gray-500 mt-2">Status: Operational</p>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Signal Data Sources</h3>
            <div className="space-y-2 mt-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Austin 311</span>
                <span className="text-green-600 font-semibold">Active</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Code Compliance</span>
                <span className="text-green-600 font-semibold">Active</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">NOAA Storm Events</span>
                <span className="text-green-600 font-semibold">Active</span>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Ingestion Controls</h3>
            <p className="text-sm text-gray-600 mb-3">
              Run ingestion scripts from the backend to update data:
            </p>
            <code className="block bg-gray-50 p-3 rounded text-sm">
              python -m backend.src.ingestion.property_universe
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}

