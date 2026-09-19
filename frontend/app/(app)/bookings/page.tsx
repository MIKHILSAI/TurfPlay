"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { TicketIcon, CalendarPlusIcon } from "lucide-react"
import { PageHeader, ErrorState, CardSkeletonList } from "@/components/state-views"
import { BookingCard } from "@/components/booking-card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent } from "@/components/ui/empty"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"

type Filter = "upcoming" | "past" | "cancelled"

export default function BookingsPage() {
  const [tab, setTab] = useState<Filter>("upcoming")
  const bookings = useAsync(() => api.listBookings(tab), [tab])

  useEffect(() => {
    function reloadBookings() {
      bookings.reload()
    }
    window.addEventListener("turf:bookings-changed", reloadBookings)
    return () => window.removeEventListener("turf:bookings-changed", reloadBookings)
  }, [bookings.reload])

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="My bookings"
        description="Review upcoming reservations and your booking history."
        action={
          <Button asChild>
            <Link href="/book">
              <CalendarPlusIcon data-icon="inline-start" />
              New booking
            </Link>
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={(v) => setTab(v as Filter)}>
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="past">Past</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
        </TabsList>

        <TabsContent value={tab} className="mt-6">
          {bookings.loading ? (
            <CardSkeletonList count={3} />
          ) : bookings.error ? (
            <ErrorState message={bookings.error} onRetry={bookings.reload} />
          ) : bookings.data && bookings.data.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {bookings.data.map((b) => (
                <BookingCard key={b._id} booking={b} />
              ))}
            </div>
          ) : (
            <Empty className="border">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <TicketIcon />
                </EmptyMedia>
                <EmptyTitle>No {tab} bookings</EmptyTitle>
                <EmptyDescription>
                  {tab === "upcoming"
                    ? "You have no upcoming reservations."
                    : tab === "past"
                      ? "Your completed bookings will appear here."
                      : "You haven't cancelled any bookings."}
                </EmptyDescription>
              </EmptyHeader>
              {tab === "upcoming" ? (
                <EmptyContent>
                  <Button asChild>
                    <Link href="/book">Book a facility</Link>
                  </Button>
                </EmptyContent>
              ) : null}
            </Empty>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
