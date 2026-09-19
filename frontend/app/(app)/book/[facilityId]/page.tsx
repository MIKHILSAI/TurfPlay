"use client"

import { use, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { ArrowLeftIcon, CheckCircle2Icon, AlertCircleIcon } from "lucide-react"
import { PageHeader, ErrorState, CardSkeletonList } from "@/components/state-views"
import { PriceBreakdownView } from "@/components/price-breakdown"
import { EquipmentPicker } from "@/components/equipment-picker"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectGroup, SelectItem } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Switch } from "@/components/ui/switch"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { Separator } from "@/components/ui/separator"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { isApiError, errorMessage } from "@/lib/errors"
import { facilityLabel, formatCurrency } from "@/lib/format"
import { startTimeOptions, addMinutes, addDaysISO, formatClock, todayISO } from "@/lib/time"
import { useAuth } from "@/components/auth-provider"
import type { AlternativeSlot, EquipmentSelection, PriceBreakdown, AvailabilityResponse } from "@/lib/types"

const DURATIONS = [
  { value: 30, label: "30 min" },
  { value: 60, label: "1 hour" },
  { value: 90, label: "1.5 hours" },
  { value: 120, label: "2 hours" },
]

export default function BookFacilityPage({ params }: { params: Promise<{ facilityId: string }> }) {
  const { facilityId } = use(params)
  const router = useRouter()
  const { customer, refresh: refreshCustomer } = useAuth()
  const facility = useAsync(() => api.getResource(facilityId), [facilityId])
  const membership = useAsync(() => api.getMembership(), [])

  const [date, setDate] = useState(todayISO())
  const [duration, setDuration] = useState(60)
  const [startTime, setStartTime] = useState<string>("")
  const [equipment, setEquipment] = useState<EquipmentSelection[]>([])
  const [applyMembership, setApplyMembership] = useState(false)

  const [availability, setAvailability] = useState<AvailabilityResponse | null>(null)
  const [checkingSlot, setCheckingSlot] = useState(false)
  const [quote, setQuote] = useState<PriceBreakdown | null>(null)
  const [quoting, setQuoting] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const hasMembership = membership.data?.status === "active"
  const maxAdvanceDays = customer?.max_advance_booking_days
  const bookingDateMax = typeof maxAdvanceDays === "number"
    ? addDaysISO(todayISO(), maxAdvanceDays)
    : undefined

  useEffect(() => {
    void refreshCustomer()

    function refreshOnFocus() {
      void refreshCustomer()
    }

    window.addEventListener("focus", refreshOnFocus)
    function refreshMembership() {
      void refreshCustomer()
      membership.reload()
    }
    window.addEventListener("turf:membership-changed", refreshMembership)
    return () => {
      window.removeEventListener("focus", refreshOnFocus)
      window.removeEventListener("turf:membership-changed", refreshMembership)
    }
  }, [membership.reload, refreshCustomer])

  const timeOptions = useMemo(() => {
    if (!facility.data) return []
    return startTimeOptions(facility.data.open_time, facility.data.close_time, duration)
  }, [facility.data, duration])

  const endTime = startTime ? addMinutes(startTime, duration) : ""

  // Any change to slot inputs invalidates a prior availability/quote result.
  function resetDerived() {
    setAvailability(null)
    setQuote(null)
    setActionError(null)
  }

  async function checkAvailability() {
    if (!startTime) {
      toast.error("Choose a start time first.")
      return
    }
    setCheckingSlot(true)
    setActionError(null)
    setAvailability(null)
    setQuote(null)
    try {
      const res = await api.checkAvailability(facilityId, { date, start_time: startTime, end_time: endTime })
      setAvailability(res)
      if (res.available) {
        await getQuote()
      }
    } catch (err) {
      if (isApiError(err) && err.alternatives) {
        setAvailability({ available: false, message: err.message, alternatives: err.alternatives })
      } else {
        setActionError(errorMessage(err))
      }
    } finally {
      setCheckingSlot(false)
    }
  }

  async function getQuote() {
    setQuoting(true)
    try {
      const res = await api.quote({
        resource_id: facilityId,
        date,
        start_time: startTime,
        end_time: endTime,
        equipment,
        apply_membership: applyMembership && hasMembership,
      })
      setQuote(res)
    } catch (err) {
      setActionError(errorMessage(err))
    } finally {
      setQuoting(false)
    }
  }

  async function confirmBooking() {
    setConfirming(true)
    setActionError(null)
    try {
      const booking = await api.createBooking({
        resource_id: facilityId,
        date,
        start_time: startTime,
        end_time: endTime,
        equipment,
        apply_membership: applyMembership && hasMembership,
      })
      toast.success("Booking confirmed!")
      router.push(`/bookings/${booking._id}?confirmed=1`)
    } catch (err) {
      if (isApiError(err) && err.alternatives) {
        setAvailability({ available: false, message: err.message, alternatives: err.alternatives })
        setQuote(null)
      }
      setActionError(errorMessage(err))
    } finally {
      setConfirming(false)
    }
  }

  function pickAlternative(alt: AlternativeSlot) {
    setStartTime(alt.start_time)
    resetDerived()
  }

  if (facility.loading) {
    return (
      <div className="flex flex-col gap-6">
        <BackLink />
        <CardSkeletonList count={2} />
      </div>
    )
  }

  if (facility.error || !facility.data) {
    return (
      <div className="flex flex-col gap-6">
        <BackLink />
        <ErrorState message={facility.error ?? "Facility not found."} onRetry={facility.reload} />
      </div>
    )
  }

  const f = facility.data

  return (
    <div className="flex flex-col gap-6">
      <BackLink />
      <PageHeader
        title={f.name}
        description={`${facilityLabel(f.type)} · Open ${f.open_time}–${f.close_time} · ${formatCurrency(f.hourly_rate)}/hr`}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Choose your slot</CardTitle>
              <CardDescription>Pick a date, duration, and start time, then check availability.</CardDescription>
            </CardHeader>
            <CardContent>
              <FieldGroup>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="date">Date</FieldLabel>
                    <Input
                      id="date"
                      type="date"
                      value={date}
                      min={todayISO()}
                      max={bookingDateMax}
                      onChange={(e) => {
                        const nextDate = e.target.value
                        if (bookingDateMax && nextDate > bookingDateMax) {
                          setActionError(`Your account can book up to ${maxAdvanceDays} days ahead.`)
                          return
                        }
                        setDate(nextDate)
                        resetDerived()
                      }}
                    />
                    {bookingDateMax ? (
                      <p className="text-xs text-muted-foreground">
                        Your account can book up to {maxAdvanceDays} days ahead.
                      </p>
                    ) : null}
                  </Field>
                  <Field>
                    <FieldLabel>Duration</FieldLabel>
                    <Select
                      value={String(duration)}
                      onValueChange={(v) => {
                        setDuration(Number(v))
                        setStartTime("")
                        resetDerived()
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {DURATIONS.map((d) => (
                            <SelectItem key={d.value} value={String(d.value)}>
                              {d.label}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                </div>

                <Field>
                  <FieldLabel>Start time</FieldLabel>
                  {timeOptions.length > 0 ? (
                    <ToggleGroup
                      value={startTime ? [startTime] : []}
                      onValueChange={(values) => {
                        const next = values[0]
                        if (next) {
                          setStartTime(String(next))
                          resetDerived()
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
                    <p className="text-sm text-muted-foreground">
                      No start times fit this duration within opening hours.
                    </p>
                  )}
                </Field>

                {startTime ? (
                  <p className="text-sm text-muted-foreground">
                    Selected: <span className="font-medium text-foreground">{formatClock(startTime)}</span> –{" "}
                    <span className="font-medium text-foreground">{formatClock(endTime)}</span>
                  </p>
                ) : null}
              </FieldGroup>
            </CardContent>
          </Card>

          <EquipmentPicker
            value={equipment}
            facilityType={f.type}
            onChange={(next) => {
              setEquipment(next)
              setQuote(null)
            }}
          />

          <Card>
            <CardHeader>
              <CardTitle>Membership discount</CardTitle>
              <CardDescription>
                {hasMembership
                  ? "Apply your active membership perks to this booking."
                  : "You don't have an active membership. Discounts won't apply."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between gap-4">
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Apply membership discount</span>
                  {hasMembership && membership.data?.discount_percent ? (
                    <span className="text-xs text-muted-foreground">
                      Saves {membership.data.discount_percent}% on the base amount
                    </span>
                  ) : null}
                </div>
                <Switch
                  checked={applyMembership && hasMembership}
                  disabled={!hasMembership}
                  onCheckedChange={(c) => {
                    setApplyMembership(c)
                    setQuote(null)
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-4 lg:sticky lg:top-20 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
              <CardDescription>Check availability to see live pricing.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {availability && !availability.available ? (
                <Alert variant="destructive">
                  <AlertCircleIcon />
                  <AlertTitle>Slot unavailable</AlertTitle>
                  <AlertDescription className="flex flex-col gap-2">
                    <span>{availability.message ?? "That slot is already booked."}</span>
                    {availability.alternatives && availability.alternatives.length > 0 ? (
                      <div className="flex flex-col gap-1.5">
                        <span className="text-xs font-medium">Suggested alternatives:</span>
                        <div className="flex flex-wrap gap-2">
                          {availability.alternatives.map((alt, i) => (
                            <Button
                              key={i}
                              size="sm"
                              variant="outline"
                              onClick={() => pickAlternative(alt)}
                            >
                              {formatClock(alt.start_time)}
                            </Button>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </AlertDescription>
                </Alert>
              ) : null}

              {availability?.available ? (
                <Badge
                  variant="secondary"
                  className="w-fit gap-1 border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                >
                  <CheckCircle2Icon className="size-3.5" />
                  Slot available
                </Badge>
              ) : null}

              {quoting ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Spinner className="size-4" />
                  Calculating price…
                </div>
              ) : quote ? (
                <PriceBreakdownView breakdown={quote} />
              ) : (
                <p className="text-sm text-muted-foreground">No price yet.</p>
              )}

              {actionError ? (
                <Alert variant="destructive">
                  <AlertCircleIcon />
                  <AlertDescription>{actionError}</AlertDescription>
                </Alert>
              ) : null}

              <Separator />

              {!quote || !availability?.available ? (
                <Button onClick={checkAvailability} disabled={!startTime || checkingSlot}>
                  {checkingSlot ? <Spinner data-icon="inline-start" /> : null}
                  {checkingSlot ? "Checking…" : "Check availability & price"}
                </Button>
              ) : (
                <div className="flex flex-col gap-2">
                  <Button onClick={confirmBooking} disabled={confirming}>
                    {confirming ? <Spinner data-icon="inline-start" /> : null}
                    {confirming ? "Confirming…" : `Confirm booking · ${formatCurrency(quote.total_amount)}`}
                  </Button>
                  <Button variant="ghost" onClick={checkAvailability} disabled={checkingSlot}>
                    Re-check price
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function BackLink() {
  return (
    <Button asChild variant="ghost" size="sm" className="w-fit -ml-2">
      <Link href="/book">
        <ArrowLeftIcon data-icon="inline-start" />
        All facilities
      </Link>
    </Button>
  )
}
