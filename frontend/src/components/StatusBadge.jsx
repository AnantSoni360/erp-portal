import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock, ShieldAlert } from 'lucide-react';

export const StatusBadge = ({ status, check }) => {
  const s = String(status || '').trim();
  const c = String(check || '').trim();

  // Determine appearance
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  let icon = null;

  if (s === 'Book' || s === 'Posted' || s === 'OK' || c === 'OK') {
    bg = 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-1 ring-emerald-600/10';
    icon = <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />;
  } else if (s === 'Flagged' || c === 'Flagged' || s === 'Reorder') {
    bg = 'bg-amber-50 text-amber-700 border-amber-200 ring-1 ring-amber-600/10';
    icon = <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />;
  } else if (s === 'Excluded' || c === 'Excluded') {
    bg = 'bg-slate-100 text-slate-500 border-slate-200 line-through';
    icon = <XCircle className="w-3 h-3 mr-1 text-slate-400" />;
  } else if (s === 'Negative' || c === 'Check entry') {
    bg = 'bg-rose-50 text-rose-700 border-rose-200 ring-1 ring-rose-600/10';
    icon = <ShieldAlert className="w-3 h-3 mr-1 text-rose-600" />;
  } else if (s === 'Consumable') {
    bg = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (s === 'Returnable') {
    bg = 'bg-purple-50 text-purple-700 border-purple-200';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${bg}`}>
      {icon}
      <span>{s || c || 'Unknown'}</span>
    </span>
  );
};
