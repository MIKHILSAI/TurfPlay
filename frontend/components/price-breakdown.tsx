import { Separator } from "@/components/ui/separator"
import { formatCurrency } from "@/lib/format"
import type { PriceBreakdown } from "@/lib/types"

function Row({ label, value, muted }: { label: string; value: number; muted?: boolean }) {
  if (!value) return null
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={muted ? "text-emerald-700 dark:text-emerald-400" : "tabular-nums"}>
        {muted ? "−" : ""}
        {formatCurrency(Math.abs(value))}
      </span>
    </div>
  )
}

// Renders values exactly as returned by the backend. Never recomputed here.
export function PriceBreakdownView({ breakdown }: { breakdown: PriceBreakdown }) {
  const discount = breakdown.membership_discount ?? breakdown.discount_amount ?? 0
  return (
    <div className="flex flex-col gap-2">
      <Row label="Base amount" value={breakdown.base_amount} />
      <Row label="Peak surcharge" value={breakdown.peak_surcharge ?? 0} />
      <Row label="Weekend surcharge" value={breakdown.weekend_surcharge ?? 0} />
      <Row label="Equipment" value={breakdown.equipment_amount} />
      <Row label="Membership discount" value={discount} muted />
      <Row label="Deposit" value={breakdown.deposit_amount} />
      <Separator className="my-1" />
      <div className="flex items-center justify-between text-base font-semibold">
        <span>Total</span>
        <span className="tabular-nums">{formatCurrency(breakdown.total_amount)}</span>
      </div>
    </div>
  )
}
