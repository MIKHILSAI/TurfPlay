"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { AlertCircleIcon } from "lucide-react"
import { AuthShell } from "@/components/auth-shell"
import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Field, FieldGroup, FieldLabel, FieldError } from "@/components/ui/field"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { errorMessage } from "@/lib/errors"

export default function LoginPage() {
  const router = useRouter()
  const { login, status } = useAuth()
  const [identifier, setIdentifier] = useState("")
  const [password, setPassword] = useState("")
  const [errors, setErrors] = useState<{ identifier?: string; password?: string }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard")
  }, [status, router])

  function validate() {
    const next: typeof errors = {}
    if (!identifier.trim()) next.identifier = "Enter your email or phone."
    if (!password) next.password = "Enter your password."
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    if (!validate()) return
    setSubmitting(true)
    try {
      await login(identifier.trim(), password)
      router.replace("/dashboard")
    } catch (err) {
      setFormError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to book facilities and manage your reservations."
      footer={
        <>
          {"Don't have an account? "}
          <Link href="/signup" className="font-medium text-primary underline-offset-4 hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate>
        <FieldGroup>
          {formError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertTitle>Unable to sign in</AlertTitle>
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          ) : null}
          <Field data-invalid={!!errors.identifier}>
            <FieldLabel htmlFor="identifier">Email or phone</FieldLabel>
            <Input
              id="identifier"
              type="text"
              autoComplete="username"
              value={identifier}
              aria-invalid={!!errors.identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="you@example.com"
            />
            {errors.identifier ? <FieldError>{errors.identifier}</FieldError> : null}
          </Field>
          <Field data-invalid={!!errors.password}>
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              aria-invalid={!!errors.password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
            {errors.password ? <FieldError>{errors.password}</FieldError> : null}
          </Field>
          <Button type="submit" disabled={submitting}>
            {submitting ? <Spinner data-icon="inline-start" /> : null}
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </FieldGroup>
      </form>
    </AuthShell>
  )
}
