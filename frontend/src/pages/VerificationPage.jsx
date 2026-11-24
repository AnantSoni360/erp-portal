import React, { useState, useEffect } from 'react';
import { verificationApi, materialsApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { StatusBadge } from '../components/StatusBadge';
import { ModalDialog } from '../components/ModalDialog';
import { 
  CheckCheck, 
  Search, 
  Filter, 
  AlertTriangle, 
  ShieldCheck, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight, 
  RefreshCw, 
  Eye, 
  ArrowRight,
  FileCheck2,
  Clock,
  Layers
} from 'lucide-react';

export const VerificationPage = () => {
  const { t } = useLanguage();
  const [pendingItems, setPendingItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [entityType, setEntityType] = useState('all'); // 'all', 'inward', 'contractor'
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  // Review Modal State
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [reviewForm, setReviewForm] = useState({
    target_status: 'Book', // or 'Posted' or 'Excluded'
    reason: '',
    corrected_quantity: '',
    verification_notes: ''
  });
  const [reviewSuccess, setReviewSuccess] = useState('');
  const [reviewError, setReviewError] = useState('');

  const fetchPending = async () => {
    setLoading(true);
    try {
      const res = await verificationApi.getPending({
        entity_type: entityType,
        search: search.trim() || undefined,
        page,
        limit
      });
      setPendingItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      console.error('Failed to load pending verification items', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, [page, entityType]);

  const handleOpenReview = (item) => {
    setSelectedItem(item);
    setReviewSuccess('');
    setReviewError('');
    const defaultApprovedStatus = item.entity_type === 'inward' ? 'Book' : 'Posted';
    setReviewForm({
      target_status: defaultApprovedStatus,
      reason: `Verified and confirmed against source slip ${item.source_ref || item.reference}`,
      corrected_quantity: String(item.quantity || ''),
      verification_notes: ''
    });
    setShowReviewModal(true);
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setReviewError('');
    setReviewSuccess('');
    if (!reviewForm.reason.trim()) {
      setReviewError('Auditor justification reason is required');
      return;
    }

    try {
      const res = await verificationApi.review(selectedItem.entity_type, selectedItem.id, {
        target_status: reviewForm.target_status,
        reason: reviewForm.reason.trim(),
        corrected_quantity: reviewForm.corrected_quantity ? parseFloat(reviewForm.corrected_quantity) : undefined,
        verification_notes: reviewForm.verification_notes.trim() || undefined
      });
      setReviewSuccess(res.data.message);
      setTimeout(() => {
        setShowReviewModal(false);
        fetchPending();
      }, 1000);
    } catch (err) {
      setReviewError(err.response?.data?.detail || 'Failed to submit review');
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
              {t.verification.tag}
            </span>
            <span className="text-xs text-slate-500">{t.verification.subtag}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            {t.verification.title}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t.verification.desc}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="px-3.5 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span><strong>{total}</strong> {t.verification.pendingBadge}</span>
          </div>

          <button
            onClick={fetchPending}
            className="p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by Ref ID, Contractor, Notes, or Review Reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchPending()}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-slate-50/50"
            />
          </div>

          <div>
            <select
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              <option value="all">All Quarantined Operations (Inward + Contractor)</option>
              <option value="inward">Inward Receipts Only</option>
              <option value="contractor">Contractor Movements Only</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>
            Displaying <strong className="text-slate-900">{pendingItems.length}</strong> of <strong className="text-slate-900">{total}</strong> flagged transactions awaiting individual review
          </span>
          <button
            onClick={() => {
              setSearch('');
              setEntityType('all');
              setPage(1);
            }}
            className="text-royalblue-700 hover:text-royalblue-800 font-semibold"
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Queue Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Reference ID</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Party / Contractor</th>
                <th className="px-4 py-3">Item ID</th>
                <th className="px-5 py-3">Specification / Description</th>
                <th className="px-3 py-3 text-right">Quantity</th>
                <th className="px-5 py-3">Quarantine Review Reason (from Excel)</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-royalblue-600 mb-2" />
                    <span>Loading pending audit queue...</span>
                  </td>
                </tr>
              ) : pendingItems.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-6 py-12 text-center text-slate-400">
                    <CheckCheck className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
                    <span className="font-semibold text-slate-700 block">All Transactions Verified!</span>
                    <span className="text-xs">No pending flagged entries in this queue.</span>
                  </td>
                </tr>
              ) : (
                pendingItems.map((item) => (
                  <tr key={`${item.entity_type}-${item.id}`} className="hover:bg-amber-50/30 transition-colors">
                    <td className="px-5 py-3 font-mono font-semibold text-royalblue-700 whitespace-nowrap">
                      {item.reference}
                    </td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {item.date ? item.date.split('T')[0] : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.tx_type === 'INWARD' ? 'bg-emerald-50 text-emerald-700' :
                        item.tx_type === 'ISSUE' ? 'bg-blue-50 text-royalblue-700' : 'bg-purple-50 text-purple-700'
                      }`}>
                        {item.tx_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap max-w-[160px] truncate">
                      {item.party}
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-slate-700 whitespace-nowrap">
                      {item.item_id === 'MT0000' ? (
                        <span className="text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                          Unassigned
                        </span>
                      ) : (
                        item.item_id
                      )}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-900 max-w-xs truncate">
                      {item.material_name}
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-slate-900">
                      {item.quantity} {item.unit}
                    </td>
                    <td className="px-5 py-3 text-slate-600 max-w-xs truncate" title={item.review_reason}>
                      {item.review_reason || item.notes || 'Pending store review'}
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        {item.current_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap">
                      <button
                        onClick={() => handleOpenReview(item)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-royalblue-700 hover:bg-royalblue-800 shadow-2xs transition-colors flex items-center space-x-1 mx-auto"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Audit & Decide</span>
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

      {/* Modal: Individual Transaction Audit Decision */}
      <ModalDialog
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        title={`Audit Decision: ${selectedItem?.reference}`}
        subtitle={`Type: ${selectedItem?.tx_type} | Party: ${selectedItem?.party}`}
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleReviewSubmit} className="space-y-4">
          {reviewSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center space-x-2">
              <CheckCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{reviewSuccess}</span>
            </div>
          )}

          {reviewError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{reviewError}</span>
            </div>
          )}

          {/* Context Card */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Material / Specification:</span>
              <span className="font-bold text-slate-900">{selectedItem?.material_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Source Register / Slip Ref:</span>
              <span className="font-mono text-slate-700">{selectedItem?.source_ref || 'None'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Flag Reason in Excel:</span>
              <span className="text-amber-800 font-medium">{selectedItem?.review_reason || selectedItem?.notes || 'Pending'}</span>
            </div>
          </div>

          {/* Decision Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Auditor Verification Decision *</label>
            <select
              value={reviewForm.target_status}
              onChange={(e) => setReviewForm({ ...reviewForm, target_status: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 bg-white"
            >
              {selectedItem?.entity_type === 'inward' ? (
                <>
                  <option value="Book">Approve & Book (Commit to Live Stock Balance)</option>
                  <option value="Flagged">Keep Flagged (Request Further Verification)</option>
                  <option value="Excluded">Exclude (Permanent Reference - Zero Stock Effect)</option>
                </>
              ) : (
                <>
                  <option value="Posted">Approve & Post (Commit to Live Stock Balance)</option>
                  <option value="Flagged">Keep Flagged (Request Further Verification)</option>
                  <option value="Excluded">Exclude (Permanent Reference - Zero Stock Effect)</option>
                </>
              )}
            </select>
          </div>

          {/* Quantity adjustment if required */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Verified Quantity ({selectedItem?.unit})
            </label>
            <input
              type="number"
              step="any"
              value={reviewForm.corrected_quantity}
              onChange={(e) => setReviewForm({ ...reviewForm, corrected_quantity: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500 font-mono"
            />
            <span className="text-[10px] text-slate-400">
              Update if source slip quantity was unreadable or adjusted upon inspection
            </span>
          </div>

          {/* Justification */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Auditor Justification Reason *
            </label>
            <textarea
              required
              rows={3}
              placeholder="e.g. Physical delivery challan verified by Store Keeper Suresh and cross-checked with supervisor..."
              value={reviewForm.reason}
              onChange={(e) => setReviewForm({ ...reviewForm, reason: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowReviewModal(false)}
              className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-lg bg-royalblue-700 hover:bg-royalblue-800 text-white text-xs font-semibold shadow-xs"
            >
              Commit Audited Decision
            </button>
          </div>
        </form>
      </ModalDialog>
    </div>
  );
};
