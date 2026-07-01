interface CardProps {
  className?: string;
  children: React.ReactNode;
  hoverEffect?: boolean;
  accentTop?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

export default function Card({ 
  className = "", 
  children, 
  hoverEffect = false,
  accentTop = false,
  padding = "md" 
}: CardProps) {
  const paddingMap = {
    none: "",
    sm: "p-4",
    md: "p-5 sm:p-6",
    lg: "p-6 sm:p-8"
  };

  return (
    <div className={`
      bg-white rounded-lg border border-slate-200/90 shadow-sm relative overflow-hidden
      ${hoverEffect ? 'card-hover-lift' : ''}
      ${className}
    `}>
      {accentTop && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-blue-600"></div>
      )}
      <div className={paddingMap[padding]}>
        {children}
      </div>
    </div>
  );
}
