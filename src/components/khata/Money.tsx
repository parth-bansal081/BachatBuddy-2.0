import { formatInr } from "@/lib/format";

interface MoneyProps {
  value: number;
  sign?: boolean;
}

export function Money({ value, sign = false }: MoneyProps) {
  return <span className="font-num">{formatInr(value, sign)}</span>;
}