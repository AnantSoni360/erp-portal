import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { 
  LayoutDashboard, 
  Package, 
  ArrowDownLeft, 
  ArrowUpRight, 
  Users2, 
  CheckCheck, 
  FileSpreadsheet, 
  Download, 
  History,
  ShieldCheck,
  Building2,
  Box
} from 'lucide-react';

export const Sidebar = ({ activeTab, onSelectTab, pendingCount = 0 }) => {
  const { t } = useLanguage();

  const menuItems = [
    { id: 'dashboard', label: t.nav.dashboard, icon: LayoutDashboard },
    { id: 'materials', label: t.nav.materials, icon: Package, badge: '849 SKUs' },
    { id: 'inward', label: t.nav.inward, icon: ArrowDownLeft },
    { id: 'transactions', label: t.nav.transactions, icon: ArrowUpRight },
    { id: 'contractors', label: t.nav.contractors, icon: Users2, badge: '19 Accounts' },
    { id: 'verification', label: t.nav.verification, icon: CheckCheck, alertCount: pendingCount },
    { id: 'reconciliation', label: t.nav.reconciliation, icon: FileSpreadsheet },
    { id: 'reports', label: t.nav.reports, icon: Download },
    { id: 'audit', label: t.nav.audit, icon: History },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-200 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-royalblue-700 via-royalblue-600 to-royalblue-800 text-white flex items-center justify-center shadow-md shadow-royalblue-500/20">
          <Box className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight flex items-center space-x-1">
            <span>MMTPL</span>
            <span className="text-royalblue-600 text-xs px-1.5 py-0.2 rounded font-semibold bg-royalblue-50 border border-royalblue-200">
              ERP
            </span>
          </h1>
          <p className="text-[11px] text-slate-500 font-medium">Store & Inventory Portal</p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 p-3.5 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 pt-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {t.nav.operations}
        </div>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                isActive
                  ? 'bg-royalblue-700 text-white shadow-sm shadow-royalblue-700/30'
                  : 'text-slate-600 hover:text-royalblue-700 hover:bg-royalblue-50/70'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon
                  className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-white' : 'text-slate-400 group-hover:text-royalblue-600'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </div>

              {item.alertCount > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  isActive ? 'bg-white text-royalblue-700' : 'bg-amber-500 text-white shadow-xs'
                }`}>
                  {item.alertCount}
                </span>
              )}

              {item.badge && !item.alertCount && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                  isActive ? 'bg-royalblue-800 text-royalblue-100' : 'bg-slate-100 text-slate-500'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="bg-white rounded-xl p-3 border border-slate-200 text-xs space-y-1 shadow-2xs">
          <div className="flex items-center justify-between text-slate-700 font-medium">
            <span className="flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>{t.nav.parityStatus}</span>
            </span>
            <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
              {t.nav.parityCertified}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            {t.nav.parityFormula}
          </p>
        </div>
      </div>
    </aside>
  );
};
