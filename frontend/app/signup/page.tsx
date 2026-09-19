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

interface FormErrors {
  name?: string
  email?: string
  phone?: string
  password?: string
  confirmPassword?: string
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^[0-9+\-\s()]{7,15}$/

export default function SignupPage() {
  const router = useRouter()
  const { signup, status } = useAuth()
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirmPassword: "" })
  const [errors, setErrors] = useState<FormErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard")
  }, [status, router])

  function update(key: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function validate() {
    const next: FormErrors = {}
    if (!form.name.trim()) next.name = "Enter your full name."
    if (!form.email.trim()) next.email = "Enter your email."
    else if (!EMAIL_RE.test(form.email.trim())) next.email = "Enter a valid email address."
    if (!form.phone.trim()) next.phone = "Enter your phone number."
    else if (!PHONE_RE.test(form.phone.trim())) next.phone = "Enter a valid phone number."
    if (!form.password) next.password = "Choose a password."
    else if (form.password.length < 8) next.password = "Use at least 8 characters."
    if (form.confirmPassword !== form.password) next.confirmPassword = "Passwords don't match."
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    if (!validate()) return
    setSubmitting(true)
    try {
      await signup({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
      })
      router.replace("/dashboard")
    } catch (err) {
      setFormError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Sign up to start booking courts and renting equipment."
      footer={
        <>
          {"Already have an account? "}
          <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate>
        <FieldGroup>
          {formError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertTitle>Unable to create account</AlertTitle>
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          ) : null}
          <Field data-invalid={!!errors.name}>
            <FieldLabel htmlFor="name">Full name</FieldLabel>
            <Input
              id="name"
              value={form.name}
              autoComplete="name"
              aria-invalid={!!errors.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Jordan Smith"
            />
            {errors.name ? <FieldError>{errors.name}</FieldError> : null}
          </Field>
          <Field data-invalid={!!errors.email}>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              value={form.email}
              autoComplete="email"
              aria-invalid={!!errors.email}
              onChange={(e) => update("email", e.target.value)}
              placeholder="you@example.com"
            />
            {errors.email ? <FieldError>{errors.email}</FieldError> : null}
          </Field>
          <Field data-invalid={!!errors.phone}>
            <FieldLabel htmlFor="phone">Phone</FieldLabel>
            <Input
              id="phone"
              type="tel"
              value={form.phone}
              autoComplete="tel"
              aria-invalid={!!errors.phone}
              onChange={(e) => update("phone", e.target.value)}
              placeholder="+91 98765 43210"
            />
            {errors.phone ? <FieldError>{errors.phone}</FieldError> : null}
          </Field>
          <Field data-invalid={!!errors.password}>
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <Input
              id="password"
              type="password"
              value={form.password}
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              onChange={(e) => update("password", e.target.value)}
              placeholder="At least 8 characters"
            />
            {errors.password ? <FieldError>{errors.password}</FieldError> : null}
          </Field>
          <Field data-invalid={!!errors.confirmPassword}>
            <FieldLabel htmlFor="confirmPassword">Confirm password</FieldLabel>
            <Input
              id="confirmPassword"
              type="password"
              value={form.confirmPassword}
              autoComplete="new-password"
              aria-invalid={!!errors.confirmPassword}
              onChange={(e) => update("confirmPassword", e.target.value)}
              placeholder="Re-enter your password"
            />
            {errors.confirmPassword ? <FieldError>{errors.confirmPassword}</FieldError> : null}
          </Field>
          <Button type="submit" disabled={submitting}>
            {submitting ? <Spinner data-icon="inline-start" /> : null}
            {submitting ? "Creating account…" : "Create account"}
          </Button>
        </FieldGroup>
      </form>
    </AuthShell>
  )
}
