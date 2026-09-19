"use client"

import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import { AlertCircleIcon, CheckCircle2Icon } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectGroup, SelectItem } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { useAsync } from "@/lib/use-async"
import { errorMessage, isApiError } from "@/lib/errors"
import { formatCurrency, facilityLabel } from "@/lib/format"
import { addDaysISO, startTimeOptions, addMinutes, formatClock, todayISO } from "@/lib/time"
import type { Booking, ReschedulePreview } from "@/lib/types"

export function RescheduleDialog({
  booking,
  open,
  onOpenChange,
  onRescheduled,
  initialDate,
  initialStartTime,
}: {
  booking: Booking
  open: boolean
  onOpenChange: (open: boolean) => void
  onRescheduled: (updated: Booking) => void
  initialDate?: string
  initialStartTime?: string
}) {
  const { customer, refresh: refreshCustomer } = useAuth()
  const facilities = useAsync(() => api.listResources(), [])

  const [resourceId, setResourceId] = useState(booking.resource_id)
  const [date, setDate] = useState(initialDate ?? booking.booking_date.slice(0, 10))
  const [startTime, setStartTime] = useState(initialStartTime ?? booking.start_time)
  const [preview, setPreview] = useState<ReschedulePreview | null>(null)
  const [checking, setChecking] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const duration = booking.duration_mins
  const selectedFacility = useMemo(
    () => facilities.data?.find((f) => f._id === resourceId),
    [facilities.data, resourceId],
  )

  const timeOptions = useMemo(() => {
    if (!selectedFacility) return []
    return startTimeOptions(selectedFacility.open_time, selectedFacility.close_time, duration)
  }, [selectedFacility, duration])

  const endTime = addMinutes(startTime, duration)
  const maxAdvanceDays = customer?.max_advance_booking_days
  const rescheduleDateMax = typeof maxAdvanceDays === "number"
    ? addDaysISO(todayISO(), maxAdvanceDays)
    : undefined

  useEffect(() => {
    void refreshCustomer()
  }, [refreshCustomer])

  useEffect(() => {
    if (!open) return
    setDate(initialDate ?? booking.booking_date.slice(0, 10))
    setStartTime(initialStartTime ?? booking.start_time)
    setPreview(null)
    setError(null)
  }, [booking._id, booking.booking_date, booking.start_time, initialDate, initialStartTime, open])

  function resetPreview() {
    setPreview(null)
    setError(null)
  }

  async function checkPreview() {
    setChecking(true)
    setError(null)
    setPreview(null)
    try {
      const res = await api.reschedulePreview(booking._id, {
        new_resource_id: resourceId,
        new_date: date,
        new_start_time: startTime,
        new_end_time: endTime,
      })
      setPreview(res)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setChecking(false)
    }
  }

  async function confirm() {
    setSubmitting(true)
    setError(null)
    try {
      const updated = await api.rescheduleBooking(booking._id, {
        new_resource_id: resourceId,
        new_date: date,
        new_start_time: startTime,
        new_end_time: endTime,
      })
      toast.success("Booking rescheduled.")
      onRescheduled(updated)
      onOpenChange(false)
    } catch (err) {
      if (isApiError(err)) setError(err.message)
      else setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const canConfirm = preview?.eligible && preview?.slot_available

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Reschedule booking</DialogTitle>
          <DialogDescription>
            Pick a new facility, date, and time. We&apos;ll check availability and any price difference before you
            confirm.
          </DialogDescription>
        </DialogHeader>

        <FieldGroup>
          <Field>
            <FieldLabel>Facility</FieldLabel>
            <Select
              value={resourceId}
              onValueChange={(v) => {
                setResourceId(v)
                setStartTime("")
                resetPreview()
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Choose a facility" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {(facilities.data ?? [])
                    .filter((f) => f.active)
                    .map((f) => (
                      <SelectItem key={f._id} value={f._id}>
                        {f.name} · {facilityLabel(f.type)}
                      </SelectItem>
                    ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>

          <Field>
            <FieldLabel htmlFor="reschedule-date">Date</FieldLabel>
            <Input
              id="reschedule-date"
              type="date"
              value={date}
              min={todayISO()}
              max={rescheduleDateMax}
              onChange={(e) => {
                const nextDate = e.target.value
                if (rescheduleDateMax && nextDate > rescheduleDateMax) {
                  setError(`Your account can reschedule up to ${maxAdvanceDays} days ahead.`)
                  return
                }
                setDate(nextDate)
                resetPreview()
              }}
            />
            {rescheduleDateMax ? (
              <p className="text-xs text-muted-foreground">
                Your account can reschedule up to {maxAdvanceDays} days ahead.
              </p>
            ) : null}
          </Field>

          <Field>
            <FieldLabel>Start time ({duration} min)</FieldLabel>
            {timeOptions.length > 0 ? (
              <ToggleGroup
                  value={startTime ? [startTime] : []}
                  onValueChange={(values) => {
                    const next = values[0]
                    if (next) {
                      setStartTime(String(next))
                    resetPreview()
                  }
                }}
                className="flex-wrap justify-start"
              >
                {timeOptions.map((t) => (
                  <ToggleGroupItem key={t} value={t} className="min-w-20">
                    {formatClock(t)}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            ) : (
              <p className="text-sm text-muted-foreground">No start times fit within opening hours.</p>
            )}
          </Field>

          {preview ? (
            <Alert variant={canConfirm ? "default" : "destructive"}>
              {canConfirm ? <CheckCircle2Icon /> : <AlertCircleIcon />}
              <AlertTitle>
                {!preview.eligible
                  ? "Not eligible to reschedule"
                  : !preview.slot_available
                    ? "Slot unavailable"
                    : "Ready to reschedule"}
              </AlertTitle>
              <AlertDescription className="flex flex-col gap-2">
                {preview.message ? <span>{preview.message}</span> : null}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">Reschedules left: {preview.remaining_reschedule_count}</Badge>
                  {preview.price_difference !== 0 ? (
                    <Badge variant="secondary">
                      {preview.price_difference > 0 ? "Extra due: " : "Refund: "}
                      {formatCurrency(Math.abs(preview.price_difference))}
                    </Badge>
                  ) : (
                    <Badge variant="secondary">No price change</Badge>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          ) : null}

          {error ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
        </FieldGroup>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          {canConfirm ? (
            <Button onClick={confirm} disabled={submitting}>
              {submitting ? <Spinner data-icon="inline-start" /> : null}
              {submitting ? "Rescheduling…" : "Confirm reschedule"}
            </Button>
          ) : (
            <Button onClick={checkPreview} disabled={!startTime || checking}>
              {checking ? <Spinner data-icon="inline-start" /> : null}
              {checking ? "Checking…" : "Check new slot"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
