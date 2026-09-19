import type { ReactNode } from "react"
import { ZapIcon } from "lucide-react"

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}) {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center bg-muted/40 px-4 py-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <ZapIcon className="size-6" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">TurfPlay</h1>
        </div>
        <div className="flex flex-col gap-1 text-center">
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        {children}
        <div className="text-center text-sm text-muted-foreground">{footer}</div>
      </div>
    </main>
  )
}
