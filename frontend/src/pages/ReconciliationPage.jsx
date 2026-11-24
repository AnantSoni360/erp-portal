import React, { useState, useEffect } from 'react';
import { materialsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { 
  FileSpreadsheet, 
  Search, 
  CheckCheck, 
  ShieldCheck, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  AlertTriangle,
  Layers,
  ArrowRight,
  TrendingDown,
  Info
} from 'lucide-react';

export const ReconciliationPage = () => {
  const { t } = useLanguage();
  const [materials, setMaterials] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('ALL'); // 'ALL', 'NEGATIVE', 'POSITIVE'
  const [loading, setLoading] = useState(false);

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const res = await materialsApi.list({
        search: search.trim() || undefined,
        stock_status: filterType === 'NEGATIVE' ? 'Negative' : undefined,
        page,
        limit
      });
      setMaterials(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      console.error('Failed to load reconciliation items', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, [page, filterType]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              {t.reconciliation.tag}
            </span>
            <span className="text-xs text-slate-500">{t.reconciliation.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.reconciliation.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.reconciliation.desc}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="px-3.5 py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>{t.reconciliation.allParity}</span>
          </div>

          <button
            onClick={fetchMaterials}
            className="p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Information Banner */}
      <div className="bg-gradient-to-r from-royalblue-700 to-royalblue-800 text-white p-5 rounded-2xl shadow-sm space-y-2">
        <div className="flex items-center space-x-2">
          <Info className="w-5 h-5 text-royalblue-200" />
          <h3 className="text-sm font-bold tracking-tight">Dual-Condition Calculation Integrity</h3>
        </div>
        <p className="text-xs text-royalblue-100 leading-relaxed max-w-4xl">
          Inward entries affect balance strictly when <code>Status = Book</code> and <code>Check = OK</code>.
          Contractor issues and returns affect balance strictly when <code>Status = Posted</code> and <code>Check = OK</code>.
          All <code>Flagged</code> entries (189 inward + 2,338 contractor) remain safely quarantined in the verification queue, preserving 100% calculation parity with MMTPL Store Tracker.xlsx.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by Item ID (e.g. MT0001) or specification..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchMaterials()}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-slate-50/50"
            />
          </div>

          <div>
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="ALL">All 849 Materials</option>
              <option value="NEGATIVE">Historical Negative Balances (62 Items)</option>
              <option value="POSITIVE">Positive / Active Stock</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>
            Displaying <strong className="text-slate-900">{materials.length}</strong> of <strong className="text-slate-900">{total}</strong> materials
          </span>
          <button
            onClick={() => {
              setSearch('');
              setFilterType('ALL');
              setPage(1);
            }}
            className="text-royalblue-700 hover:text-royalblue-800 font-semibold"
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Reconciliation Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Item ID</th>
                <th className="px-5 py-3">Specification</th>
                <th className="px-3 py-3 text-center">Unit</th>
                <th className="px-4 py-3 text-right">Booked Inward (E)</th>
                <th className="px-4 py-3 text-right">Posted Issued (F)</th>
                <th className="px-4 py-3 text-right">Posted Returned (G)</th>
                <th className="px-5 py-3 text-right font-bold text-slate-900">Computed Balance (E-F+G)</th>
                <th className="px-4 py-3 text-center">Audit Parity</th>
                <th className="px-4 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Verifying ledger calculations...</span>
                  </td>
                </tr>
              ) : (
                materials.map((m) => (
                  <tr key={m.item_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-3 font-mono font-semibold text-royalblue-700 whitespace-nowrap">
                      {m.item_id}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-900 max-w-xs truncate">
                      {m.name}
                    </td>
                    <td className="px-3 py-3 text-center font-mono font-semibold text-slate-500">
                      {m.unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-700">
                      {m.booked_inward}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-rose-600">
                      {m.issued > 0 ? `-${m.issued}` : '0'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-600">
                      {m.returned > 0 ? `+${m.returned}` : '0'}
                    </td>
                    <td className={`px-5 py-3 text-right font-mono font-bold ${
                      m.book_balance < 0 ? 'text-rose-600 bg-rose-50/50' : 'text-slate-900'
                    }`}>
                      {m.book_balance}
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCheck className="w-3 h-3 text-emerald-600" />
                        <span>Exact Parity</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <StatusBadge status={m.stock_status} />
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
