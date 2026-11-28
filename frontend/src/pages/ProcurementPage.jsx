import React, { useState, useEffect } from 'react';
import { 
  FileText, Building2, Search, Filter, Printer, ExternalLink, 
  ChevronRight, CheckCircle2, Shield, AlertCircle, ArrowUpRight,
  PackageCheck, Truck, CreditCard, Banknote, MapPin, Phone, Mail, User, X
} from 'lucide-react';
import { procurementApi } from '../api';
import { useLanguage } from '../context/LanguageContext';

export const ProcurementPage = () => {
  const { t } = useLanguage();
  const [activeSubTab, setActiveSubTab] = useState('pos'); // 'pos' or 'vendors'
  const [stats, setStats] = useState(null);
  const [pos, setPos] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedVendorFilter, setSelectedVendorFilter] = useState('');
  const [selectedPo, setSelectedPo] = useState(null);
  const [loadingPoDetail, setLoadingPoDetail] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, posRes, vendorsRes] = await Promise.all([
        procurementApi.getStats(),
        procurementApi.listPOs({ search, vendor_code: selectedVendorFilter, limit: 100 }),
        procurementApi.listVendors()
      ]);
      setStats(statsRes.data);
      setPos(posRes.data);
      setVendors(vendorsRes.data);
    } catch (err) {
      console.error('Failed to load procurement data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, selectedVendorFilter]);

  const handleViewPo = async (poNo) => {
    try {
      setLoadingPoDetail(true);
      const res = await procurementApi.getPODetail(poNo);
      setSelectedPo(res.data);
    } catch (e) {
      console.error('Failed to load PO details:', e);
    } finally {
      setLoadingPoDetail(false);
    }
  };

  const formatInr = (val) => {
    if (!val && val !== 0) return '₹0.00';
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-royalblue-600 mb-1">
            <span className="px-2 py-0.5 bg-royalblue-50 rounded-full border border-royalblue-200">
              Procurement & Vendor Management
            </span>
            <span>•</span>
            <span className="text-slate-500">LMEL Ghugus Site</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Purchase Orders & Vendor Desk
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Centralized registry of 62 operational POs, 20 verified vendors, and real unit purchasing cost telemetry.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex bg-slate-100 p-1 rounded-xl self-start md:self-auto border border-slate-200">
          <button
            onClick={() => setActiveSubTab('pos')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center space-x-2 ${
              activeSubTab === 'pos'
                ? 'bg-royalblue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Purchase Orders ({pos.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('vendors')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center space-x-2 ${
              activeSubTab === 'vendors'
                ? 'bg-royalblue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Vendors Directory ({vendors.length})</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total PO Spend</span>
              <span className="p-2 bg-royalblue-50 text-royalblue-600 rounded-xl">
                <Banknote className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {formatInr(stats.total_gross_value)}
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Taxable: {formatInr(stats.total_taxable_value)}</span>
              <span className="text-emerald-600 font-semibold">18% GST Tracked</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Purchase Orders</span>
              <span className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
                <FileText className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {stats.total_pos} <span className="text-sm font-normal text-slate-500">Orders</span>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Across FY 25-26 & 26-27</span>
              <span className="text-royalblue-600 font-semibold">100% Digitized</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Capital Plant Assets</span>
              <span className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                <Truck className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {stats.asset_items_count} <span className="text-sm font-normal text-slate-500">Line Items</span>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>Value: {formatInr(stats.asset_taxable_value)}</span>
              <span className="text-purple-600 font-semibold">Cranes, W/M & Panels</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Verified Vendors</span>
              <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                <Building2 className="w-4 h-4" />
              </span>
            </div>
            <div className="text-2xl font-extrabold text-slate-900">
              {stats.total_vendors} <span className="text-sm font-normal text-slate-500">Registered</span>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
              <span>All with GSTIN & Bank A/C</span>
              <span className="text-emerald-600 font-semibold">100% Verified</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content View */}
      {activeSubTab === 'pos' ? (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Filters Bar */}
          <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search PO number, vendor, remarks..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-royalblue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <select
                value={selectedVendorFilter}
                onChange={(e) => setSelectedVendorFilter(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-royalblue-500"
              >
                <option value="">All Vendors ({vendors.length})</option>
                {vendors.map((v) => (
                  <option key={v.vendor_code} value={v.vendor_code}>
                    {v.name} ({v.po_count} POs)
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* PO Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">PO Number & Date</th>
                  <th className="py-3 px-4">Supplier / Vendor</th>
                  <th className="py-3 px-4">Site & Work Order</th>
                  <th className="py-3 px-4 text-center">Items</th>
                  <th className="py-3 px-4 text-right">Taxable (₹)</th>
                  <th className="py-3 px-4 text-right">Gross Total (₹)</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan="8" className="py-8 text-center text-slate-400 font-medium">
                      Loading purchase orders...
                    </td>
                  </tr>
                ) : pos.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="py-8 text-center text-slate-400 font-medium">
                      No purchase orders found matching criteria.
                    </td>
                  </tr>
                ) : (
                  pos.map((po) => (
                    <tr key={po.po_no} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-royalblue-700">{po.po_no}</div>
                        <div className="text-[11px] text-slate-400">
                          {po.po_date ? new Date(po.po_date).toLocaleDateString('en-GB') : '-'}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{po.vendor_name || po.vendor_code}</div>
                        <div className="text-[10px] text-slate-400">{po.vendor_code}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-700 font-medium truncate max-w-[200px]">{po.project_site}</div>
                        <div className="text-[10px] text-slate-400">{po.work_order_no || 'LMEL GHUGUS'}</div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-bold text-[11px]">
                          {po.items_count}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-slate-700">
                        {formatInr(po.total_taxable)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-900">
                        {formatInr(po.gross_amount)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {po.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleViewPo(po.po_no)}
                          className="px-2.5 py-1 rounded-lg bg-royalblue-50 hover:bg-royalblue-600 hover:text-white text-royalblue-600 font-bold text-[11px] border border-royalblue-200 transition-all flex items-center space-x-1 mx-auto"
                        >
                          <span>View PO</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Vendors Directory Tab */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendors.map((v) => (
            <div key={v.vendor_code} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <span className="px-2 py-0.5 rounded-md bg-royalblue-50 text-royalblue-700 font-mono font-bold text-[10px] border border-royalblue-200">
                    {v.vendor_code}
                  </span>
                  <h3 className="font-bold text-slate-900 text-sm mt-1">{v.name}</h3>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900">{v.po_count} POs</span>
                  <div className="text-[10px] text-slate-400">{formatInr(v.total_po_value)}</div>
                </div>
              </div>

              <div className="mt-3 space-y-1.5 text-[11px] text-slate-600">
                {v.contact_person && (
                  <div className="flex items-center space-x-2">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{v.contact_person}</span>
                  </div>
                )}
                {v.phone && (
                  <div className="flex items-center space-x-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{v.phone}</span>
                  </div>
                )}
                {v.address && (
                  <div className="flex items-start space-x-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                    <span className="line-clamp-2">{v.address}</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[10px]">
                <div className="font-mono text-slate-500 font-semibold">
                  GST: <span className="text-slate-800">{v.gstin || 'N/A'}</span>
                </div>
                <div className="text-slate-400 font-medium">
                  {v.bank_name ? `${v.bank_name}` : 'Bank on file'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PO Slip Detail Modal */}
      {selectedPo && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8 max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-4 bg-slate-900 text-white flex items-center justify-between print:hidden">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-royalblue-400" />
                <span className="font-bold text-sm">Purchase Order Slip: {selectedPo.po_no}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-lg bg-royalblue-600 hover:bg-royalblue-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow-sm transition-all"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Slip</span>
                </button>
                <button
                  onClick={() => setSelectedPo(null)}
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Printable Slip Content */}
            <div className="p-8 overflow-y-auto space-y-6 text-slate-800 text-xs">
              {/* Header Letterhead */}
              <div className="border-b-2 border-slate-800 pb-4 text-center">
                <h2 className="text-xl font-extrabold text-slate-900 uppercase tracking-wide">
                  MAN MACHINE TECHNOCRATS PRIVATE LIMITED
                </h2>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  6th Floor, A Wing, Akruti Trade Center, MIDC Marol, Andheri East, Mumbai, Maharashtra 400093
                </p>
                <p className="text-[10px] font-bold text-slate-700">
                  GSTIN: 27AAUCM3977B1Z0 | Email: planning.cell@mnm.ltd | Contact: +91 9008038052
                </p>
                <div className="mt-2 inline-block px-4 py-1 bg-slate-100 border border-slate-300 rounded font-bold uppercase tracking-wider text-xs">
                  PURCHASE ORDER
                </div>
              </div>

              {/* PO Info Grid */}
              <div className="grid grid-cols-2 gap-4 border border-slate-300 p-4 rounded-lg bg-slate-50/50">
                <div>
                  <div className="font-bold text-slate-900 text-sm">PO NO: {selectedPo.po_no}</div>
                  <div className="text-slate-600 mt-1">
                    <span className="font-semibold">PO Date:</span>{' '}
                    {selectedPo.po_date ? new Date(selectedPo.po_date).toLocaleDateString('en-GB') : '-'}
                  </div>
                  <div className="text-slate-600">
                    <span className="font-semibold">Work Order:</span> {selectedPo.work_order_no || '5500002378'}
                  </div>
                  <div className="text-slate-600">
                    <span className="font-semibold">Project Site:</span> {selectedPo.project_site}
                  </div>
                </div>

                <div className="border-l border-slate-200 pl-4">
                  <div className="font-bold text-slate-900 text-sm">SUPPLIER DETAILS:</div>
                  <div className="font-bold text-royalblue-700 mt-1">{selectedPo.vendor?.name}</div>
                  <div className="text-slate-600">{selectedPo.vendor?.address}</div>
                  <div className="text-slate-600">
                    <span className="font-semibold">GSTIN:</span> {selectedPo.vendor?.gstin || 'N/A'}
                  </div>
                  <div className="text-slate-600">
                    <span className="font-semibold">Contact:</span> {selectedPo.vendor?.contact_person} ({selectedPo.vendor?.phone})
                  </div>
                </div>
              </div>

              {/* Line Items Table */}
              <div>
                <table className="w-full border border-slate-300 text-left">
                  <thead className="bg-slate-100 border-b border-slate-300 font-bold uppercase text-[10px]">
                    <tr>
                      <th className="py-2 px-3 border-r border-slate-300 w-12 text-center">SL</th>
                      <th className="py-2 px-3 border-r border-slate-300">Description of Materials / T&P</th>
                      <th className="py-2 px-3 border-r border-slate-300 w-16 text-center">UOM</th>
                      <th className="py-2 px-3 border-r border-slate-300 w-20 text-right">Qty</th>
                      <th className="py-2 px-3 border-r border-slate-300 w-24 text-right">Rate (₹)</th>
                      <th className="py-2 px-3 text-right w-28">Amount (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {selectedPo.items?.map((it) => (
                      <tr key={it.id}>
                        <td className="py-2 px-3 border-r border-slate-200 text-center font-medium text-slate-500">
                          {it.sl_no}
                        </td>
                        <td className="py-2 px-3 border-r border-slate-200 font-medium">
                          {it.item_description}
                          {it.remarks && (
                            <span className="ml-2 text-[9px] px-1.5 py-0.2 bg-slate-100 rounded text-slate-500 font-bold uppercase">
                              {it.remarks}
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 border-r border-slate-200 text-center">{it.uom}</td>
                        <td className="py-2 px-3 border-r border-slate-200 text-right font-semibold">{it.qty}</td>
                        <td className="py-2 px-3 border-r border-slate-200 text-right">{formatInr(it.unit_price)}</td>
                        <td className="py-2 px-3 text-right font-bold">{formatInr(it.taxable_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="border-t-2 border-slate-800 bg-slate-50 font-bold">
                    <tr>
                      <td colSpan="5" className="py-2 px-3 text-right border-r border-slate-300">
                        Sub Total (Taxable Value):
                      </td>
                      <td className="py-2 px-3 text-right">{formatInr(selectedPo.total_taxable)}</td>
                    </tr>
                    {selectedPo.igst_amount > 0 ? (
                      <tr>
                        <td colSpan="5" className="py-2 px-3 text-right border-r border-slate-300">
                          IGST @18%:
                        </td>
                        <td className="py-2 px-3 text-right">{formatInr(selectedPo.igst_amount)}</td>
                      </tr>
                    ) : (
                      <>
                        <tr>
                          <td colSpan="5" className="py-2 px-3 text-right border-r border-slate-300">
                            CGST @9%:
                          </td>
                          <td className="py-2 px-3 text-right">{formatInr(selectedPo.cgst_amount)}</td>
                        </tr>
                        <tr>
                          <td colSpan="5" className="py-2 px-3 text-right border-r border-slate-300">
                            SGST @9%:
                          </td>
                          <td className="py-2 px-3 text-right">{formatInr(selectedPo.sgst_amount)}</td>
                        </tr>
                      </>
                    )}
                    <tr className="bg-slate-200 text-slate-900 text-sm">
                      <td colSpan="5" className="py-2.5 px-3 text-right border-r border-slate-300 font-extrabold">
                        Grand Total:
                      </td>
                      <td className="py-2.5 px-3 text-right font-extrabold text-royalblue-700">
                        {formatInr(selectedPo.gross_amount)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {/* Terms & Conditions */}
              <div className="border border-slate-300 p-4 rounded-lg bg-slate-50 text-[11px] space-y-1">
                <div className="font-bold text-slate-900">TERMS & CONDITIONS:</div>
                <div><span className="font-semibold">1) Payment Terms:</span> {selectedPo.payment_terms || 'As agreed'}</div>
                <div><span className="font-semibold">2) Delivery Terms:</span> {selectedPo.delivery_terms || 'Immediate'}</div>
                <div><span className="font-semibold">3) Delivery Location:</span> C/o Lloyds Metals & Energy Ltd, Ghugus, Chandrapur, MH 442505</div>
                <div><span className="font-semibold">4) Note:</span> Original GST Invoice & Acknowledged Delivery Challan must accompany dispatch.</div>
              </div>

              {/* Signatures */}
              <div className="pt-10 flex items-center justify-between text-xs text-slate-700">
                <div className="text-center">
                  <div className="w-40 border-b border-slate-400 mb-1"></div>
                  <div className="font-bold">Prepared By</div>
                  <div className="text-[10px] text-slate-500">{selectedPo.prepared_by}</div>
                </div>
                <div className="text-center">
                  <div className="w-40 border-b border-slate-400 mb-1"></div>
                  <div className="font-bold">Store & Project Manager</div>
                  <div className="text-[10px] text-slate-500">LMEL Ghugus Site</div>
                </div>
                <div className="text-center">
                  <div className="w-40 border-b border-slate-400 mb-1"></div>
                  <div className="font-bold">Authorized Signatory</div>
                  <div className="text-[10px] text-slate-500">MMTPL Head Office</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
