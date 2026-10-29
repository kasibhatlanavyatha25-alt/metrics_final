import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    positive: boolean;
  };
  glowColor?: 'danger' | 'warning' | 'success' | 'primary';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  glowColor = 'primary',
}) => {
  const getGlowClass = () => {
    switch (glowColor) {
      case 'danger': return 'glow-danger border-rose-500/30';
      case 'warning': return 'glow-warning border-amber-500/30';
      case 'success': return 'glow-success border-emerald-500/30';
      default: return 'border-slate-800';
    }
  };

  return (
    <div className={`glass-card glass-card-hover rounded-xl p-4 flex flex-col justify-between border ${getGlowClass()}`}>
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">{title}</span>
          <div className="text-2xl font-black text-white mt-1 font-mono tracking-tight">{value}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700/60">
          {icon}
        </div>
      </div>
      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/60 pt-2">
          {subtitle && <span>{subtitle}</span>}
          {trend && (
            <span className={`font-semibold ${trend.positive ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
