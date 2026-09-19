"use client"

import { MinusIcon, PlusIcon, PackageIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { formatCurrency } from "@/lib/format"
import type { EquipmentSelection } from "@/lib/types"

function equipmentMatchesFacility(equipmentType: string, facilityType: string): boolean {
  const equipmentPrefix = equipmentType.trim().toLowerCase().split("_")[0]
  const normalizedFacility = facilityType.trim().toLowerCase()
  if (normalizedFacility === "multipurpose room" || normalizedFacility === "multipurpose") {
    return equipmentType.trim().toLowerCase().startsWith("multipurpose_room_")
  }
  return equipmentPrefix === normalizedFacility
}

export function EquipmentPicker({
  value,
  onChange,
  facilityType,
}: {
  value: EquipmentSelection[]
  onChange: (next: EquipmentSelection[]) => void
  facilityType: string
}) {
  const equipment = useAsync(() => api.listEquipment(), [])

  function quantityFor(id: string): number {
    return value.find((e) => e.equipment_id === id)?.quantity ?? 0
  }

  function setQuantity(id: string, quantity: number) {
    const clamped = Math.max(0, quantity)
    const others = value.filter((e) => e.equipment_id !== id)
    onChange(clamped === 0 ? others : [...others, { equipment_id: id, quantity: clamped }])
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add equipment</CardTitle>
        <CardDescription>Optional rentals added to your total. Deposits are refundable.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {equipment.loading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full rounded-md" />
            ))}
          </div>
        ) : equipment.error ? (
          <p className="text-sm text-muted-foreground">Equipment couldn&apos;t be loaded right now.</p>
        ) : equipment.data && equipment.data.length > 0 ? (
          equipment.data
            .filter((item) => item.active && equipmentMatchesFacility(item.type, facilityType))
            .map((item) => {
              const qty = quantityFor(item._id)
              const atMax = qty >= item.quantity_available
              return (
                <div key={item._id} className="flex items-center justify-between gap-3 rounded-md border p-3">
                  <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
                      <PackageIcon className="size-4" />
                    </span>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{item.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatCurrency(item.price)} · {item.quantity_available} available
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      size="icon"
                      variant="outline"
                      className="size-8"
                      aria-label={`Remove one ${item.name}`}
                      disabled={qty === 0}
                      onClick={() => setQuantity(item._id, qty - 1)}
                    >
                      <MinusIcon />
                    </Button>
                    <span className="w-6 text-center text-sm tabular-nums" aria-live="polite">
                      {qty}
                    </span>
                    <Button
                      type="button"
                      size="icon"
                      variant="outline"
                      className="size-8"
                      aria-label={`Add one ${item.name}`}
                      disabled={atMax}
                      onClick={() => setQuantity(item._id, qty + 1)}
                    >
                      <PlusIcon />
                    </Button>
                  </div>
                </div>
              )
            })
        ) : (
          <p className="text-sm text-muted-foreground">No equipment available for rental.</p>
        )}
      </CardContent>
    </Card>
  )
}
