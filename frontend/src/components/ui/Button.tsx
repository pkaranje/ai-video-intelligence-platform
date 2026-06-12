import type { ElementType, HTMLAttributes } from "react";

const variantClasses = {
  primary:
    "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200",
  secondary:
    "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700",
  ghost: "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800",
} as const;

const base =
  "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 disabled:pointer-events-none disabled:opacity-50";

interface ButtonProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType;
  variant?: keyof typeof variantClasses;
}

export function Button({
  as: Tag = "button",
  variant = "primary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <Tag
      className={[base, variantClasses[variant], className].join(" ")}
      {...rest}
    >
      {children}
    </Tag>
  );
}
