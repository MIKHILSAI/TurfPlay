"use client"

import Link from "next/link"
import { useEffect } from "react"
import { CalendarPlusIcon, MessagesSquareIcon, CrownIcon, ArrowRightIcon } from "lucide-react"
import { useAuth } from "@/components/auth-provider"
import { PageHeader, ErrorState, CardSkeletonList } from "@/components/state-views"
import { BookingCard } from "@/components/booking-card"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent } from "@/components/ui/empty"
import { TicketIcon } from "lucide-react"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { formatCurrency } from "@/lib/format"

export default function DashboardPage() {
  const { customer } = useAuth()
  const bookings = useAsync(() => api.listBookings("upcoming"), [])
  const membership = useAsync(() => api.getMembership(), [])

  useEffect(() => {
    function reloadBookings() {
      bookings.reload()
    }
    function reloadMembership() {
      membership.reload()
    }
    window.addEventListener("turf:bookings-changed", reloadBookings)
    window.addEventListener("turf:membership-changed", reloadMembership)
    return () => {
      window.removeEventListener("turf:bookings-changed", reloadBookings)
      window.removeEventListener("turf:membership-changed", reloadMembership)
    }
  }, [bookings.reload, membership.reload])

  const firstName = customer?.name?.split(" ")[0] ?? "there"

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title={`Welcome back, ${firstName}`} description="Here's what's coming up and what you can do next." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <QuickAction
          href="/book"
          title="Book a facility"
          description="Find a court and reserve a slot."
          icon={CalendarPlusIcon}
        />
        <QuickAction
          href="/assistant"
          title="Ask the assistant"
          description="Book or manage reservations by chat."
          icon={MessagesSquareIcon}
        />
        <QuickAction
          href="/membership"
          title="Membership"
          description="View perks and manage your plan."
          icon={CrownIcon}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="flex flex-col gap-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Upcoming bookings</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/bookings">
                View all
                <ArrowRightIcon data-icon="inline-end" />
              </Link>
            </Button>
          </div>
          {bookings.loading ? (
            <CardSkeletonList count={2} />
          ) : bookings.error ? (
            <ErrorState message={bookings.error} onRetry={bookings.reload} />
          ) : bookings.data && bookings.data.length > 0 ? (
            <div className="flex flex-col gap-4">
              {bookings.data.slice(0, 4).map((b) => (
                <BookingCard key={b._id} booking={b} />
              ))}
            </div>
          ) : (
            <Empty className="border">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <TicketIcon />
                </EmptyMedia>
                <EmptyTitle>No upcoming bookings</EmptyTitle>
                <EmptyDescription>Reserve a facility to see it here.</EmptyDescription>
              </EmptyHeader>
              <EmptyContent>
                <Button asChild>
                  <Link href="/book">Book a facility</Link>
                </Button>
              </EmptyContent>
            </Empty>
          )}
        </section>

        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold">Membership</h2>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CrownIcon className="size-4 text-amber-500" />
                {membership.loading
                  ? "Loading…"
                  : membership.data?.status === "active"
                    ? membership.data.type
                    : "No active plan"}
              </CardTitle>
              <CardDescription>
                {membership.data?.status === "active"
                  ? "Enjoy discounts and priority access."
                  : "Upgrade to unlock discounts and priority booking."}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {membership.data?.status === "active" ? (
                <div className="flex flex-wrap gap-2">
                  {membership.data.discount_percent ? (
                    <Badge variant="secondary">{membership.data.discount_percent}% off</Badge>
                  ) : null}
                  {membership.data.priority_access ? <Badge variant="secondary">Priority access</Badge> : null}
                </div>
              ) : null}
              <Button asChild variant={membership.data?.status === "active" ? "outline" : "default"}>
                <Link href="/membership">
                  {membership.data?.status === "active" ? "Manage membership" : "View plans"}
                </Link>
              </Button>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  )
}

function QuickAction({
  href,
  title,
  description,
  icon: Icon,
}: {
  href: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}) {
  return (
    <Link href={href} className="group">
      <Card className="h-full transition-colors group-hover:border-primary/50">
        <CardContent className="flex items-start gap-3 p-4">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="size-5" />
          </span>
          <div className="flex flex-col gap-0.5">
            <span className="font-medium">{title}</span>
            <span className="text-sm text-muted-foreground">{description}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
