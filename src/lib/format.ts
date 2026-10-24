export function formatInr(value: number, showSign = false): string {
  const sign = value < 0 ? "−" : showSign ? "+" : "";
  const absValue = Math.abs(value);
  const rupees = Math.floor(absValue);
  const paise = Math.round((absValue - rupees) * 100);
  const rupeesStr = rupees.toLocaleString("en-IN");
  if (paise > 0) {
    return `${sign}₹${rupeesStr}.${paise.toString().padStart(2, "0")}`;
  }
  return `${sign}₹${rupeesStr}`;
}