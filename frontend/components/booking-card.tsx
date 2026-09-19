import Link from "next/link"
import { CalendarIcon, ClockIcon, MapPinIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { BookingStatusBadge, PaymentStatusBadge } from "@/components/status-badges"
import { formatCurrency, formatDate, formatTimeRange, facilityLabel } from "@/lib/format"
import type { Booking } from "@/lib/types"

export function BookingCard({ booking }: { booking: Booking }) {
  const resource = booking.resource
  return (
    <Link href={`/bookings/${booking._id}`} className="group block">
      <Card className="transition-colors group-hover:border-primary/50">
        <CardContent className="flex flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col gap-0.5">
              <span className="font-medium">{resource?.name ?? "Facility"}</span>
              {resource ? (
                <span className="text-xs text-muted-foreground">{facilityLabel(resource.type)}</span>
              ) : null}
            </div>
            <BookingStatusBadge status={booking.status} />
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <CalendarIcon className="size-4" />
              {formatDate(booking.booking_date)}
            </span>
            <span className="flex items-center gap-1.5">
              <ClockIcon className="size-4" />
              {formatTimeRange(booking.start_time, booking.end_time)}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-medium tabular-nums">
              {formatCurrency(booking.price_breakdown?.total_amount)}
            </span>
            <PaymentStatusBadge status={booking.payment_status} />
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
