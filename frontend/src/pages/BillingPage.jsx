import React, { useState, useEffect } from 'react';
import { 
  Receipt, Building2, Search, Filter, Download, 
  ChevronRight, CheckCircle2, ShieldAlert, ArrowUpRight,
  BadgeDollarSign, Landmark, Calendar, Layers, FileCheck, Layers2
} from 'lucide-react';
import { billingApi } from '../api';
import { useLanguage } from '../context/LanguageContext';

export const BillingPage = () => {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedWo, setSelectedWo] = useState('');
  const [selectedDept, setSelectedDept] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, invRes, woRes, deptRes] = await Promise.all([
        billingApi.getStats(),
        billingApi.listInvoices({ search, work_order: selectedWo, department: selectedDept, limit: 100 }),
        billingApi.getByWorkOrder(),
        billingApi.getByDepartment()
      ]);
      setStats(statsRes.data);
      setInvoices(invRes.data);
      setWorkOrders(woRes.data);
      setDepartments(deptRes.data);
    } catch (err) {
      console.error('Failed to load billing abstract:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, selectedWo, selectedDept]);

  const formatInr = (val) => {
    if (!val && val !== 0) return '₹0.00';
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatCr = (val) => {
    if (!val) return '₹0.00 Cr';
    const cr = Number(val) / 10000000;
    return `₹${cr.toFixed(2)} Cr`;
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-royalblue-600 mb-1">
            <span className="px-2 py-0.5 bg-royalblue-50 rounded-full border border-royalblue-200">
              Client Project Billing
            </span>
            <span>•</span>
            <span className="text-slate-500">Lloyds Metals & Energy Ltd (LMEL) Ghugus</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Client Invoicing & Billing Abstract
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Official billing ledger across Coke Oven, Battery Refractory, CDQ Fabrication & Rolling Mill packages.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-royalblue-600" />
            <span>Client: LMEL Ghugus</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Gross Billed Value</span>
              <span className="p-2 bg-royalblue-50 text-royalblue-600 rounded-xl">
                <BadgeDollarSign className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {formatCr(stats.total_gross)}
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Exact: {formatInr(stats.total_gross)}</span>
              <span className="text-emerald-600 font-semibold">{stats.total_invoices} Invoices</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Taxable Work Value</span>
              <span className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
                <Receipt className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {formatCr(stats.total_bill_amount)}
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Exact: {formatInr(stats.total_bill_amount)}</span>
              <span className="text-indigo-600 font-semibold">Excl. GST</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total GST Billed</span>
              <span className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                <Landmark className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {formatCr(stats.total_sgst + stats.total_cgst)}
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>SGST: {formatCr(stats.total_sgst)}</span>
              <span className="text-purple-600 font-semibold">CGST: {formatCr(stats.total_cgst)}</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">TDS Deductions (IT)</span>
              <span className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                <FileCheck className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {formatInr(stats.total_tds)}
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Received: {formatCr(stats.total_received)}</span>
              <span className="text-amber-600 font-semibold">2% IT Deducted</span>
            </div>
          </div>
        </div>
      )}

      {/* Work Orders Summary Cards */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Work Orders Breakdown (LMEL Packages)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => setSelectedWo('')}
            className={`p-3.5 rounded-xl border text-left transition-all ${
              selectedWo === ''
                ? 'bg-royalblue-50 border-royalblue-300 ring-2 ring-royalblue-500/20'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <div className="text-[11px] font-bold text-slate-500">ALL PACKAGES</div>
            <div className="text-base font-bold text-slate-900 mt-1">{stats?.total_invoices || 48} Invoices</div>
            <div className="text-[11px] font-semibold text-royalblue-700 mt-0.5">{formatCr(stats?.total_gross)}</div>
          </button>

          {workOrders.map((wo) => (
            <button
              key={wo.work_order_no}
              onClick={() => setSelectedWo(wo.work_order_no)}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                selectedWo === wo.work_order_no
                  ? 'bg-royalblue-50 border-royalblue-300 ring-2 ring-royalblue-500/20'
                  : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 bg-white rounded border border-slate-200 text-slate-700">
                  WO #{wo.work_order_no}
                </span>
                <span className="text-[10px] text-slate-400 font-bold">{wo.invoice_count} bills</span>
              </div>
              <div className="text-base font-bold text-slate-900 mt-1.5">{formatCr(wo.gross_total)}</div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                Taxable: {formatCr(wo.taxable_amount)}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Invoices Table Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Filters Bar */}
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search invoice no, description, bill no..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-royalblue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            {/* Department Filter */}
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            >
              <option value="">All Departments ({departments.length})</option>
              {departments.map((d) => (
                <option key={d.department} value={d.department}>
                  {d.department} ({d.invoice_count} bills)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Invoices Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-3.5 w-12 text-center">SL</th>
                <th className="py-3 px-3.5">Invoice & Bill No</th>
                <th className="py-3 px-3.5">Date & Month</th>
                <th className="py-3 px-3.5">Package / WO</th>
                <th className="py-3 px-3.5">Department & Description</th>
                <th className="py-3 px-3.5 text-right">Taxable (₹)</th>
                <th className="py-3 px-3.5 text-right">GST (₹)</th>
                <th className="py-3 px-3.5 text-right">Gross Total (₹)</th>
                <th className="py-3 px-3.5 text-right">TDS (₹)</th>
                <th className="py-3 px-3.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="10" className="py-8 text-center text-slate-400 font-medium">
                    Loading client billing abstract...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan="10" className="py-8 text-center text-slate-400 font-medium">
                    No client invoices found.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-3.5 text-center font-mono text-slate-400 text-[11px]">
                      {inv.sl_no}
                    </td>
                    <td className="py-3 px-3.5">
                      <div className="font-bold text-royalblue-700">{inv.invoice_no}</div>
                      <div className="text-[10px] text-slate-400">{inv.bill_no || 'RAB / Profarma'}</div>
                    </td>
                    <td className="py-3 px-3.5">
                      <div className="font-semibold text-slate-800">
                        {inv.bill_date ? new Date(inv.bill_date).toLocaleDateString('en-GB') : '-'}
                      </div>
                      <div className="text-[10px] text-slate-400">{inv.bill_month}</div>
                    </td>
                    <td className="py-3 px-3.5">
                      <span className="font-mono font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded text-[10px]">
                        {inv.work_order_no}
                      </span>
                    </td>
                    <td className="py-3 px-3.5">
                      <div className="font-semibold text-slate-900">{inv.department || 'GENERAL'}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[240px]" title={inv.description}>
                        {inv.description}
                      </div>
                    </td>
                    <td className="py-3 px-3.5 text-right font-semibold text-slate-700">
                      {formatInr(inv.bill_amount)}
                    </td>
                    <td className="py-3 px-3.5 text-right text-slate-500">
                      {formatInr(inv.sgst_amount + inv.cgst_amount)}
                    </td>
                    <td className="py-3 px-3.5 text-right font-bold text-slate-900">
                      {formatInr(inv.gross_amount)}
                    </td>
                    <td className="py-3 px-3.5 text-right text-amber-700 font-medium">
                      {formatInr(inv.tds_amount)}
                    </td>
                    <td className="py-3 px-3.5 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        inv.status === 'Received'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-blue-50 text-royalblue-700 border-royalblue-200'
                      }`}>
                        {inv.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
