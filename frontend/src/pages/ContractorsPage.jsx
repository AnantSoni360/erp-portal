import React, { useState, useEffect } from 'react';
import { contractorsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { ModalDialog } from '../components/ModalDialog';
import { 
  Users2, 
  Search, 
  ArrowUpRight, 
  RotateCcw, 
  Package, 
  RefreshCw, 
  Eye, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck,
  Building,
  FileSpreadsheet
} from 'lucide-react';

export const ContractorsPage = () => {
  const { t } = useLanguage();
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  // Contractor Profile Modal
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedContractor, setSelectedContractor] = useState(null);
  const [contractorData, setContractorData] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [txSearch, setTxSearch] = useState('');
  const [profilePage, setProfilePage] = useState(1);

  const fetchContractors = async () => {
    setLoading(true);
    try {
      const res = await contractorsApi.list();
      setContractors(res.data || []);
    } catch (e) {
      console.error('Failed to load contractors', e);
    } finally {
      setLoading(false);
    }
  };

  const loadContractorProfile = async (code, page = 1, searchQuery = '') => {
    setProfileLoading(true);
    try {
      const res = await contractorsApi.getProfile(code, {
        page,
        limit: 15,
        search: searchQuery.trim() || undefined
      });
      setContractorData(res.data);
    } catch (e) {
      console.error('Failed to load profile', e);
    } finally {
      setProfileLoading(false);
    }
  };

  useEffect(() => {
    fetchContractors();
  }, []);

  const handleOpenProfile = (c) => {
    setSelectedContractor(c);
    setTxSearch('');
    setProfilePage(1);
    setShowProfileModal(true);
    loadContractorProfile(c.contractor_code, 1, '');
  };

  const filteredContractors = contractors.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.contractor_code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-royalblue-50 text-royalblue-700 border border-royalblue-200">
              {t.contractors.tag}
            </span>
            <span className="text-xs text-slate-500">{t.contractors.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.contractors.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.contractors.desc}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={t.contractors.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-slate-50/50"
            />
          </div>

          <button
            onClick={fetchContractors}
            className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Grid of 19 Contractors */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
          <span>Loading contractor ledgers...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredContractors.map((c) => (
            <div
              key={c.contractor_code}
              className="bg-white rounded-2xl border border-slate-200/90 shadow-2xs hover:shadow-md transition-all p-5 flex flex-col justify-between group relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-royalblue-700 via-royalblue-500 to-royalblue-400"></div>

              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-royalblue-50 text-royalblue-700 border border-royalblue-200">
                      {c.contractor_code}
                    </span>
                    <h3 className="text-base font-bold text-slate-900 tracking-tight mt-2 group-hover:text-royalblue-700 transition-colors">
                      {c.name}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">Sheet: {c.sheet_name}</p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-50 text-royalblue-700 border border-slate-100">
                    <Building className="w-5 h-5" />
                  </div>
                </div>

                {/* Metrics Breakdown */}
                <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-center">
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Transactions</p>
                    <p className="text-sm font-bold text-slate-900 font-mono mt-0.5">{c.total_transactions}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Total Issued</p>
                    <p className="text-sm font-bold text-rose-600 font-mono mt-0.5">{c.total_issued}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Total Returned</p>
                    <p className="text-sm font-bold text-emerald-600 font-mono mt-0.5">{c.total_returned}</p>
                  </div>
                </div>

                {/* Returnable Material Liability Tag */}
                <div className="mt-3 p-2.5 rounded-xl bg-purple-50/70 border border-purple-200/80 flex items-center justify-between text-xs">
                  <span className="text-purple-800 font-medium">Outstanding Returnables:</span>
                  <span className="font-bold font-mono text-purple-900">
                    {c.outstanding_returnables} units
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end">
                <button
                  onClick={() => handleOpenProfile(c)}
                  className="px-3.5 py-1.5 rounded-lg bg-royalblue-50 hover:bg-royalblue-100 text-royalblue-700 text-xs font-semibold transition-colors flex items-center space-x-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Account Ledger</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Contractor Profile & Itemized Consumption */}
      <ModalDialog
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        title={`Contractor Account: ${selectedContractor?.name}`}
        subtitle={`Account Code: ${selectedContractor?.contractor_code} | Source Sheet: ${selectedContractor?.sheet_name}`}
        maxWidth="max-w-5xl"
      >
        <div className="space-y-5">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-medium">Total Transactions</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                {contractorData?.transactions?.total || 0}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-medium">Cumulative Issued</span>
              <p className="text-lg font-bold text-rose-600 font-mono mt-0.5">
                {selectedContractor?.total_issued}
              </p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-medium">Cumulative Returned</span>
              <p className="text-lg font-bold text-emerald-600 font-mono mt-0.5">
                {selectedContractor?.total_returned}
              </p>
            </div>
            <div className="bg-purple-50 p-3 rounded-xl border border-purple-200">
              <span className="text-[11px] text-purple-700 font-medium">Outstanding Returnables</span>
              <p className="text-lg font-bold text-purple-900 font-mono mt-0.5">
                {selectedContractor?.outstanding_returnables}
              </p>
            </div>
          </div>

          {/* Section 1: Material Consumption Summary Table */}
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
              Material-Wise Consumption Summary ({contractorData?.material_summary?.length || 0} Materials)
            </h4>
            <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th className="px-4 py-2">Item ID</th>
                    <th className="px-4 py-2">Material Specification</th>
                    <th className="px-3 py-2 text-center">Unit</th>
                    <th className="px-3 py-2 text-right">Total Issued</th>
                    <th className="px-3 py-2 text-right">Total Returned</th>
                    <th className="px-4 py-2 text-right font-bold text-slate-900">Net Retained</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {contractorData?.material_summary?.map((m) => (
                    <tr key={m.item_id} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-mono text-royalblue-700 font-semibold">{m.item_id}</td>
                      <td className="px-4 py-2 text-slate-900 font-medium">{m.material_name}</td>
                      <td className="px-3 py-2 text-center font-mono text-slate-500">{m.unit}</td>
                      <td className="px-3 py-2 text-right font-mono text-rose-600">{m.issued}</td>
                      <td className="px-3 py-2 text-right font-mono text-emerald-600">{m.returned}</td>
                      <td className="px-4 py-2 text-right font-mono font-bold text-slate-900">{m.net}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Full Individual Transaction Register */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Contractor Transaction Register
              </h4>
              <div className="w-64 relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
                <input
                  type="text"
                  placeholder="Filter slips or item IDs..."
                  value={txSearch}
                  onChange={(e) => {
                    setTxSearch(e.target.value);
                    loadContractorProfile(selectedContractor.contractor_code, 1, e.target.value);
                  }}
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-royalblue-500"
                />
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2">Tx ID</th>
                    <th className="px-4 py-2">Date</th>
                    <th className="px-3 py-2">Item ID</th>
                    <th className="px-4 py-2">Specification</th>
                    <th className="px-3 py-2 text-right">Issued</th>
                    <th className="px-3 py-2 text-right">Returned</th>
                    <th className="px-3 py-2">Slip Reference</th>
                    <th className="px-3 py-2 text-center">Status</th>
                    <th className="px-3 py-2 text-center">Check</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {profileLoading ? (
                    <tr>
                      <td colSpan={9} className="p-8 text-center text-slate-400">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-royalblue-600 mb-2" />
                        <span>Loading transactions...</span>
                      </td>
                    </tr>
                  ) : contractorData?.transactions?.items?.map((tx) => (
                    <tr key={tx.transaction_id} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-mono text-royalblue-700 font-medium">{tx.transaction_id}</td>
                      <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                        {tx.date ? tx.date.split('T')[0] : '-'}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-700">{tx.item_id}</td>
                      <td className="px-4 py-2 text-slate-900 font-medium truncate max-w-xs">{tx.material_name}</td>
                      <td className="px-3 py-2 text-right font-mono font-bold text-rose-600">
                        {tx.issued_qty > 0 ? `-${tx.issued_qty}` : '-'}
                      </td>
                      <td className="px-3 py-2 text-right font-mono font-bold text-emerald-600">
                        {tx.returned_qty > 0 ? `+${tx.returned_qty}` : '-'}
                      </td>
                      <td className="px-3 py-2 text-slate-600 truncate max-w-[120px]">{tx.slip_ref || '-'}</td>
                      <td className="px-3 py-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          tx.status === 'Posted' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {tx.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <StatusBadge status={tx.check_status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <span>Page {profilePage} of {contractorData?.transactions?.total_pages || 1}</span>
                <div className="flex space-x-1">
                  <button
                    disabled={profilePage <= 1}
                    onClick={() => {
                      const p = profilePage - 1;
                      setProfilePage(p);
                      loadContractorProfile(selectedContractor.contractor_code, p, txSearch);
                    }}
                    className="px-2 py-1 border rounded bg-white disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    disabled={profilePage >= (contractorData?.transactions?.total_pages || 1)}
                    onClick={() => {
                      const p = profilePage + 1;
                      setProfilePage(p);
                      loadContractorProfile(selectedContractor.contractor_code, p, txSearch);
                    }}
                    className="px-2 py-1 border rounded bg-white disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ModalDialog>
    </div>
  );
};
