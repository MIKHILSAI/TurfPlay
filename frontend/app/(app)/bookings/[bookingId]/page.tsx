"use client"

import { use, useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import {
  ArrowLeftIcon,
  CalendarIcon,
  ClockIcon,
  MapPinIcon,
  UsersIcon,
  XCircleIcon,
  RefreshCwIcon,
  CheckCircle2Icon,
} from "lucide-react"
import { PageHeader, ErrorState, CardSkeletonList } from "@/components/state-views"
import { PriceBreakdownView } from "@/components/price-breakdown"
import { BookingStatusBadge, PaymentStatusBadge } from "@/components/status-badges"
import { CancelDialog } from "@/components/cancel-dialog"
import { RescheduleDialog } from "@/components/reschedule-dialog"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { formatDate, formatTimeRange, facilityLabel } from "@/lib/format"
import type { Booking } from "@/lib/types"

export default function BookingDetailsPage({ params }: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = use(params)
  const searchParams = useSearchParams()
  const justConfirmed = searchParams.get("confirmed") === "1"

  const { data, error, loading, reload } = useAsync(() => api.getBooking(bookingId), [bookingId])
  const [booking, setBooking] = useState<Booking | null>(null)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)

  useEffect(() => {
    if (data) setBooking(data)
  }, [data])

  const current = booking ?? data

  if (loading && !current) {
    return (
      <div className="flex flex-col gap-6">
        <BackLink />
        <CardSkeletonList count={2} />
      </div>
    )
  }

  if (error || !current) {
    return (
      <div className="flex flex-col gap-6">
        <BackLink />
        <ErrorState message={error ?? "Booking not found."} onRetry={reload} />
      </div>
    )
  }

  const resource = current.resource
  const isActive = current.status === "confirmed" || current.status === "rescheduled" || current.status === "pending"

  return (
    <div className="flex flex-col gap-6">
      <BackLink />

      {justConfirmed ? (
        <Alert>
          <CheckCircle2Icon />
          <AlertTitle>Booking confirmed</AlertTitle>
          <AlertDescription>Your reservation is set. A confirmation has been saved to your account.</AlertDescription>
        </Alert>
      ) : null}

      <PageHeader
        title={resource?.name ?? "Booking"}
        description={resource ? facilityLabel(resource.type) : undefined}
        action={
          <div className="flex items-center gap-2">
            <BookingStatusBadge status={current.status} />
            <PaymentStatusBadge status={current.payment_status} />
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Reservation details</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <Detail icon={CalendarIcon} label="Date" value={formatDate(current.booking_date)} />
              <Detail
                icon={ClockIcon}
                label="Time"
                value={`${formatTimeRange(current.start_time, current.end_time)} (${current.duration_mins} min)`}
              />
              {resource ? <Detail icon={MapPinIcon} label="Facility" value={resource.name} /> : null}
              {resource ? (
                <Detail icon={UsersIcon} label="Capacity" value={`Up to ${resource.capacity}`} />
              ) : null}
              {current.equipment && current.equipment.length > 0 ? (
                <>
                  <Separator />
                  <div className="flex flex-col gap-2 text-sm">
                    <span className="font-medium">Equipment</span>
                    {current.equipment.map((item, index) => (
                      <div key={`${String(item._id ?? item.equipment_id)}-${index}`} className="flex items-center justify-between gap-3 text-muted-foreground">
                        <span>{String(item.equipment_name ?? item.equipment_id ?? "Equipment")}</span>
                        <span>×{String(item.quantity ?? 0)}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}
              <Separator />
              <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                <span>Reschedules used: {current.reschedule_count}</span>
              </div>
            </CardContent>
          </Card>

          {isActive ? (
            <Card>
              <CardHeader>
                <CardTitle>Manage booking</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button variant="outline" onClick={() => setRescheduleOpen(true)}>
                  <RefreshCwIcon data-icon="inline-start" />
                  Reschedule
                </Button>
                <Button variant="destructive" onClick={() => setCancelOpen(true)}>
                  <XCircleIcon data-icon="inline-start" />
                  Cancel booking
                </Button>
              </CardContent>
            </Card>
          ) : null}
        </div>

        <div className="flex flex-col gap-4 lg:sticky lg:top-20 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle>Price breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {current.price_breakdown ? (
                <PriceBreakdownView breakdown={current.price_breakdown} />
              ) : (
                <p className="text-sm text-muted-foreground">No pricing details available.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <CancelDialog
        booking={current}
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        onCancelled={(updated) => setBooking(updated)}
      />
      <RescheduleDialog
        booking={current}
        open={rescheduleOpen}
        onOpenChange={setRescheduleOpen}
        onRescheduled={(updated) => setBooking(updated)}
      />
    </div>
  )
}

function Detail({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
        <Icon className="size-4" />
      </span>
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-sm font-medium">{value}</span>
      </div>
    </div>
  )
}

function BackLink() {
  return (
    <Button asChild variant="ghost" size="sm" className="w-fit -ml-2">
      <Link href="/bookings">
        <ArrowLeftIcon data-icon="inline-start" />
        My bookings
      </Link>
    </Button>
  )
}
