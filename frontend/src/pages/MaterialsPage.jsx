import React, { useState, useEffect } from 'react';
import { materialsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { ModalDialog } from '../components/ModalDialog';
import { 
  Package, 
  Search, 
  Filter, 
  Plus, 
  Edit3, 
  Eye, 
  RefreshCw, 
  Layers, 
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  FileSpreadsheet,
  CheckCircle2,
  Box
} from 'lucide-react';

export const MaterialsPage = () => {
  const { t } = useLanguage();
  const [materials, setMaterials] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [stockStatus, setStockStatus] = useState('All');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showLedgerModal, setShowLedgerModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [ledgerEntries, setLedgerEntries] = useState([]);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  // Form states
  const [newMatForm, setNewMatForm] = useState({
    item_id: '',
    name: '',
    category: 'Tools and general',
    unit: 'NOS',
    reorder_level: '',
    opening_stock: '0'
  });
  const [formError, setFormError] = useState('');
  const [editForm, setEditForm] = useState({
    name: '',
    category: '',
    unit: '',
    reorder_level: '',
    opening_stock: ''
  });

  const fetchCategories = async () => {
    try {
      const res = await materialsApi.getCategories();
      setCategories(res.data || []);
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  };

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const res = await materialsApi.list({
        search: search.trim() || undefined,
        category: category !== 'All' ? category : undefined,
        stock_status: stockStatus !== 'All' ? stockStatus : undefined,
        page,
        limit
      });
      setMaterials(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch materials', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchMaterials();
  }, [page, category, stockStatus]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchMaterials();
  };

  const handleOpenLedger = async (mat) => {
    setSelectedMaterial(mat);
    setShowLedgerModal(true);
    setLedgerLoading(true);
    try {
      const res = await materialsApi.getLedger(mat.item_id);
      setLedgerEntries(res.data || []);
    } catch (e) {
      console.error('Failed to load ledger', e);
    } finally {
      setLedgerLoading(false);
    }
  };

  const handleOpenEdit = (mat) => {
    setSelectedMaterial(mat);
    setEditForm({
      name: mat.name,
      category: mat.category,
      unit: mat.unit,
      reorder_level: mat.reorder_level !== null ? String(mat.reorder_level) : '',
      opening_stock: String(mat.opening_stock || 0)
    });
    setShowEditModal(true);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    try {
      await materialsApi.create({
        item_id: newMatForm.item_id.trim().toUpperCase(),
        name: newMatForm.name.trim(),
        category: newMatForm.category,
        unit: newMatForm.unit.trim().toUpperCase(),
        reorder_level: newMatForm.reorder_level ? parseFloat(newMatForm.reorder_level) : null,
        opening_stock: newMatForm.opening_stock ? parseFloat(newMatForm.opening_stock) : 0.0
      });
      setShowCreateModal(false);
      setNewMatForm({
        item_id: '',
        name: '',
        category: 'Tools and general',
        unit: 'NOS',
        reorder_level: '',
        opening_stock: '0'
      });
      fetchMaterials();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create material');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    try {
      await materialsApi.update(selectedMaterial.item_id, {
        name: editForm.name.trim(),
        category: editForm.category,
        unit: editForm.unit.trim().toUpperCase(),
        reorder_level: editForm.reorder_level ? parseFloat(editForm.reorder_level) : null,
        opening_stock: editForm.opening_stock ? parseFloat(editForm.opening_stock) : 0.0
      });
      setShowEditModal(false);
      fetchMaterials();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to update material');
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-royalblue-50 text-royalblue-700 border border-royalblue-200">
              {t.materials.tag}
            </span>
            <span className="text-xs text-slate-500">{t.materials.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.materials.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.materials.desc}
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 rounded-xl bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs shadow-royalblue-700/20 transition-colors flex items-center space-x-2 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>{t.materials.registerBtn}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search */}
          <form onSubmit={handleSearchSubmit} className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder={t.materials.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500/30 focus:border-royalblue-600 bg-slate-50/50"
            />
          </form>

          {/* Category Filter */}
          <div>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500/30 focus:border-royalblue-600 bg-white"
            >
              <option value="All">{t.materials.allCategories} ({categories.length})</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Stock Status Filter */}
          <div>
            <select
              value={stockStatus}
              onChange={(e) => {
                setStockStatus(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500/30 focus:border-royalblue-600 bg-white"
            >
              <option value="All">{t.materials.allStatuses}</option>
              <option value="OK">{t.materials.statusOk}</option>
              <option value="Reorder">{t.materials.statusReorder}</option>
              <option value="Negative">{t.materials.statusNegative}</option>
            </select>
          </div>
        </div>

        {/* Filter Badges Bar */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>
            {t.materials.showing} <strong className="text-slate-900">{materials.length}</strong> {t.materials.of} <strong className="text-slate-900">{total}</strong> {t.materials.materialsUnit}
          </span>
          <button
            onClick={() => {
              setSearch('');
              setCategory('All');
              setStockStatus('All');
              setPage(1);
            }}
            className="text-royalblue-700 hover:text-royalblue-800 font-semibold"
          >
            {t.materials.resetFilters}
          </button>
        </div>
      </div>

      {/* Materials Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t.materials.colItemId}</th>
                <th className="px-5 py-3">{t.materials.colSpec}</th>
                <th className="px-4 py-3">{t.materials.colCategory}</th>
                <th className="px-3 py-3 text-center">{t.materials.colUnit}</th>
                <th className="px-4 py-3 text-right">{t.materials.colInward}</th>
                <th className="px-4 py-3 text-right">{t.materials.colIssued}</th>
                <th className="px-4 py-3 text-right">{t.materials.colReturned}</th>
                <th className="px-4 py-3 text-right font-bold text-slate-900">{t.materials.colBalance}</th>
                <th className="px-4 py-3 text-center">{t.materials.colStatus}</th>
                <th className="px-4 py-3 text-center">{t.materials.colActions}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Loading materials catalog...</span>
                  </td>
                </tr>
              ) : materials.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <Package className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    <span>No materials matched your filter criteria.</span>
                  </td>
                </tr>
              ) : (
                materials.map((m) => (
                  <tr key={m.item_id} className="hover:bg-royalblue-50/40 transition-colors">
                    <td className="px-5 py-3 font-mono font-semibold text-royalblue-700 whitespace-nowrap">
                      {m.item_id}
                    </td>
                    <td className="px-5 py-3">
                      <div className="font-medium text-slate-900">{m.name}</div>
                      {/* Welding Rod Conversion Indicator if applicable */}
                      {m.is_welding_rod && m.welding_rod_cases !== null && (
                        <div className="text-[11px] text-royalblue-700 font-mono mt-0.5 flex items-center space-x-1">
                          <Box className="w-3 h-3 text-royalblue-600" />
                          <span>Equivalent: <strong>{m.welding_rod_cases} Cases</strong> (Packets conversion applied)</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {m.category}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-center font-mono font-semibold text-slate-500">
                      {m.unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-700">
                      {m.booked_inward}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-700">
                      {m.issued}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-700">
                      {m.returned}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono font-bold ${
                      m.book_balance < 0 ? 'text-rose-600 bg-rose-50/50' : 'text-slate-900'
                    }`}>
                      {m.book_balance}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={m.stock_status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <button
                          onClick={() => handleOpenLedger(m)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-royalblue-700 hover:bg-royalblue-50 transition-colors"
                          title="View Full Item Ledger History"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleOpenEdit(m)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-royalblue-700 hover:bg-royalblue-50 transition-colors"
                          title="Edit Details / Reorder Point"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </div>
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

      {/* Modal 1: Register New Material */}
      <ModalDialog
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Register New Material"
        subtitle="Add a new verified material item into the central MMTPL Material Master"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Item ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. MT1011"
                value={newMatForm.item_id}
                onChange={(e) => setNewMatForm({ ...newMatForm, item_id: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Unit of Measurement *</label>
              <input
                type="text"
                required
                placeholder="e.g. NOS, MTR, PAIR, SET"
                value={newMatForm.unit}
                onChange={(e) => setNewMatForm({ ...newMatForm, unit: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Material / Specification *</label>
            <input
              type="text"
              required
              placeholder="e.g. Grinding wheel 4 inch Norton"
              value={newMatForm.name}
              onChange={(e) => setNewMatForm({ ...newMatForm, name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Category *</label>
              <select
                value={newMatForm.category}
                onChange={(e) => setNewMatForm({ ...newMatForm, category: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Opening Stock (Units)</label>
              <input
                type="number"
                step="any"
                value={newMatForm.opening_stock}
                onChange={(e) => setNewMatForm({ ...newMatForm, opening_stock: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
              <span className="text-[10px] text-slate-400">Opening balance during onboarding</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Reorder Point Threshold (Optional)</label>
            <input
              type="number"
              step="any"
              placeholder="Alert threshold quantity"
              value={newMatForm.reorder_level}
              onChange={(e) => setNewMatForm({ ...newMatForm, reorder_level: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
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
              Save Material Record
            </button>
          </div>
        </form>
      </ModalDialog>

      {/* Modal 2: Material Details & Chronological Audit Ledger */}
      <ModalDialog
        isOpen={showLedgerModal}
        onClose={() => setShowLedgerModal(false)}
        title={`Stock Ledger History: ${selectedMaterial?.item_id}`}
        subtitle={selectedMaterial?.name}
        maxWidth="max-w-4xl"
      >
        <div className="space-y-4">
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-4 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500">Category:</span>
              <p className="font-semibold text-slate-900">{selectedMaterial?.category}</p>
            </div>
            <div>
              <span className="text-slate-500">Unit:</span>
              <p className="font-semibold text-slate-900">{selectedMaterial?.unit}</p>
            </div>
            <div>
              <span className="text-slate-500">Current Balance:</span>
              <p className="font-bold font-mono text-royalblue-700 text-sm">
                {selectedMaterial?.book_balance} {selectedMaterial?.unit}
              </p>
            </div>
            <div>
              <span className="text-slate-500">Status:</span>
              <div className="mt-0.5">
                <StatusBadge status={selectedMaterial?.stock_status} />
              </div>
            </div>
          </div>

          {/* Chronological Table */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100/70 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-2.5">Date</th>
                  <th className="px-4 py-2.5">Type</th>
                  <th className="px-4 py-2.5">Reference ID</th>
                  <th className="px-4 py-2.5">Party / Source</th>
                  <th className="px-3 py-2.5 text-right">In (+Qty)</th>
                  <th className="px-3 py-2.5 text-right">Out (-Qty)</th>
                  <th className="px-4 py-2.5 text-right font-bold text-slate-900">Running Balance</th>
                  <th className="px-3 py-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {ledgerLoading ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-slate-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto text-royalblue-600 mb-2" />
                      <span>Reconstructing complete stock timeline...</span>
                    </td>
                  </tr>
                ) : ledgerEntries.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-slate-400">
                      <span>No transactions logged for this item yet. Current balance is 0.</span>
                    </td>
                  </tr>
                ) : (
                  ledgerEntries.map((entry, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                        {entry.date ? entry.date.split('T')[0] : '-'}
                      </td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          entry.type === 'INWARD' ? 'bg-emerald-50 text-emerald-700' :
                          entry.type === 'ISSUE' ? 'bg-blue-50 text-royalblue-700' :
                          entry.type === 'RETURN' ? 'bg-purple-50 text-purple-700' : 'bg-slate-100 text-slate-700'
                        }`}>
                          {entry.type}
                        </span>
                      </td>
                      <td className="px-4 py-2 font-mono text-royalblue-700 font-medium">
                        {entry.reference_id}
                      </td>
                      <td className="px-4 py-2 text-slate-700 max-w-xs truncate">
                        {entry.contractor_or_vendor}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-emerald-600">
                        {entry.in_qty > 0 ? `+${entry.in_qty}` : '-'}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-rose-600">
                        {entry.out_qty > 0 ? `-${entry.out_qty}` : '-'}
                      </td>
                      <td className="px-4 py-2 text-right font-mono font-bold text-slate-900">
                        {entry.balance_after}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <StatusBadge status={entry.status} check={entry.check_status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </ModalDialog>

      {/* Modal 3: Edit Material */}
      <ModalDialog
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title={`Edit Material: ${selectedMaterial?.item_id}`}
        subtitle="Modify master details, unit, or reorder alert threshold"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Material Name / Specification *</label>
            <input
              type="text"
              required
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Category *</label>
              <select
                value={editForm.category}
                onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Unit *</label>
              <input
                type="text"
                required
                value={editForm.unit}
                onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Reorder Point Level</label>
              <input
                type="number"
                step="any"
                value={editForm.reorder_level}
                onChange={(e) => setEditForm({ ...editForm, reorder_level: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Opening Stock</label>
              <input
                type="number"
                step="any"
                value={editForm.opening_stock}
                onChange={(e) => setEditForm({ ...editForm, opening_stock: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowEditModal(false)}
              className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-lg bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs"
            >
              Update Record
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
};
