import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { 
  Bell, 
  ChevronDown, 
  Shield, 
  CheckCircle2, 
  Globe,
  Languages
} from 'lucide-react';

export const Header = ({ onNavigate, pendingCount = 0 }) => {
  const { user, demoUsers, switchRole } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);

  const roleLabels = {
    admin: { label: 'Admin', color: 'bg-rose-50 text-rose-700 border-rose-200' },
    store_manager: { label: 'Store Manager', color: 'bg-royalblue-50 text-royalblue-700 border-royalblue-200' },
    store_employee: { label: 'Store Employee', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    management: { label: 'Management', color: 'bg-purple-50 text-purple-700 border-purple-200' }
  };

  const currentRoleInfo = roleLabels[user?.role] || roleLabels.admin;

  const languagesList = [
    { code: 'en', label: 'English', sub: 'Standard Corporate ERP', flag: '🇬🇧' },
    { code: 'hi', label: 'Hinglish', sub: 'हिंदी + English Store Format', flag: '🇮🇳' },
  ];

  const currentLang = languagesList.find(l => l.code === language) || languagesList[0];

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-xs px-6 py-3.5 flex items-center justify-between">
      {/* Left: Organization Context */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {t.header.storeSystem}
          </span>
        </div>
        <span className="text-slate-300">|</span>
        <span className="text-xs text-slate-500 hidden md:inline">
          {t.header.liveParity}
        </span>
      </div>

      {/* Right: Language Switcher, Notifications, Role Switcher */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Verification Queue Alert Notification */}
        <button
          onClick={() => onNavigate && onNavigate('verification')}
          className="relative p-2 rounded-lg text-slate-500 hover:text-royalblue-700 hover:bg-royalblue-50 transition-colors flex items-center space-x-1.5 text-xs font-medium"
          title="Review Pending Verification Items"
        >
          <Bell className="w-4 h-4 text-amber-500" />
          <span className="hidden sm:inline">{t.header.pendingReview}</span>
          {pendingCount > 0 && (
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-white">
              {pendingCount}
            </span>
          )}
        </button>

        {/* --- Language Switcher Dropdown --- */}
        <div className="relative">
          <button
            onClick={() => {
              setShowLangMenu(!showLangMenu);
              setShowRoleMenu(false);
            }}
            className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-royalblue-400 bg-slate-50 hover:bg-royalblue-50/50 transition-all text-xs font-semibold text-slate-700"
            title="Switch Language / भाषा बदलें"
          >
            <Globe className="w-3.5 h-3.5 text-royalblue-700" />
            <span className="hidden sm:inline text-slate-800 font-medium">
              {currentLang.flag} {currentLang.label}
            </span>
            <span className="sm:hidden font-mono text-slate-800 uppercase font-bold">
              {currentLang.code}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showLangMenu && (
            <div className="absolute right-0 mt-2 w-60 rounded-xl bg-white shadow-xl border border-slate-200 py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3 py-1.5 border-b border-slate-100 flex items-center space-x-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <Languages className="w-3.5 h-3.5 text-slate-500" />
                <span>Select Language / भाषा चुनें</span>
              </div>

              <div className="py-1">
                {languagesList.map((langItem) => {
                  const isSelected = language === langItem.code;
                  return (
                    <button
                      key={langItem.code}
                      onClick={() => {
                        setLanguage(langItem.code);
                        setShowLangMenu(false);
                      }}
                      className={`w-full px-3 py-2 text-left flex items-center justify-between hover:bg-royalblue-50/80 transition-colors ${
                        isSelected ? 'bg-royalblue-50 border-l-4 border-royalblue-700' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <span className="text-base">{langItem.flag}</span>
                        <div>
                          <p className="text-xs font-bold text-slate-900 leading-none">
                            {langItem.label}
                          </p>
                          <p className="text-[10px] text-slate-500 mt-0.5 leading-none">
                            {langItem.sub}
                          </p>
                        </div>
                      </div>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-royalblue-700 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* --- Role Switcher Pill & Dropdown --- */}
        <div className="relative">
          <button
            onClick={() => {
              setShowRoleMenu(!showRoleMenu);
              setShowLangMenu(false);
            }}
            className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-royalblue-300 bg-slate-50/70 hover:bg-royalblue-50/50 transition-all text-left"
          >
            <div className="w-7 h-7 rounded-full bg-royalblue-700 text-white flex items-center justify-center font-bold text-xs shadow-xs">
              {user?.full_name ? user.full_name[0] : 'U'}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-semibold text-slate-800 leading-none">{user?.full_name || 'Administrator'}</p>
              <div className="flex items-center space-x-1 mt-0.5">
                <span className={`text-[10px] px-1.5 py-0.2 font-medium rounded border ${currentRoleInfo.color}`}>
                  {currentRoleInfo.label}
                </span>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl bg-white shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{t.header.switchRole}</p>
                <p className="text-xs text-slate-600 mt-0.5">{t.header.testPermissions}</p>
              </div>

              <div className="py-1">
                {demoUsers.map((u) => {
                  const isCurrent = user?.username === u.username;
                  return (
                    <button
                      key={u.username}
                      onClick={() => {
                        switchRole(u.username);
                        setShowRoleMenu(false);
                      }}
                      className={`w-full px-4 py-2 text-left flex items-start space-x-3 hover:bg-royalblue-50/70 transition-colors ${
                        isCurrent ? 'bg-royalblue-50 border-l-4 border-royalblue-700' : ''
                      }`}
                    >
                      <Shield className={`w-4 h-4 mt-0.5 ${isCurrent ? 'text-royalblue-700' : 'text-slate-400'}`} />
                      <div>
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-semibold text-slate-900">{u.full_name}</span>
                          {isCurrent && <CheckCircle2 className="w-3.5 h-3.5 text-royalblue-700" />}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-tight">{u.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
