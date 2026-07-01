interface BadgeProps {
  variant?: "success" | "warning" | "danger" | "info" | "neutral" | "purple";
  size?: "sm" | "md";
  showDot?: boolean;
  children: React.ReactNode;
}

const styles: Record<string, string> = {
  success: "bg-green-100 text-green-800 border border-green-200",
  warning: "bg-amber-100 text-amber-800 border border-amber-200",
  danger: "bg-red-100 text-red-800 border border-red-200",
  info: "bg-blue-100 text-blue-800 border border-blue-200",
  neutral: "bg-slate-100 text-slate-700 border border-slate-200",
  purple: "bg-purple-100 text-purple-800 border border-purple-200",
};

const dotColors: Record<string, string> = {
  success: "bg-green-500",
  warning: "bg-amber-500",
  danger: "bg-red-500",
  info: "bg-blue-500",
  neutral: "bg-slate-500",
  purple: "bg-purple-500",
};

const sizes: Record<string, string> = {
  sm: "px-2 py-0.5 text-[11px]",
  md: "px-2.5 py-1 text-[12px]",
};

export default function Badge({ variant = "neutral", size = "sm", showDot = false, children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium capitalize ${styles[variant]} ${sizes[size]}`}>
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`}></span>
      )}
      {children}
    </span>
  );
}
