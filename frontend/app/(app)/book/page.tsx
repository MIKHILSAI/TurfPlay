"use client"

import { useState, useMemo } from "react"
import { PageHeader, ErrorState } from "@/components/state-views"
import { FacilityCard } from "@/components/facility-card"
import { Skeleton } from "@/components/ui/skeleton"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import { SearchXIcon } from "lucide-react"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { facilityLabel } from "@/lib/format"
import type { FacilityType } from "@/lib/types"

const TYPES: (FacilityType | "all")[] = ["all", "badminton", "football", "tennis", "multipurpose"]

function normalizeFacilityType(type: unknown): string {
  const value = Array.isArray(type) ? type[0] : type
  const normalized = String(value ?? "").trim().toLowerCase()
  return normalized === "multipurpose room" ? "multipurpose" : normalized
}

export default function BookPage() {
  const facilities = useAsync(() => api.listResources(), [])
  const [filter, setFilter] = useState<FacilityType | "all">("all")

  const filtered = useMemo(() => {
    if (!facilities.data) return []
    const normalizedFilter = normalizeFacilityType(filter)
    if (normalizedFilter === "all") return facilities.data
    return facilities.data.filter((f) => normalizeFacilityType(f.type) === normalizedFilter)
  }, [facilities.data, filter])

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Book a facility" description="Choose a court or room to check availability and reserve." />

      <ToggleGroup
        value={filter}
        onValueChange={(v) => {
          const next = Array.isArray(v) ? v[0] : v
          if (next) setFilter(String(next) as FacilityType | "all")
        }}
        className="flex-wrap justify-start"
      >
        {TYPES.map((t) => (
          <button
            type="button"
            key={t}
            aria-pressed={filter === t}
            onClick={() => setFilter(t)}
            className="rounded-md border px-3 py-2 text-sm font-medium transition-colors hover:bg-muted aria-pressed:bg-primary aria-pressed:text-primary-foreground"
          >
            {t === "all" ? "All" : facilityLabel(t as FacilityType)}
          </button>
        ))}
      </ToggleGroup>

      {facilities.loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      ) : facilities.error ? (
        <ErrorState message={facilities.error} onRetry={facilities.reload} />
      ) : filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((f) => (
            <FacilityCard key={f._id} facility={f} />
          ))}
        </div>
      ) : (
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <SearchXIcon />
            </EmptyMedia>
            <EmptyTitle>No facilities found</EmptyTitle>
            <EmptyDescription>Try a different facility type.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
    </div>
  )
}
