"use client"

import { useEffect, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/auth-provider"
import { Spinner } from "@/components/ui/spinner"

export function RouteGuard({ children }: { children: ReactNode }) {
  const router = useRouter()
  const { status } = useAuth()

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login")
  }, [status, router])

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-svh items-center justify-center" aria-live="polite" aria-busy="true">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Spinner className="size-6" />
          <p className="text-sm">Loading your session…</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
