import { ApiError } from "./errors"
import type {
  AvailabilityResponse,
  Booking,
  BookingRequest,
  BookingStatus,
  CancelPreview,
  Customer,
  Equipment,
  Facility,
  LoginResponse,
  Membership,
  MembershipPlan,
  PriceBreakdown,
  QuoteRequest,
  ReschedulePreview,
  ReschedulePreviewRequest,
  AssistantResponse,
} from "./types"

const TOKEN_KEY = "turf_auth_token"

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return
  window.localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(TOKEN_KEY)
}

function baseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL
  if (!url) {
    throw new ApiError(
      0,
      {
        error_code: "MISSING_API_URL",
        message:
          "NEXT_PUBLIC_API_BASE_URL is not set. Add it in Project Settings so the frontend knows where the FastAPI backend lives.",
      },
      "Backend URL is not configured.",
    )
  }
  return url.replace(/\/$/, "")
}

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | number | undefined>
  auth?: boolean
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, auth = true } = options

  let url = `${baseUrl()}${path}`
  if (query) {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value))
      }
    }
    const qs = params.toString()
    if (qs) url += `?${qs}`
  }

  const headers: Record<string, string> = {}
  if (body !== undefined) headers["Content-Type"] = "application/json"
  if (auth) {
    const token = getToken()
    if (token) headers["Authorization"] = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(
      0,
      { error_code: "NETWORK_ERROR", message: "Could not reach the backend. Check your connection and the API URL." },
      "Network error.",
    )
  }

  if (res.status === 204) return undefined as T

  let data: unknown = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }

  if (!res.ok) {
    // Global session-expiry signal. The AuthProvider listens for this and
    // clears the token + redirects to /login. Skipped for the auth calls
    // themselves so a bad login shows an inline error instead.
    if (res.status === 401 && auth && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("turf:unauthorized"))
    }
    throw new ApiError(res.status, data as never, `Request failed with status ${res.status}.`)
  }

  return data as T
}

export const api = {
  // Auth
  signup: (body: { name: string; email: string; phone: string; password: string }) =>
    request<LoginResponse>("/auth/signup", { method: "POST", body, auth: false }),
  login: (body: { identifier: string; password: string }) =>
    request<LoginResponse>("/auth/login", { method: "POST", body, auth: false }),
  me: () => request<Customer>("/auth/me"),
  logout: () => request<void>("/auth/logout", { method: "POST" }),

  // Resources
  listResources: () => request<Facility[]>("/resources"),
  getResource: (id: string) => request<Facility>(`/resources/${id}`),
  checkAvailability: (id: string, q: { date: string; start_time: string; end_time: string }) =>
    request<AvailabilityResponse>(`/resources/${id}/availability`, { query: q }),

  // Pricing
  quote: (body: QuoteRequest) => request<PriceBreakdown>("/pricing/quote", { method: "POST", body }),

  // Bookings
  createBooking: (body: BookingRequest) => request<Booking>("/bookings", { method: "POST", body }),
  listBookings: (status?: BookingStatus | "upcoming" | "past" | "cancelled") =>
    request<Booking[]>("/bookings", { query: { status } }),
  getBooking: (id: string) => request<Booking>(`/bookings/${id}`),
  addEquipmentToBooking: (id: string, body: { equipment_id: string; quantity: number }) =>
    request<Booking>(`/bookings/${id}/equipment`, { method: "POST", body }),
  cancelPreview: (id: string) => request<CancelPreview>(`/bookings/${id}/cancel-preview`, { method: "POST" }),
  cancelBooking: (id: string) => request<Booking>(`/bookings/${id}/cancel`, { method: "POST" }),
  reschedulePreview: (id: string, body: ReschedulePreviewRequest) =>
    request<ReschedulePreview>(`/bookings/${id}/reschedule-preview`, { method: "POST", body }),
  rescheduleBooking: (id: string, body: ReschedulePreviewRequest) =>
    request<Booking>(`/bookings/${id}/reschedule`, { method: "POST", body }),

  // Membership
  getMembership: () => request<Membership | null>("/membership"),
  getMembershipPlans: () => request<MembershipPlan[]>("/membership/plans"),
  subscribeMembership: (plan_type: "monthly" | "annual") =>
    request<Membership>("/membership/subscribe", { method: "POST", body: { plan_type } }),

  // Equipment
  listEquipment: () => request<Equipment[]>("/equipment"),
  equipmentAvailability: (q: { equipment_id: string; quantity: number }) =>
    request<{ available: boolean }>("/equipment/availability", { query: q }),

  // Assistant
  chat: (body: { message: string; conversation_id?: string }) =>
    request<AssistantResponse>("/assistant/chat", { method: "POST", body }),
}
