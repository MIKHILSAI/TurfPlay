import type { ReactNode } from "react"
import { AlertCircleIcon, RotateCcwIcon } from "lucide-react"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-balance">{title}</h1>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert variant="destructive">
      <AlertCircleIcon />
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription className="flex flex-col items-start gap-3">
        <span>{message}</span>
        {onRetry ? (
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RotateCcwIcon data-icon="inline-start" />
            Try again
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  )
}

export function CardSkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-4" aria-busy="true" aria-live="polite">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex flex-col gap-3 rounded-lg border p-4">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  )
}
