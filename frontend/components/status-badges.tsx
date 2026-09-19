import { CheckCircle2Icon, ClockIcon, XCircleIcon, InfoIcon, RefreshCwIcon } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { bookingStatusMeta, paymentStatusMeta } from "@/lib/format"
import type { BookingStatus, PaymentStatus } from "@/lib/types"

function iconFor(status: BookingStatus) {
  switch (status) {
    case "confirmed":
      return CheckCircle2Icon
    case "completed":
      return CheckCircle2Icon
    case "pending":
      return ClockIcon
    case "rescheduled":
      return RefreshCwIcon
    case "cancelled":
      return XCircleIcon
    default:
      return InfoIcon
  }
}

export function BookingStatusBadge({ status }: { status: BookingStatus }) {
  const meta = bookingStatusMeta(status)
  const Icon = iconFor(status)
  return (
    <Badge variant="secondary" className={cn("gap-1 border-transparent", meta.className)}>
      <Icon className="size-3.5" />
      {meta.label}
    </Badge>
  )
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const meta = paymentStatusMeta(status)
  return (
    <Badge variant="secondary" className={cn("border-transparent", meta.className)}>
      {meta.label}
    </Badge>
  )
}
