// "oldbalanceOrg" -> "OldbalanceOrg", "is_fraud" -> "Is Fraud",
// "type = CASH_IN" -> "Type = CASH_IN" (category values are left as-is).
export function formatFeature(name) {
  if (!name) return "";
  const [column, ...value] = String(name).split(" = ");
  const pretty = column.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return value.length ? `${pretty} = ${value.join(" = ")}` : pretty;
}
