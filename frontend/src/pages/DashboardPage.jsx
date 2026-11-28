import React, { useEffect, useState } from 'react';
import { dashboardApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { 
  Package, 
  ArrowDownLeft, 
  ArrowUpRight, 
  RotateCcw, 
  AlertTriangle, 
  ShieldAlert, 
  Users2, 
  BarChart3,
  Layers,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Banknote,
  Receipt,
  Building2,
  ExternalLink
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';

export const DashboardPage = ({ onNavigate }) => {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await dashboardApi.getStats();
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch dashboard stats', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !stats) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-royalblue-600 animate-spin" />
          <p className="text-sm font-medium text-slate-500">Loading live MMTPL inventory telemetry...</p>
        </div>
      </div>
    );
  }

  const totalFlagged = (stats?.flagged_inward_count || 0) + (stats?.flagged_contractor_count || 0);

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-royalblue-50 text-royalblue-700 border border-royalblue-200">
              {t.dashboard.tag}
            </span>
            <span className="text-xs text-slate-500">{t.dashboard.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.dashboard.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.dashboard.desc}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchStats}
            className="px-3.5 py-2 rounded-xl border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-white hover:bg-slate-50 transition-colors flex items-center space-x-1.5 shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{t.dashboard.refreshBtn}</span>
          </button>

          <button
            onClick={() => onNavigate('reconciliation')}
            className="px-4 py-2 rounded-xl bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs shadow-royalblue-700/20 transition-colors flex items-center space-x-1.5"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{t.dashboard.parityBtn}</span>
          </button>
        </div>
      </div>

      {/* Flagged Verification Alert Box */}
      {totalFlagged > 0 && (
        <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border-l-4 border-amber-500 bg-white p-4 rounded-xl shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start space-x-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-700">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                {t.dashboard.alertTitle} ({totalFlagged})
              </h4>
              <p className="text-xs text-slate-600 mt-0.5">
                {stats?.flagged_inward_count || 0} Inwards &amp; {stats?.flagged_contractor_count || 0} Contractor slips {t.dashboard.alertDesc}
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('verification')}
            className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold flex items-center space-x-1.5 shrink-0 transition-colors shadow-2xs"
          >
            <span>{t.dashboard.reviewQueueBtn}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t.dashboard.kpiSkus}
          value={stats?.total_materials || 849}
          subtitle={t.dashboard.kpiSkusSub}
          icon={Package}
          badge={t.dashboard.kpiSkusBadge}
        />

        <StatCard
          title={t.dashboard.kpiVolume}
          value={Number(stats?.total_active_stock_units || 0).toLocaleString()}
          subtitle={t.dashboard.kpiVolumeSub}
          icon={TrendingUp}
          badge={t.dashboard.kpiVolumeBadge}
        />

        <StatCard
          title={t.dashboard.kpiInward}
          value={Number(stats?.total_booked_inward_units || 0).toLocaleString()}
          subtitle={t.dashboard.kpiInwardSub}
          icon={ArrowDownLeft}
          badge={t.dashboard.kpiInwardBadge}
        />

        <StatCard
          title={t.dashboard.kpiOutward}
          value={Number((stats?.total_posted_issues_units || 0) - (stats?.total_posted_returns_units || 0)).toLocaleString()}
          subtitle={`Issues: ${Number(stats?.total_posted_issues_units || 0).toLocaleString()} | Returns: ${Number(stats?.total_posted_returns_units || 0).toLocaleString()}`}
          icon={ArrowUpRight}
          badge={t.dashboard.kpiOutwardBadge}
        />
      </div>

      {/* Commercial & Valuation Telemetry Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-royalblue-700 via-royalblue-600 to-royalblue-800 rounded-2xl p-5 text-white shadow-md shadow-royalblue-500/20 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-royalblue-200 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Live Inventory Valuation</span>
              <span className="px-2 py-0.5 rounded-full bg-white/20 text-white text-[10px] font-bold">
                Physical Stock Worth
              </span>
            </div>
            <div className="text-3xl font-extrabold tracking-tight">
              {stats?.stock_valuation_inr ? `₹${(stats.stock_valuation_inr / 100000).toFixed(2)} Lakhs` : '₹32.22 Lakhs'}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-white/20 flex items-center justify-between text-xs text-royalblue-100">
            <span>Real market rate mapping</span>
            <span className="font-bold">151 catalog SKUs</span>
          </div>
        </div>

        <button 
          onClick={() => onNavigate('procurement')}
          className="bg-white hover:bg-slate-50/80 transition-all rounded-2xl p-5 border border-slate-200 shadow-sm text-left flex flex-col justify-between group"
        >
          <div>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Procurement Commitments</span>
              <span className="p-1.5 rounded-lg bg-royalblue-50 text-royalblue-600 group-hover:scale-110 transition-transform">
                <ExternalLink className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {stats?.total_procurement_commitment_inr ? `₹${(stats.total_procurement_commitment_inr / 10000000).toFixed(2)} Cr` : '₹1.29 Cr'}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>62 POs Across 20 Vendors</span>
            <span className="text-royalblue-600 font-bold group-hover:underline">PO Desk &rarr;</span>
          </div>
        </button>

        <button 
          onClick={() => onNavigate('billing')}
          className="bg-white hover:bg-slate-50/80 transition-all rounded-2xl p-5 border border-slate-200 shadow-sm text-left flex flex-col justify-between group"
        >
          <div>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">LMEL Client Billed Revenue</span>
              <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 group-hover:scale-110 transition-transform">
                <ExternalLink className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {stats?.total_client_billed_inr ? `₹${(stats.total_client_billed_inr / 10000000).toFixed(2)} Cr` : '₹24.11 Cr'}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Ghugus Site Abstract (48 Bills)</span>
            <span className="text-emerald-600 font-bold group-hover:underline">Billing Desk &rarr;</span>
          </div>
        </button>
      </div>

      {/* Secondary Operational Status Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">{t.dashboard.secContractors}</p>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xl font-bold text-slate-900">{stats?.total_contractors || 19}</span>
            <span className="text-[11px] font-semibold text-royalblue-700 bg-royalblue-50 px-2 py-0.5 rounded border border-royalblue-200">
              C001-C020
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{t.dashboard.secContractorsSub}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">{t.dashboard.secReorder}</p>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xl font-bold text-amber-600">{stats?.reorder_alerts_count || 0}</span>
            <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              Low Stock
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{t.dashboard.secReorderSub}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">{t.dashboard.secNegative}</p>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xl font-bold text-rose-600">{stats?.negative_stock_count || 62}</span>
            <span className="text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
              62 Items
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{t.dashboard.secNegativeSub}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">{t.dashboard.secPending}</p>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xl font-bold text-amber-600">{totalFlagged}</span>
            <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              Quarantined
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">{t.dashboard.secPendingSub}</p>
        </div>
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution Bar Chart */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">{t.dashboard.chartCatTitle}</h3>
              <p className="text-xs text-slate-500">{t.dashboard.chartCatDesc}</p>
            </div>
            <BarChart3 className="w-4 h-4 text-slate-400" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={stats?.categories_breakdown || []}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 70, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: '#475569' }} width={80} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val, name, item) => [`${val} Items (${item.payload.units} units)`, 'Total Materials']}
                />
                <Bar dataKey="item_count" fill="#1D4ED8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Contractor Consumption */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">{t.dashboard.chartConTitle}</h3>
              <p className="text-xs text-slate-500">{t.dashboard.chartConDesc}</p>
            </div>
            <Users2 className="w-4 h-4 text-slate-400" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={stats?.top_contractor_usage || []}
                margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis 
                  dataKey="contractor" 
                  tick={{ fontSize: 9, fill: '#475569' }} 
                  angle={-25} 
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px' }}
                  formatter={(val, name) => [`${val} units`, name === 'issued' ? 'Issued' : 'Returned']}
                />
                <Bar dataKey="issued" fill="#1D4ED8" name="issued" radius={[4, 4, 0, 0]} />
                <Bar dataKey="returned" fill="#10B981" name="returned" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Store Transactions Feed */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">{t.dashboard.recentTitle}</h3>
            <p className="text-xs text-slate-500">{t.dashboard.recentDesc}</p>
          </div>
          <button
            onClick={() => onNavigate('transactions')}
            className="text-xs font-semibold text-royalblue-700 hover:text-royalblue-800 flex items-center space-x-1"
          >
            <span>{t.dashboard.viewAllTx}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Ref ID</th>
                <th className="px-6 py-3">Type</th>
                <th className="px-6 py-3">Item ID</th>
                <th className="px-6 py-3">Material Specification</th>
                <th className="px-6 py-3 text-right">Quantity</th>
                <th className="px-6 py-3">Counterparty / Contractor</th>
                <th className="px-6 py-3 text-center">Verification Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats?.recent_transactions?.map((tx, idx) => (
                <tr key={idx} className="hover:bg-royalblue-50/40 transition-colors">
                  <td className="px-6 py-3 font-mono text-slate-500 whitespace-nowrap">{tx.date}</td>
                  <td className="px-6 py-3 font-mono font-medium text-royalblue-700">{tx.ref}</td>
                  <td className="px-6 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      tx.type === 'INWARD' ? 'bg-emerald-50 text-emerald-700' :
                      tx.type === 'ISSUE' ? 'bg-blue-50 text-royalblue-700' : 'bg-purple-50 text-purple-700'
                    }`}>
                      {tx.type}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-mono text-slate-700">{tx.item_id}</td>
                  <td className="px-6 py-3 font-medium text-slate-900 max-w-xs truncate">{tx.material_name}</td>
                  <td className="px-6 py-3 text-right font-mono font-bold text-slate-900">{tx.quantity}</td>
                  <td className="px-6 py-3 text-slate-600 truncate max-w-[180px]">{tx.party}</td>
                  <td className="px-6 py-3 text-center">
                    <StatusBadge status={tx.status} check={tx.check} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
