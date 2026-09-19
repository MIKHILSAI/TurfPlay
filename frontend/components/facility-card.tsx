import Link from "next/link"
import { ClockIcon, UsersIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatCurrency, facilityLabel } from "@/lib/format"
import type { Facility } from "@/lib/types"

export function FacilityCard({ facility }: { facility: Facility }) {
  return (
    <Card className="flex flex-col">
      <CardContent className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="font-medium">{facility.name}</span>
            <Badge variant="secondary" className="w-fit">
              {facilityLabel(facility.type)}
            </Badge>
          </div>
          <span className="text-right text-sm font-semibold tabular-nums">
            {formatCurrency(facility.hourly_rate)}
            <span className="block text-xs font-normal text-muted-foreground">per hour</span>
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <UsersIcon className="size-4" />
            Up to {facility.capacity}
          </span>
          <span className="flex items-center gap-1.5">
            <ClockIcon className="size-4" />
            {facility.open_time} – {facility.close_time}
          </span>
        </div>
        <Button asChild className="mt-1" disabled={!facility.active}>
          <Link href={`/book/${facility._id}`}>{facility.active ? "Select" : "Unavailable"}</Link>
        </Button>
      </CardContent>
    </Card>
  )
}
