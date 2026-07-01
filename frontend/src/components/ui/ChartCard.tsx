interface ChartCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export default function ChartCard({ title, description, children, action }: ChartCardProps) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200/90 bg-white shadow-sm">
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
        <div>
          <h3 className="text-[15px] font-semibold text-slate-950">{title}</h3>
          {description && <p className="text-[13px] text-slate-500 mt-1">{description}</p>}
        </div>
        {action && (
          <div className="shrink-0">
            {action}
          </div>
        )}
      </div>
      <div className="relative min-h-[300px] flex-1 p-5 sm:p-6">
        <div className="chart-frame">
          {children}
        </div>
      </div>
    </div>
  );
}
