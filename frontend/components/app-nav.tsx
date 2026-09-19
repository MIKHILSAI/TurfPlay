"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboardIcon,
  MessagesSquareIcon,
  CalendarPlusIcon,
  TicketIcon,
  CrownIcon,
  UserIcon,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"

export interface NavItem {
  href: string
  label: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboardIcon },
  { href: "/assistant", label: "AI Assistant", icon: MessagesSquareIcon },
  { href: "/book", label: "Book", icon: CalendarPlusIcon },
  { href: "/bookings", label: "My Bookings", icon: TicketIcon },
  { href: "/membership", label: "Membership", icon: CrownIcon },
  { href: "/profile", label: "Profile", icon: UserIcon },
]

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function DesktopNav() {
  const pathname = usePathname()
  return (
    <nav className="flex flex-col gap-1" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item.href)
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4 shrink-0" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

export function MobileNav() {
  const pathname = usePathname()
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex items-stretch border-t bg-background/95 backdrop-blur md:hidden"
      aria-label="Primary"
    >
      {NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item.href)
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium",
              active ? "text-primary" : "text-muted-foreground",
            )}
          >
            <Icon className="size-5" />
            <span className="truncate">{item.label.replace("AI ", "")}</span>
          </Link>
        )
      })}
    </nav>
  )
}
