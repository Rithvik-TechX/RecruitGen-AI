import React from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  tone?: "primary" | "success" | "warning" | "danger" | "info";
  caption?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ReactNode;
}

const borderColors = {
  primary: "border-l-blue-500",
  success: "border-l-green-500",
  warning: "border-l-amber-500",
  danger: "border-l-red-500",
  info: "border-l-indigo-500",
};

const iconColors = {
  primary: "text-blue-600 bg-blue-50",
  success: "text-green-600 bg-green-50",
  warning: "text-amber-600 bg-amber-50",
  danger: "text-red-600 bg-red-50",
  info: "text-indigo-600 bg-indigo-50",
};

export default function StatCard({ 
  label, 
  value, 
  tone = "primary",
  caption,
  trend,
  trendValue,
  icon
}: StatCardProps) {
  return (
    <div className={`card-hover-lift relative overflow-hidden rounded-lg border border-l-4 border-slate-200/90 bg-white p-5 shadow-sm ${borderColors[tone]}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-semibold text-slate-500">{label}</p>
          <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className="text-[27px] font-semibold leading-none tracking-tight text-slate-950">{value}</p>
            {trend && trendValue && (
              <span className={`flex items-center text-[13px] font-medium ${
                trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-slate-500'
              }`}>
                {trend === 'up' && (
                  <svg className="w-3.5 h-3.5 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                  </svg>
                )}
                {trend === 'down' && (
                  <svg className="w-3.5 h-3.5 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
                  </svg>
                )}
                {trendValue}
              </span>
            )}
          </div>
          {caption && <p className="mt-2 text-[13px] text-slate-500">{caption}</p>}
        </div>
        {icon && (
          <div className={`flex-shrink-0 rounded-lg p-2.5 ${iconColors[tone]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
