"use client"

import { useState } from "react"
import { CrownIcon, CheckIcon } from "lucide-react"
import { PageHeader, ErrorState, CardSkeletonList } from "@/components/state-views"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { errorMessage, isApiError } from "@/lib/errors"
import { formatCurrency, formatDate } from "@/lib/format"
import type { MembershipPlan } from "@/lib/types"

export default function MembershipPage() {
  const membership = useAsync(() => api.getMembership(), [])
  const plans = useAsync(() => api.getMembershipPlans(), [])
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlan | null>(null)
  const [purchasing, setPurchasing] = useState(false)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

  const isActive = membership.data?.status === "active"

  async function confirmPurchase() {
    if (!selectedPlan) return
    setPurchasing(true)
    setPurchaseError(null)
    try {
      await api.subscribeMembership(selectedPlan.name.toLowerCase() as "monthly" | "annual")
      await membership.reload()
      window.dispatchEvent(new CustomEvent("turf:membership-changed"))
      setSelectedPlan(null)
    } catch (err) {
      setPurchaseError(
        isApiError(err) && err.code === "MEMBERSHIP_ALREADY_ACTIVE"
          ? "You already have an active membership. Your current plan was not changed."
          : errorMessage(err),
      )
    } finally {
      setPurchasing(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Membership" description="Unlock discounts, priority access, and more." />

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">Your membership</h2>
        {membership.loading ? (
          <CardSkeletonList count={1} />
        ) : membership.error ? (
          <ErrorState message={membership.error} onRetry={membership.reload} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CrownIcon className="size-5 text-amber-500" />
                {isActive ? membership.data?.type : "No active membership"}
                {isActive ? (
                  <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    Active
                  </Badge>
                ) : null}
              </CardTitle>
              <CardDescription>
                {isActive
                  ? "Your perks are applied automatically at checkout."
                  : "Choose a plan below to start saving on every booking."}
              </CardDescription>
            </CardHeader>
            {isActive ? (
              <CardContent className="flex flex-col gap-3">
                <div className="flex flex-wrap gap-2">
                  {membership.data?.discount_percent ? (
                    <Badge variant="secondary">{membership.data.discount_percent}% off bookings</Badge>
                  ) : null}
                  {membership.data?.priority_access ? <Badge variant="secondary">Priority access</Badge> : null}
                </div>
                <Separator />
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex flex-col">
                    <dt className="text-muted-foreground">Started</dt>
                    <dd>{formatDate(membership.data?.start_date)}</dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-muted-foreground">Renews / expires</dt>
                    <dd>{formatDate(membership.data?.expiry_date)}</dd>
                  </div>
                </dl>
              </CardContent>
            ) : null}
          </Card>
        )}
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">Plans</h2>
        {plans.loading ? (
          <CardSkeletonList count={2} />
        ) : plans.error ? (
          <ErrorState message={plans.error} onRetry={plans.reload} />
        ) : plans.data && plans.data.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {plans.data.map((plan) => {
              const current = isActive && membership.data?.type === plan.name
              return (
                <Card key={plan._id} className="flex flex-col">
                  <CardHeader>
                    <CardTitle>{plan.name}</CardTitle>
                    <CardDescription>
                      <span className="text-2xl font-semibold text-foreground">{formatCurrency(plan.price)}</span>
                      <span className="text-muted-foreground"> / {plan.duration}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col gap-2 text-sm">
                    {plan.discount_percent ? (
                      <span className="flex items-center gap-2">
                        <CheckIcon className="size-4 text-emerald-600" />
                        {plan.discount_percent}% off every booking
                      </span>
                    ) : null}
                    <span className="flex items-center gap-2">
                      <CheckIcon className="size-4 text-emerald-600" />
                      Priority slot access
                    </span>
                  </CardContent>
                  <CardFooter>
                    <Button
                      className="w-full"
                      variant={current ? "outline" : "default"}
                      disabled={current}
                      onClick={() => {
                        setPurchaseError(null)
                        setSelectedPlan(plan)
                      }}
                    >
                      {current ? "Current plan" : "Choose plan"}
                    </Button>
                  </CardFooter>
                </Card>
              )

            })}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No plans are available right now.</p>
        )}
      </section>

      <Dialog
        open={selectedPlan !== null}
        onOpenChange={(open) => {
          if (!open && !purchasing) setSelectedPlan(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm {selectedPlan?.name} membership</DialogTitle>
            <DialogDescription>
              Confirm {selectedPlan ? formatCurrency(selectedPlan.price) : ""} for {selectedPlan?.name}. This is a demo purchase; no real payment will be charged.
            </DialogDescription>
          </DialogHeader>
          {purchaseError ? (
            <Alert variant="destructive">
              <AlertDescription>{purchaseError}</AlertDescription>
            </Alert>
          ) : null}
          <DialogFooter>
            <DialogClose render={<Button variant="outline" disabled={purchasing} />}>Cancel</DialogClose>
            <Button onClick={confirmPurchase} disabled={purchasing}>
              {purchasing ? "Confirming…" : "Confirm purchase"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
