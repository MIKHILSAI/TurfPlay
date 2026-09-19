"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { api, clearToken, setToken } from "@/lib/api"
import { isApiError } from "@/lib/errors"
import type { Customer } from "@/lib/types"

interface AuthContextValue {
  customer: Customer | null
  status: "loading" | "authenticated" | "unauthenticated"
  login: (identifier: string, password: string) => Promise<void>
  signup: (body: { name: string; email: string; phone: string; password: string }) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading")

  const hydrate = useCallback(async () => {
    try {
      const me = await api.me()
      setCustomer(me)
      setStatus("authenticated")
    } catch (err) {
      clearToken()
      setCustomer(null)
      setStatus("unauthenticated")
      if (isApiError(err) && err.code === "MISSING_API_URL") {
        // Surface configuration issues once so the user knows what to fix.
        toast.error(err.message)
      }
    }
  }, [])

  useEffect(() => {
    void hydrate()
  }, [hydrate])

  useEffect(() => {
    function refreshMembershipState() {
      void hydrate()
    }
    window.addEventListener("turf:membership-changed", refreshMembershipState)
    return () => window.removeEventListener("turf:membership-changed", refreshMembershipState)
  }, [hydrate])

  // Global 401 handling: any query/mutation that 401s dispatches this event.
  useEffect(() => {
    function onUnauthorized() {
      clearToken()
      setCustomer(null)
      setStatus("unauthenticated")
      toast.error("Your session expired. Please sign in again.")
      router.push("/login")
    }
    window.addEventListener("turf:unauthorized", onUnauthorized)
    return () => window.removeEventListener("turf:unauthorized", onUnauthorized)
  }, [router])

  const login = useCallback(
    async (identifier: string, password: string) => {
      const res = await api.login({ identifier, password })
      setToken(res.token)
      setCustomer(res.customer)
      setStatus("authenticated")
    },
    [],
  )

  const signup = useCallback(
    async (body: { name: string; email: string; phone: string; password: string }) => {
      const res = await api.signup(body)
      setToken(res.token)
      setCustomer(res.customer)
      setStatus("authenticated")
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // Even if the backend call fails, clear local state.
    }
    clearToken()
    setCustomer(null)
    setStatus("unauthenticated")
    router.push("/login")
  }, [router])

  const value = useMemo<AuthContextValue>(
    () => ({ customer, status, login, signup, logout, refresh: hydrate }),
    [customer, status, login, signup, logout, hydrate],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
