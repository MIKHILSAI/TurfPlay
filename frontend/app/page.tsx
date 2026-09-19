"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/auth-provider"
import { Spinner } from "@/components/ui/spinner"

export default function IndexPage() {
  const router = useRouter()
  const { status } = useAuth()

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard")
    else if (status === "unauthenticated") router.replace("/login")
  }, [status, router])

  return (
    <main className="flex min-h-svh items-center justify-center">
      <Spinner className="size-6 text-muted-foreground" />
    </main>
  )
}
