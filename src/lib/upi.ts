export function buildUpiLink(
  vpa: string,
  name: string,
  amount: number,
  note: string
): string {
  const pa = encodeURIComponent(vpa);
  const pn = encodeURIComponent(name);
  const am = encodeURIComponent(amount.toFixed(2));
  const tn = encodeURIComponent(note);
  return `upi://pay?pa=${pa}&pn=${pn}&am=${am}&cu=INR&tn=${tn}`;
}