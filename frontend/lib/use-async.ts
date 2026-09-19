"use client"

import { useCallback, useEffect, useState } from "react"
import { errorMessage } from "./errors"

interface AsyncState<T> {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => void
}

// Small fetch-on-mount hook with retry. We deliberately avoid fetching inside
// consumer components' effects — this hook centralizes it with proper cleanup.
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [nonce, setNonce] = useState(0)

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fn()
      .then((res) => {
        if (active) setData(res)
      })
      .catch((err) => {
        if (active) setError(errorMessage(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps])

  return { data, error, loading, reload }
}
