import type { BookingStatus, FacilityType, PaymentStatus } from "./types"

export function formatCurrency(amount: number | undefined | null): string {
  if (amount === undefined || amount === null) return "—"
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(iso: string | undefined): string {
  if (!iso) return "—"
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" })
}

export function formatDateTime(iso: string | undefined): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })
}

export function formatTimeRange(start: string, end: string): string {
  return `${start} – ${end}`
}

const FACILITY_LABELS: Record<FacilityType, string> = {
  badminton: "Badminton",
  football: "Football",
  tennis: "Tennis",
  multipurpose: "Multipurpose Room",
  "multipurpose room": "Multipurpose Room",
}

export function facilityLabel(type: FacilityType): string {
  return FACILITY_LABELS[type] ?? type
}

// Maps a status to a Badge variant + tone class. Color is always paired with text.
export function bookingStatusMeta(status: BookingStatus): { label: string; className: string } {
  switch (status) {
    case "confirmed":
      return { label: "Confirmed", className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" }
    case "completed":
      return { label: "Completed", className: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300" }
    case "pending":
      return { label: "Pending", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" }
    case "rescheduled":
      return { label: "Rescheduled", className: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300" }
    case "cancelled":
      return { label: "Cancelled", className: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" }
    default:
      return { label: status, className: "bg-muted text-muted-foreground" }
  }
}

export function paymentStatusMeta(status: PaymentStatus): { label: string; className: string } {
  switch (status) {
    case "paid":
      return { label: "Paid", className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" }
    case "refunded":
      return { label: "Refunded", className: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300" }
    case "pending":
      return { label: "Payment Pending", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" }
    case "unpaid":
      return { label: "Unpaid", className: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" }
    default:
      return { label: status, className: "bg-muted text-muted-foreground" }
  }
}
