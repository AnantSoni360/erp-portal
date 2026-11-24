import React from 'react';

export const StatCard = ({ title, value, subtitle, icon: Icon, badge, alert, trend }) => {
  return (
    <div className={`bg-white rounded-xl border ${alert ? 'border-amber-300 ring-2 ring-amber-500/20' : 'border-slate-200/80'} p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden`}>
      {/* Decorative Royal Blue subtle accent bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-royalblue-700 via-royalblue-500 to-royalblue-400"></div>
      
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold text-slate-500 tracking-wider uppercase">{title}</p>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-2xl font-bold text-slate-900 tracking-tight">{value}</h3>
            {badge && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-royalblue-50 text-royalblue-700 border border-royalblue-200">
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg ${alert ? 'bg-amber-50 text-amber-600' : 'bg-royalblue-50 text-royalblue-700'}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center text-xs text-slate-500">
          {trend}
        </div>
      )}
    </div>
  );
};
