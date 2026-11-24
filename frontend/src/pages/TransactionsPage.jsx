import React, { useState, useEffect } from 'react';
import { transactionsApi, contractorsApi, materialsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { ModalDialog } from '../components/ModalDialog';
import { 
  ArrowUpRight, 
  RotateCcw, 
  Search, 
  Plus, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  FileCheck2,
  Calendar,
  Layers
} from 'lucide-react';

export const TransactionsPage = () => {
  const { t } = useLanguage();
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [search, setSearch] = useState('');
  const [contractorFilter, setContractorFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [checkFilter, setCheckFilter] = useState('All');
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);

  // Material selection & live balance
  const [materialsList, setMaterialsList] = useState([]);
  const [matSearch, setMatSearch] = useState('');
  const [selectedMatInfo, setSelectedMatInfo] = useState(null);
  const [liveBalance, setLiveBalance] = useState(null);

  // Form State
  const [movementType, setMovementType] = useState('ISSUE'); // 'ISSUE' or 'RETURN'
  const [txForm, setTxForm] = useState({
    transaction_id: '',
    date: new Date().toISOString().split('T')[0],
    contractor_code: '',
    item_id: '',
    quantity: '',
    status: 'Posted',
    slip_ref: '',
    notes: '',
    received_by: '',
    workfront: '',
    issue_basis: 'Consumable',
    authorized_override: false,
    override_reason: ''
  });
  const [formError, setFormError] = useState('');

  // Quick Verification Form
  const [verifyForm, setVerifyForm] = useState({
    target_status: 'Posted',
    reason: 'Verified against signed site material issue slip',
    corrected_quantity: ''
  });

  const fetchContractors = async () => {
    try {
      const res = await contractorsApi.list();
      setContractors(res.data || []);
    } catch (e) {
      console.error('Failed to load contractors', e);
    }
  };

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await transactionsApi.list({
        search: search.trim() || undefined,
        contractor_code: contractorFilter !== 'All' ? contractorFilter : undefined,
        status_filter: statusFilter !== 'All' ? statusFilter : undefined,
        check_filter: checkFilter !== 'All' ? checkFilter : undefined,
        page,
        limit
      });
      setTransactions(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      console.error('Failed to load transactions', e);
    } finally {
      setLoading(false);
    }
  };

  const loadNextTxId = async () => {
    try {
      const res = await transactionsApi.getNextId();
      setTxForm((prev) => ({ ...prev, transaction_id: res.data.next_id }));
    } catch (e) {
      console.error('Failed to get next ID', e);
    }
  };

  const searchMaterials = async (query) => {
    if (!query || query.length < 1) return;
    try {
      const res = await materialsApi.list({ search: query, limit: 10 });
      setMaterialsList(res.data.items || []);
    } catch (e) {
      console.error('Failed to search materials', e);
    }
  };

  const checkLiveBalance = async (itemId) => {
    try {
      const res = await materialsApi.get(itemId);
      setLiveBalance(res.data.book_balance);
    } catch (e) {
      console.error('Failed to get live balance', e);
      setLiveBalance(null);
    }
  };

  useEffect(() => {
    fetchContractors();
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [page, contractorFilter, statusFilter, checkFilter]);

  const handleOpenCreate = () => {
    loadNextTxId();
    setFormError('');
    setSelectedMatInfo(null);
    setLiveBalance(null);
    setTxForm({
      transaction_id: '',
      date: new Date().toISOString().split('T')[0],
      contractor_code: contractors[0]?.contractor_code || 'C001',
      item_id: '',
      quantity: '',
      status: 'Posted',
      slip_ref: '',
      notes: '',
      received_by: '',
      workfront: '',
      issue_basis: 'Consumable',
      authorized_override: false,
      override_reason: ''
    });
    setShowCreateModal(true);
  };

  const handleSelectMaterial = (mat) => {
    setSelectedMatInfo(mat);
    setTxForm({ ...txForm, item_id: mat.item_id });
    setMatSearch('');
    setMaterialsList([]);
    checkLiveBalance(mat.item_id);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!txForm.item_id) {
      setFormError('Please select a material');
      return;
    }

    const qty = parseFloat(txForm.quantity);
    if (!qty || qty <= 0) {
      setFormError('Quantity must be greater than zero');
      return;
    }

    // Stock check
    if (movementType === 'ISSUE' && txForm.status === 'Posted') {
      if (liveBalance !== null && qty > liveBalance) {
        if (!txForm.authorized_override || !txForm.override_reason.trim()) {
          setFormError(
            `Insufficient Stock! Available balance is ${liveBalance} ${selectedMatInfo?.unit || 'units'}. ` +
            `Issuing ${qty} units would make stock negative. Please enable Authorized Manager Override with a justification reason.`
          );
          return;
        }
      }
    }

    try {
      await transactionsApi.create({
        transaction_id: txForm.transaction_id.trim(),
        date: txForm.date ? new Date(txForm.date).toISOString() : new Date().toISOString(),
        contractor_code: txForm.contractor_code,
        item_id: txForm.item_id.trim().toUpperCase(),
        issued_qty: movementType === 'ISSUE' ? qty : 0.0,
        returned_qty: movementType === 'RETURN' ? qty : 0.0,
        status: txForm.status,
        slip_ref: txForm.slip_ref.trim() || null,
        notes: txForm.notes.trim() || null,
        received_by: txForm.received_by.trim() || null,
        workfront: txForm.workfront.trim() || null,
        issue_basis: txForm.issue_basis,
        authorized_override: txForm.authorized_override,
        override_reason: txForm.authorized_override ? txForm.override_reason.trim() : null
      });
      setShowCreateModal(false);
      fetchTransactions();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to record transaction');
    }
  };

  const handleOpenVerify = (tx) => {
    setSelectedTx(tx);
    const currQty = tx.issued_qty > 0 ? tx.issued_qty : tx.returned_qty;
    setVerifyForm({
      target_status: tx.status === 'Flagged' ? 'Posted' : tx.status,
      reason: 'Verified against signed site material issue slip',
      corrected_quantity: String(currQty)
    });
    setShowVerifyModal(true);
  };

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    try {
      await transactionsApi.verify(selectedTx.transaction_id, {
        target_status: verifyForm.target_status,
        reason: verifyForm.reason,
        corrected_quantity: verifyForm.corrected_quantity ? parseFloat(verifyForm.corrected_quantity) : undefined
      });
      setShowVerifyModal(false);
      fetchTransactions();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to verify transaction');
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-royalblue-700 border border-blue-200">
              {t.transactions.tag}
            </span>
            <span className="text-xs text-slate-500">{t.transactions.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.transactions.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.transactions.desc}
          </p>
        </div>

        <button
          onClick={handleOpenCreate}
          className="px-4 py-2.5 rounded-xl bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs shadow-royalblue-700/20 transition-colors flex items-center space-x-2 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>{t.transactions.recordBtn}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder={t.transactions.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchTransactions()}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-slate-50/50"
            />
          </div>

          <div>
            <select
              value={contractorFilter}
              onChange={(e) => {
                setContractorFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="All">{t.transactions.allContractors}</option>
              {contractors.map((c) => (
                <option key={c.contractor_code} value={c.contractor_code}>
                  {c.name} ({c.contractor_code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="All">All Statuses</option>
              <option value="Posted">Posted (Verified in Stock)</option>
              <option value="Flagged">Flagged (Quarantined)</option>
              <option value="Excluded">Excluded (Reference Only)</option>
            </select>
          </div>

          <div>
            <select
              value={checkFilter}
              onChange={(e) => {
                setCheckFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="All">All Validation Checks</option>
              <option value="OK">Check = OK</option>
              <option value="Flagged">Check = Flagged</option>
              <option value="Excluded">Check = Excluded</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>
            Found <strong className="text-slate-900">{total}</strong> contractor transactions
          </span>
          <button
            onClick={() => {
              setSearch('');
              setContractorFilter('All');
              setStatusFilter('All');
              setCheckFilter('All');
              setPage(1);
            }}
            className="text-royalblue-700 hover:text-royalblue-800 font-semibold"
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Tx ID</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Contractor</th>
                <th className="px-4 py-3">Item ID</th>
                <th className="px-5 py-3">Material Specification</th>
                <th className="px-3 py-3 text-center">Unit</th>
                <th className="px-3 py-3 text-right">Issued</th>
                <th className="px-3 py-3 text-right">Returned</th>
                <th className="px-3 py-3 text-center">Basis</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Check</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={12} className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Loading contractor transactions...</span>
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={12} className="px-6 py-12 text-center text-slate-400">
                    <ArrowUpRight className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    <span>No transactions found.</span>
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-royalblue-50/40 transition-colors">
                    <td className="px-5 py-3 font-mono font-semibold text-royalblue-700 whitespace-nowrap">
                      {tx.transaction_id}
                    </td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {tx.date ? tx.date.split('T')[0] : '-'}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap max-w-[150px] truncate" title={tx.contractor_name}>
                      {tx.contractor_name}
                      <span className="text-[10px] text-slate-400 block font-mono">({tx.contractor_code})</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-700 whitespace-nowrap">
                      {tx.item_id}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-900 max-w-xs truncate">
                      {tx.material_name}
                      {tx.slip_ref && (
                        <p className="text-[10px] text-slate-400 truncate mt-0.5">Slip: {tx.slip_ref}</p>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-mono font-semibold text-slate-500">
                      {tx.material_unit}
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-rose-600">
                      {tx.issued_qty > 0 ? `-${tx.issued_qty}` : '-'}
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-emerald-600">
                      {tx.returned_qty > 0 ? `+${tx.returned_qty}` : '-'}
                    </td>
                    <td className="px-3 py-3 text-center whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                        tx.issue_basis === 'Returnable' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                        tx.issue_basis === 'Plant & Machinery' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {tx.issue_basis || 'Consumable'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        tx.status === 'Posted' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        tx.status === 'Flagged' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <StatusBadge status={tx.check_status} />
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <button
                        onClick={() => handleOpenVerify(tx)}
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold text-royalblue-700 bg-royalblue-50 hover:bg-royalblue-100 transition-colors"
                        title="Audit / Verify Transaction"
                      >
                        Verify
                      </button>
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

      {/* Modal 1: Record Issue or Return Movement */}
      <ModalDialog
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Record Contractor Material Movement"
        subtitle="Log material issued to contractor or returned back to store"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{formError}</span>
            </div>
          )}

          {/* Issue vs Return Toggle */}
          <div className="flex rounded-xl bg-slate-100 p-1 border border-slate-200">
            <button
              type="button"
              onClick={() => setMovementType('ISSUE')}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                movementType === 'ISSUE'
                  ? 'bg-royalblue-700 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Issue Material (Store Outward)
            </button>
            <button
              type="button"
              onClick={() => setMovementType('RETURN')}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                movementType === 'RETURN'
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Return Material (Store Inward from Contractor)
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Transaction ID *</label>
              <input
                type="text"
                required
                value={txForm.transaction_id}
                onChange={(e) => setTxForm({ ...txForm, transaction_id: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date *</label>
              <input
                type="date"
                required
                value={txForm.date}
                onChange={(e) => setTxForm({ ...txForm, date: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Contractor Account *</label>
            <select
              value={txForm.contractor_code}
              onChange={(e) => setTxForm({ ...txForm, contractor_code: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              {contractors.map((c) => (
                <option key={c.contractor_code} value={c.contractor_code}>
                  {c.name} ({c.contractor_code})
                </option>
              ))}
            </select>
          </div>

          {/* Material Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700">Select Material *</label>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search material by name or Item ID (e.g. MT0005)..."
                value={matSearch}
                onChange={(e) => {
                  setMatSearch(e.target.value);
                  searchMaterials(e.target.value);
                }}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>

            {materialsList.length > 0 && (
              <div className="max-h-40 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-white shadow-lg">
                {materialsList.map((m) => (
                  <div
                    key={m.item_id}
                    onClick={() => handleSelectMaterial(m)}
                    className="p-2 hover:bg-royalblue-50 cursor-pointer text-xs flex items-center justify-between"
                  >
                    <div>
                      <span className="font-mono font-bold text-royalblue-700 mr-2">{m.item_id}</span>
                      <span className="text-slate-800">{m.name}</span>
                    </div>
                    <span className="text-slate-500 font-mono">Bal: {m.book_balance} {m.unit}</span>
                  </div>
                ))}
              </div>
            )}

            {selectedMatInfo && (
              <div className="p-3 bg-royalblue-50 rounded-lg border border-royalblue-200 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-royalblue-900 font-mono mr-2">{selectedMatInfo.item_id}</span>
                  <span className="text-royalblue-800">{selectedMatInfo.name}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-slate-900 font-mono">
                    Available: {liveBalance !== null ? liveBalance : selectedMatInfo.book_balance} {selectedMatInfo.unit}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Quantity {movementType === 'ISSUE' ? 'to Issue' : 'Returned'} *
              </label>
              <input
                type="number"
                step="any"
                required
                placeholder="e.g. 10"
                value={txForm.quantity}
                onChange={(e) => setTxForm({ ...txForm, quantity: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Issue Basis / Classification</label>
              <select
                value={txForm.issue_basis}
                onChange={(e) => setTxForm({ ...txForm, issue_basis: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
              >
                <option value="Consumable">Consumable (Consumed on site)</option>
                <option value="Returnable">Returnable (Tracked for return)</option>
                <option value="Plant & Machinery">Plant & Machinery (Asset tool)</option>
              </select>
            </div>
          </div>

          {/* Stock Guard Override Section (shows if quantity > liveBalance) */}
          {movementType === 'ISSUE' && selectedMatInfo && parseFloat(txForm.quantity || 0) > (liveBalance || 0) && (
            <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-300 space-y-2">
              <div className="flex items-center space-x-2 text-amber-800 font-semibold text-xs">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                <span>Negative Stock Guard Alert</span>
              </div>
              <p className="text-[11px] text-amber-700">
                Requested issue quantity ({txForm.quantity}) exceeds currently available stock ({liveBalance} {selectedMatInfo.unit}).
                An authorized manager override with a recorded reason is required.
              </p>
              <label className="flex items-center space-x-2 text-xs font-semibold text-slate-800">
                <input
                  type="checkbox"
                  checked={txForm.authorized_override}
                  onChange={(e) => setTxForm({ ...txForm, authorized_override: e.target.checked })}
                  className="rounded text-royalblue-600 focus:ring-royalblue-500"
                />
                <span>Authorized Override Approved</span>
              </label>
              {txForm.authorized_override && (
                <input
                  type="text"
                  required
                  placeholder="Mandatory Override Justification Reason..."
                  value={txForm.override_reason}
                  onChange={(e) => setTxForm({ ...txForm, override_reason: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-amber-300 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Workfront / Location</label>
              <input
                type="text"
                placeholder="e.g. Boiler 2, Yard 4"
                value={txForm.workfront}
                onChange={(e) => setTxForm({ ...txForm, workfront: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Received By</label>
              <input
                type="text"
                placeholder="e.g. Foreman Ramesh"
                value={txForm.received_by}
                onChange={(e) => setTxForm({ ...txForm, received_by: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Slip / Source Reference</label>
              <input
                type="text"
                placeholder="e.g. Slip 1024 / Book 2"
                value={txForm.slip_ref}
                onChange={(e) => setTxForm({ ...txForm, slip_ref: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Transaction Status</label>
              <select
                value={txForm.status}
                onChange={(e) => setTxForm({ ...txForm, status: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
              >
                <option value="Posted">Posted (Verified - Affects Inventory)</option>
                <option value="Flagged">Flagged (Unverified - Quarantine)</option>
                <option value="Excluded">Excluded (Reference Only)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes / Remarks</label>
            <textarea
              rows={2}
              placeholder="e.g. Issued for turbine structural welding"
              value={txForm.notes}
              onChange={(e) => setTxForm({ ...txForm, notes: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-lg bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs"
            >
              Commit Movement
            </button>
          </div>
        </form>
      </ModalDialog>

      {/* Modal 2: Verify Contractor Transaction */}
      <ModalDialog
        isOpen={showVerifyModal}
        onClose={() => setShowVerifyModal(false)}
        title={`Audit & Verify Transaction: ${selectedTx?.transaction_id}`}
        subtitle={`Contractor: ${selectedTx?.contractor_name} | Material: ${selectedTx?.item_id}`}
      >
        <form onSubmit={handleVerifySubmit} className="space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Current Status:</span>
              <StatusBadge status={selectedTx?.status} check={selectedTx?.check_status} />
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Slip Ref:</span>
              <span className="text-slate-700 font-mono">{selectedTx?.slip_ref || 'None'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Original Notes / Reason:</span>
              <span className="text-slate-700">{selectedTx?.notes || 'None'}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Verification Status *</label>
            <select
              value={verifyForm.target_status}
              onChange={(e) => setVerifyForm({ ...verifyForm, target_status: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="Posted">Posted (Approve - Update Live Inventory)</option>
              <option value="Flagged">Flagged (Keep in Verification Queue)</option>
              <option value="Excluded">Excluded (Quarantine Permanently)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Corrected Quantity (Optional)</label>
            <input
              type="number"
              step="any"
              value={verifyForm.corrected_quantity}
              onChange={(e) => setVerifyForm({ ...verifyForm, corrected_quantity: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Auditor Verification Justification *</label>
            <textarea
              required
              rows={3}
              value={verifyForm.reason}
              onChange={(e) => setVerifyForm({ ...verifyForm, reason: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowVerifyModal(false)}
              className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-lg bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs"
            >
              Commit Verification Decision
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
};
