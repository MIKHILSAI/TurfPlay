"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { AlertCircleIcon } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api"
import { errorMessage } from "@/lib/errors"
import { formatCurrency } from "@/lib/format"
import type { Booking, CancelPreview } from "@/lib/types"

export function CancelDialog({
  booking,
  open,
  onOpenChange,
  onCancelled,
}: {
  booking: Booking
  open: boolean
  onOpenChange: (open: boolean) => void
  onCancelled: (updated: Booking) => void
}) {
  const [preview, setPreview] = useState<CancelPreview | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setPreview(null)
    setError(null)
    setLoadingPreview(true)
    api
      .cancelPreview(booking._id)
      .then(setPreview)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoadingPreview(false))
  }, [booking._id, open])

  // Fetch the refund preview each time the dialog opens.
  function handleOpenChange(next: boolean) {
    onOpenChange(next)
  }

  async function confirmCancel() {
    setSubmitting(true)
    setError(null)
    try {
      const updated = await api.cancelBooking(booking._id)
      toast.success("Booking cancelled.")
      onCancelled(updated)
      onOpenChange(false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cancel this booking?</DialogTitle>
          <DialogDescription>
            Review your refund eligibility before confirming. This can&apos;t be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {loadingPreview ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner className="size-4" />
              Checking refund eligibility…
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : preview ? (
            <Alert variant={preview.eligible ? "default" : "destructive"}>
              <AlertCircleIcon />
              <AlertTitle>
                {preview.eligible
                  ? `Refund: ${formatCurrency(preview.refund_amount)}`
                  : "Not eligible for a refund"}
              </AlertTitle>
              <AlertDescription>{preview.message}</AlertDescription>
            </Alert>
          ) : null}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
            Keep booking
          </Button>
          <Button variant="destructive" onClick={confirmCancel} disabled={submitting || loadingPreview}>
            {submitting ? <Spinner data-icon="inline-start" /> : null}
            {submitting ? "Cancelling…" : "Cancel booking"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
