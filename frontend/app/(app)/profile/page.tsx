"use client"

import { LogOutIcon, MailIcon, PhoneIcon, UserIcon } from "lucide-react"
import { useAuth } from "@/components/auth-provider"
import { PageHeader } from "@/components/state-views"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { formatDateTime } from "@/lib/format"

function initials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

export default function ProfilePage() {
  const { customer, logout } = useAuth()
  if (!customer) return null

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Profile" description="Your account details." />

      <Card className="max-w-xl">
        <CardHeader>
          <div className="flex items-center gap-4">
            <Avatar className="size-14">
              <AvatarFallback className="text-lg">{initials(customer.name)}</AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <CardTitle className="text-xl">{customer.name}</CardTitle>
              {customer.created_at ? (
                <span className="text-sm text-muted-foreground">Member since {formatDateTime(customer.created_at)}</span>
              ) : null}
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Separator />
          <dl className="flex flex-col gap-4">
            <Detail icon={UserIcon} label="Full name" value={customer.name} />
            <Detail icon={MailIcon} label="Email" value={customer.email} />
            <Detail icon={PhoneIcon} label="Phone" value={customer.phone} />
          </dl>
          <Separator />
          <Button variant="outline" className="w-fit" onClick={() => void logout()}>
            <LogOutIcon data-icon="inline-start" />
            Log out
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

function Detail({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
        <Icon className="size-4" />
      </span>
      <div className="flex flex-col">
        <dt className="text-xs text-muted-foreground">{label}</dt>
        <dd className="text-sm font-medium">{value}</dd>
      </div>
    </div>
  )
}
