import React, { useState, useEffect } from 'react';
import { auditApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { 
  History, 
  Search, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  UserCheck, 
  ShieldAlert,
  FileCheck2,
  Calendar,
  Layers
} from 'lucide-react';

export const AuditPage = () => {
  const { t } = useLanguage();
  const [audits, setAudits] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [entityType, setEntityType] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAudits = async () => {
    setLoading(true);
    try {
      const res = await auditApi.list({
        entity_type: entityType || undefined,
        page,
        limit
      });
      setAudits(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      console.error('Failed to load audits', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
  }, [page, entityType]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {t.audit.tag}
            </span>
            <span className="text-xs text-slate-500">{t.audit.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.audit.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.audit.desc}
          </p>
        </div>

        <button
          onClick={fetchAudits}
          className="p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-slate-700">Filter Entity:</span>
          <select
            value={entityType}
            onChange={(e) => {
              setEntityType(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-royalblue-500"
          >
            <option value="">All Entities</option>
            <option value="inward">Inward Consignments</option>
            <option value="contractor_tx">Contractor Transactions</option>
            <option value="material">Material Master SKUs</option>
          </select>
        </div>

        <span className="text-slate-500">
          Total Recorded Audit Events: <strong className="text-slate-900">{total}</strong>
        </span>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Entity Type</th>
                <th className="px-4 py-3">Reference ID</th>
                <th className="px-4 py-3">Action Type</th>
                <th className="px-6 py-3">Justification Reason</th>
                <th className="px-6 py-3">Values Modified (Old vs New)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Loading audit records...</span>
                  </td>
                </tr>
              ) : audits.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    <History className="w-6 h-6 mx-auto text-slate-300 mb-2" />
                    <span>No audit entries logged yet.</span>
                  </td>
                </tr>
              ) : (
                audits.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-3 text-slate-500 whitespace-nowrap font-mono">
                      {a.timestamp ? a.timestamp.replace('T', ' ').split('.')[0] : '-'}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-900 whitespace-nowrap">
                      {a.changed_by}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600 uppercase text-[10px]">
                      {a.entity_type}
                    </td>
                    <td className="px-4 py-3 font-mono font-medium text-royalblue-700">
                      {a.entity_id}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        a.action === 'CREATE' ? 'bg-emerald-50 text-emerald-700' :
                        a.action === 'VERIFY_REVIEW' ? 'bg-royalblue-50 text-royalblue-700' :
                        a.action === 'OVERRIDE' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                        {a.action}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-800 max-w-sm truncate" title={a.reason}>
                      {a.reason}
                    </td>
                    <td className="px-6 py-3 font-mono text-[11px] text-slate-500 max-w-xs truncate" title={`Old: ${a.old_values || 'None'} | New: ${a.new_values || 'None'}`}>
                      {a.old_values && <span>Old: {a.old_values} | </span>}
                      <span>New: {a.new_values}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-6 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 bg-slate-50/50">
          <span>
            Page <strong className="text-slate-900">{page}</strong> of <strong className="text-slate-900">{totalPages}</strong>
          </span>

          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1 text-slate-700 font-medium"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1 text-slate-700 font-medium"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
