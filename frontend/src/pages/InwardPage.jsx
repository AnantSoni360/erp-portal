import React, { useState, useEffect } from 'react';
import { inwardApi, materialsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { ModalDialog } from '../components/ModalDialog';
import { 
  ArrowDownLeft, 
  Search, 
  Plus, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle2, 
  AlertTriangle,
  FileText,
  Calendar,
  Layers
} from 'lucide-react';

export const InwardPage = () => {
  const { t } = useLanguage();
  const [inwards, setInwards] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [checkFilter, setCheckFilter] = useState('All');
  const [loading, setLoading] = useState(false);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [selectedInward, setSelectedInward] = useState(null);
  const [materialsList, setMaterialsList] = useState([]);
  const [matSearch, setMatSearch] = useState('');

  // Form State
  const [inwardForm, setInwardForm] = useState({
    receipt_id: '',
    date: new Date().toISOString().split('T')[0],
    item_id: '',
    quantity: '',
    status: 'Book',
    ge_invoice_ref: '',
    notes: '',
    pdf_page: ''
  });
  const [selectedMatInfo, setSelectedMatInfo] = useState(null);
  const [formError, setFormError] = useState('');

  // Quick Verification Form
  const [verifyForm, setVerifyForm] = useState({
    target_status: 'Book',
    reason: 'Verified against supplier delivery invoice',
    corrected_quantity: ''
  });

  const fetchInwards = async () => {
    setLoading(true);
    try {
      const res = await inwardApi.list({
        search: search.trim() || undefined,
        status_filter: statusFilter !== 'All' ? statusFilter : undefined,
        check_filter: checkFilter !== 'All' ? checkFilter : undefined,
        page,
        limit
      });
      setInwards(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      console.error('Failed to load inwards', e);
    } finally {
      setLoading(false);
    }
  };

  const loadNextReceiptId = async () => {
    try {
      const res = await inwardApi.getNextId();
      setInwardForm((prev) => ({ ...prev, receipt_id: res.data.next_id }));
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

  useEffect(() => {
    fetchInwards();
  }, [page, statusFilter, checkFilter]);

  const handleOpenCreate = () => {
    loadNextReceiptId();
    setFormError('');
    setSelectedMatInfo(null);
    setInwardForm({
      receipt_id: '',
      date: new Date().toISOString().split('T')[0],
      item_id: '',
      quantity: '',
      status: 'Book',
      ge_invoice_ref: '',
      notes: '',
      pdf_page: ''
    });
    setShowCreateModal(true);
  };

  const handleSelectMaterial = (mat) => {
    setSelectedMatInfo(mat);
    setInwardForm({ ...inwardForm, item_id: mat.item_id });
    setMatSearch('');
    setMaterialsList([]);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    if (!inwardForm.item_id) {
      setFormError('Please select a valid material');
      return;
    }
    try {
      await inwardApi.create({
        receipt_id: inwardForm.receipt_id.trim(),
        date: inwardForm.date ? new Date(inwardForm.date).toISOString() : new Date().toISOString(),
        item_id: inwardForm.item_id.trim().toUpperCase(),
        quantity: parseFloat(inwardForm.quantity),
        status: inwardForm.status,
        ge_invoice_ref: inwardForm.ge_invoice_ref.trim() || null,
        notes: inwardForm.notes.trim() || null,
        pdf_page: inwardForm.pdf_page ? String(inwardForm.pdf_page) : null
      });
      setShowCreateModal(false);
      fetchInwards();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create inward receipt');
    }
  };

  const handleOpenVerify = (inw) => {
    setSelectedInward(inw);
    setVerifyForm({
      target_status: inw.status === 'Flagged' ? 'Book' : inw.status,
      reason: 'Verified against supplier delivery invoice',
      corrected_quantity: String(inw.quantity)
    });
    setShowVerifyModal(true);
  };

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    try {
      await inwardApi.verify(selectedInward.receipt_id, {
        target_status: verifyForm.target_status,
        reason: verifyForm.reason,
        corrected_quantity: verifyForm.corrected_quantity ? parseFloat(verifyForm.corrected_quantity) : undefined
      });
      setShowVerifyModal(false);
      fetchInwards();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to verify inward receipt');
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              {t.inward.tag}
            </span>
            <span className="text-xs text-slate-500">{t.inward.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.inward.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.inward.desc}
          </p>
        </div>

        <button
          onClick={handleOpenCreate}
          className="px-4 py-2.5 rounded-xl bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs shadow-royalblue-700/20 transition-colors flex items-center space-x-2 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>{t.inward.newConsignmentBtn}</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder={t.inward.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchInwards()}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500/30 focus:border-royalblue-600 bg-slate-50/50"
            />
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
              <option value="All">{t.inward.allBookingStatuses}</option>
              <option value="Book">{t.inward.statusBook}</option>
              <option value="Flagged">{t.inward.statusFlagged}</option>
              <option value="Excluded">{t.inward.statusExcluded}</option>
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
              <option value="All">{t.inward.allCheckFlags}</option>
              <option value="OK">Check = OK</option>
              <option value="Flagged">Check = Flagged</option>
              <option value="Excluded">Check = Excluded</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>
            {t.inward.found} <strong className="text-slate-900">{total}</strong> {t.inward.records}
          </span>
          <button
            onClick={() => {
              setSearch('');
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

      {/* Inward Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Receipt ID</th>
                <th className="px-5 py-3">Date</th>
                <th className="px-4 py-3">Item ID</th>
                <th className="px-5 py-3">Material Specification</th>
                <th className="px-3 py-3 text-center">Unit</th>
                <th className="px-4 py-3 text-right">Quantity</th>
                <th className="px-4 py-3">GE / Invoice Ref</th>
                <th className="px-4 py-3 text-center">Booking Status</th>
                <th className="px-4 py-3 text-center">Verification Check</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Loading inward consignments...</span>
                  </td>
                </tr>
              ) : inwards.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <ArrowDownLeft className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    <span>No inward records found.</span>
                  </td>
                </tr>
              ) : (
                inwards.map((inw) => (
                  <tr key={inw.receipt_id} className="hover:bg-royalblue-50/40 transition-colors">
                    <td className="px-5 py-3 font-mono font-semibold text-royalblue-700 whitespace-nowrap">
                      {inw.receipt_id}
                    </td>
                    <td className="px-5 py-3 text-slate-500 whitespace-nowrap">
                      {inw.date ? inw.date.split('T')[0] : '-'}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-700 whitespace-nowrap">
                      {inw.item_id}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-900 max-w-xs truncate">
                      {inw.material_name}
                      {inw.notes && (
                        <p className="text-[11px] text-slate-400 font-normal truncate mt-0.5">{inw.notes}</p>
                      )}
                    </td>
                    <td className="px-3 py-3 text-center font-mono font-semibold text-slate-500">
                      {inw.material_unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-900">
                      +{inw.quantity}
                    </td>
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      {inw.ge_invoice_ref || '-'}
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        inw.status === 'Book' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        inw.status === 'Flagged' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {inw.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <StatusBadge status={inw.check_status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleOpenVerify(inw)}
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold text-royalblue-700 bg-royalblue-50 hover:bg-royalblue-100 transition-colors"
                        title="Audit / Verify Receipt"
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

      {/* Modal 1: New Inward Consignment Entry */}
      <ModalDialog
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Record New Inward Consignment"
        subtitle="Log material received by store into central database"
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
              <label className="block text-xs font-semibold text-slate-700 mb-1">Receipt ID *</label>
              <input
                type="text"
                required
                value={inwardForm.receipt_id}
                onChange={(e) => setInwardForm({ ...inwardForm, receipt_id: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date of Receipt *</label>
              <input
                type="date"
                required
                value={inwardForm.date}
                onChange={(e) => setInwardForm({ ...inwardForm, date: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>
          </div>

          {/* Material Search and Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700">Search Material *</label>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Type material name or Item ID (e.g. MT0750)..."
                value={matSearch}
                onChange={(e) => {
                  setMatSearch(e.target.value);
                  searchMaterials(e.target.value);
                }}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>

            {/* Suggestions dropdown */}
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
                    <span className="text-slate-500 font-mono">{m.unit}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Selected Material Chip */}
            {selectedMatInfo && (
              <div className="p-3 bg-royalblue-50 rounded-lg border border-royalblue-200 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-royalblue-900 font-mono mr-2">{selectedMatInfo.item_id}</span>
                  <span className="text-royalblue-800">{selectedMatInfo.name}</span>
                </div>
                <span className="font-mono font-semibold px-2 py-0.5 rounded bg-white text-royalblue-700 border border-royalblue-200">
                  Unit: {selectedMatInfo.unit}
                </span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity Received *</label>
              <input
                type="number"
                step="any"
                required
                placeholder="e.g. 50"
                value={inwardForm.quantity}
                onChange={(e) => setInwardForm({ ...inwardForm, quantity: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Booking Status *</label>
              <select
                value={inwardForm.status}
                onChange={(e) => setInwardForm({ ...inwardForm, status: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
              >
                <option value="Book">Book (Verified - Adds to Stock)</option>
                <option value="Flagged">Flagged (Unverified - Quarantine)</option>
                <option value="Excluded">Excluded (Reference Only)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">GE / Invoice Reference</label>
              <input
                type="text"
                placeholder="e.g. GE-2026-992 / Inv 4410"
                value={inwardForm.ge_invoice_ref}
                onChange={(e) => setInwardForm({ ...inwardForm, ge_invoice_ref: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">PDF / Register Page Ref</label>
              <input
                type="text"
                placeholder="e.g. 1"
                value={inwardForm.pdf_page}
                onChange={(e) => setInwardForm({ ...inwardForm, pdf_page: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Supporting Notes / Remarks</label>
            <textarea
              rows={2}
              placeholder="e.g. Material received in good condition, batch inspected"
              value={inwardForm.notes}
              onChange={(e) => setInwardForm({ ...inwardForm, notes: e.target.value })}
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
              Save Inward Entry
            </button>
          </div>
        </form>
      </ModalDialog>

      {/* Modal 2: Quick Verify Receipt */}
      <ModalDialog
        isOpen={showVerifyModal}
        onClose={() => setShowVerifyModal(false)}
        title={`Audit & Verify Inward Receipt: ${selectedInward?.receipt_id}`}
        subtitle={`Item: ${selectedInward?.item_id} - ${selectedInward?.material_name}`}
      >
        <form onSubmit={handleVerifySubmit} className="space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Current Status:</span>
              <StatusBadge status={selectedInward?.status} check={selectedInward?.check_status} />
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Original Notes:</span>
              <span className="text-slate-700">{selectedInward?.notes || 'None'}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Verification Status *</label>
            <select
              value={verifyForm.target_status}
              onChange={(e) => setVerifyForm({ ...verifyForm, target_status: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="Book">Book (Approve - Add to live book balance)</option>
              <option value="Flagged">Flagged (Keep in review queue)</option>
              <option value="Excluded">Excluded (Quarantine permanently)</option>
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
