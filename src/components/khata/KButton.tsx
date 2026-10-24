type KButtonVariant = "primary" | "outline";

interface KButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: KButtonVariant;
}

export function KButton({
  variant = "primary",
  className = "",
  disabled,
  children,
  ...props
}: KButtonProps) {
  const base = "font-num text-sm px-4 min-h-[48px] rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-khata-vermilion";
  const variants = {
    primary: "bg-khata-ink text-khata-paper hover:bg-khata-ink/80 disabled:opacity-50 disabled:cursor-not-allowed",
    outline: "border-2 border-khata-ink text-khata-ink hover:bg-khata-ink/5 disabled:opacity-50 disabled:cursor-not-allowed",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}