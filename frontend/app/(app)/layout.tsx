"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { ZapIcon, LogOutIcon } from "lucide-react"
import { RouteGuard } from "@/components/route-guard"
import { DesktopNav, MobileNav } from "@/components/app-nav"
import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

function initials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

function AppChrome({ children }: { children: ReactNode }) {
  const { customer, logout } = useAuth()

  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ZapIcon className="size-5" />
          </span>
          <span>TurfPlay</span>
        </Link>
        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-2 sm:flex">
            <Avatar className="size-8">
              <AvatarFallback>{customer ? initials(customer.name) : "?"}</AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium">{customer?.name}</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => void logout()}>
            <LogOutIcon data-icon="inline-start" />
            <span className="hidden sm:inline">Log out</span>
          </Button>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1">
        <aside className="hidden w-60 shrink-0 border-r p-4 md:block">
          <DesktopNav />
        </aside>
        <main className="min-w-0 flex-1 px-4 pb-24 pt-6 md:px-8 md:pb-10">{children}</main>
      </div>

      <MobileNav />
    </div>
  )
}

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard>
      <AppChrome>{children}</AppChrome>
    </RouteGuard>
  )
}
