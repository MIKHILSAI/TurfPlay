import type { AlternativeSlot, ApiErrorBody } from "./types"

// Human-friendly copy for known backend error codes. Anything unrecognized
// falls back to the raw `message` from the response, never a stack trace.
const ERROR_COPY: Record<string, string> = {
  AUTHENTICATION_FAILED: "Your email/phone or password is incorrect. Please try again.",
  RESOURCE_NOT_FOUND: "We couldn't find that facility.",
  RESOURCE_INACTIVE: "That facility is currently unavailable for booking.",
  OUTSIDE_OPENING_HOURS: "That time is outside the facility's opening hours.",
  FACILITY_CLOSED: "The facility is closed at the selected time.",
  SLOT_UNAVAILABLE: "That slot is already booked. See suggested alternatives below.",
  INVALID_DURATION: "The selected duration isn't valid for this facility.",
  ADVANCE_BOOKING_LIMIT_EXCEEDED: "This date is outside your advance booking limit.",
  BOOKING_NOT_FOUND: "We couldn't find that booking.",
  BOOKING_NOT_OWNED: "You don't have access to that booking.",
  ALREADY_CANCELLED: "This booking has already been cancelled.",
  CANCELLATION_NOT_ELIGIBLE: "This booking is no longer eligible for cancellation.",
  RESCHEDULE_LIMIT_REACHED: "This booking has reached its reschedule limit.",
  RESCHEDULE_NOT_ELIGIBLE: "This booking isn't eligible to be rescheduled.",
  EQUIPMENT_UNAVAILABLE: "The requested equipment isn't available in that quantity.",
  INVALID_MEMBERSHIP: "Your membership isn't valid for this action.",
  MEMBERSHIP_ALREADY_ACTIVE: "You already have an active membership.",
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly alternatives?: AlternativeSlot[]

  constructor(status: number, body: Partial<ApiErrorBody> | null, fallback: string) {
    const code = body?.error_code ?? "UNKNOWN"
    const friendly = ERROR_COPY[code] ?? body?.message ?? fallback
    super(friendly)
    this.name = "ApiError"
    this.status = status
    this.code = code
    this.alternatives = body?.alternatives
  }
}

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError
}

export function errorMessage(err: unknown): string {
  if (isApiError(err)) return err.message
  if (err instanceof Error) return err.message
  return "Something went wrong. Please try again."
}
