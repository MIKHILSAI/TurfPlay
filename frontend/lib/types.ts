// Domain types mirroring the FastAPI backend contract.

export type FacilityType = "badminton" | "football" | "tennis" | "multipurpose" | "multipurpose room"

export interface Facility {
  _id: string
  name: string
  type: FacilityType
  capacity: number
  hourly_rate: number
  open_time: string
  close_time: string
  active: boolean
}

export interface Customer {
  _id: string
  name: string
  email: string
  phone: string
  created_at?: string
  max_advance_booking_days: number
}

export interface LoginResponse {
  token: string
  customer: Customer
}

export interface EquipmentSelection {
  equipment_id: string
  quantity: number
}

export interface Equipment {
  _id: string
  name: string
  type: string
  price: number
  deposit: number
  quantity_available: number
  active: boolean
}

export interface PriceBreakdown {
  base_amount: number
  peak_surcharge?: number
  weekend_surcharge?: number
  membership_discount?: number
  discount_amount?: number
  equipment_amount: number
  deposit_amount: number
  total_amount: number
}

export type BookingStatus = "confirmed" | "cancelled" | "completed" | "rescheduled" | "pending"

export type PaymentStatus = "paid" | "unpaid" | "refunded" | "pending"

export interface Booking {
  _id: string
  customer_id: string
  resource_id: string
  booking_date: string
  start_time: string
  end_time: string
  blocked_end_time?: string
  duration_mins: number
  status: BookingStatus
  payment_status: PaymentStatus
  price_breakdown: PriceBreakdown
  reschedule_count: number
  created_at: string
  // The backend may denormalize the facility onto the booking; keep it optional.
  resource?: Facility
  equipment?: Array<Record<string, unknown>>
}

export interface AvailabilityResponse {
  available: boolean
  message?: string
  alternatives?: AlternativeSlot[]
}

export interface AlternativeSlot {
  resource_id: string
  start_time: string
  end_time: string
}

export interface QuoteRequest {
  resource_id: string
  date: string
  start_time: string
  end_time: string
  equipment: EquipmentSelection[]
  apply_membership: boolean
}

export type BookingRequest = QuoteRequest

export interface CancelPreview {
  eligible: boolean
  refund_amount: number
  message: string
}

export interface ReschedulePreviewRequest {
  new_resource_id: string
  new_date: string
  new_start_time: string
  new_end_time: string
}

export interface ReschedulePreview {
  eligible: boolean
  slot_available: boolean
  remaining_reschedule_count: number
  price_difference: number
  message?: string
}

export interface Membership {
  type: string
  status: "active" | "inactive"
  start_date?: string
  expiry_date?: string
  discount_percent?: number
  priority_access?: boolean
}

export interface MembershipPlan {
  _id: string
  name: string
  price: number
  duration: string
  discount_percent?: number
}

export type AssistantResponseType =
  | "text"
  | "availability"
  | "booking_summary"
  | "confirmation"
  | "cancellation_confirmation"
  | "reschedule_form"
  | "price_breakdown"
  | "action_buttons"

export interface AssistantAction {
  label: string
  action: string
  payload?: Record<string, unknown>
}

export interface AssistantResponse {
  type: AssistantResponseType
  message: string
  data?: Record<string, unknown>
  actions?: AssistantAction[]
  conversation_id?: string
}

export interface ApiErrorBody {
  error_code: string
  message: string
  alternatives?: AlternativeSlot[]
}
