"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import { toast } from "sonner"
import { ArrowUpIcon, CheckCircle2Icon, MessageSquareTextIcon, SendIcon, SparklesIcon } from "lucide-react"
import { useAuth } from "@/components/auth-provider"
import { PageHeader, ErrorState } from "@/components/state-views"
import { CancelDialog } from "@/components/cancel-dialog"
import { RescheduleDialog } from "@/components/reschedule-dialog"
import { PriceBreakdownView } from "@/components/price-breakdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { MessageScroller, MessageScrollerContent, MessageScrollerItem, MessageScrollerViewport } from "@/components/ui/message-scroller"
import { api } from "@/lib/api"
import { errorMessage } from "@/lib/errors"
import { formatCurrency, formatDate, formatTimeRange } from "@/lib/format"
import { useAsync } from "@/lib/use-async"
import type { AssistantAction, AssistantResponse, Booking, BookingRequest, PriceBreakdown } from "@/lib/types"
import { useVoiceChat } from "@/lib/hooks/useVoiceChat"
import { VoiceButton } from "@/components/VoiceButton"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  text: string
  response?: AssistantResponse
  speakable?: boolean
}

const defaultMessage = "I want to book a badminton court tomorrow at 6pm."

export default function AssistantPage() {
  const { customer } = useAuth()
  const bookings = useAsync(() => api.listBookings("upcoming"), [])
  const [message, setMessage] = useState(defaultMessage)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeBooking, setActiveBooking] = useState<Booking | null>(null)
  const [dialog, setDialog] = useState<"cancel" | "reschedule" | null>(null)
  const [rescheduleTarget, setRescheduleTarget] = useState<{ date?: string; startTime?: string }>({})
  const submittingRef = useRef(false)
  const actionRunningRef = useRef(false)
  const spokenIdsRef = useRef<Set<string>>(new Set())  // ← tracks which messages have been spoken
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: `Hi ${customer?.name?.split(" ")[0] ?? "there"}! I can help you browse courts, check availability, and explain booking options without finalizing anything unless you ask me to.`,
    },
  ])

  const canSend = message.trim().length > 0 && !loading

  // ============================================================
  // VOICE CHAT
  // ============================================================

  const apiBase = process.env.NEXT_PUBLIC_API_URL!

  const {
    recording,
    transcribing,
    speaking,
    startRecording,
    stopRecording,
    speak,
  } = useVoiceChat(apiBase)

  // When STT returns text, submit it as a normal chat message
  const handleTranscribed = (text: string) => {
    setMessage(text)
    void submitMessage(text)
  }

  // Auto-speak only NEW assistant messages we haven't spoken yet.
  // Guards against:
  //   - React StrictMode double-firing the effect in dev
  //   - re-runs caused by `speak` reference changes
  //   - re-runs caused by user messages arriving
  useEffect(() => {
    const last = messages[messages.length - 1]
    if (!last) return
    if (last.role !== "assistant") return
    if (!last.speakable) return
    if (spokenIdsRef.current.has(last.id)) return

    spokenIdsRef.current.add(last.id) // mark BEFORE calling speak
    void speak(last.text)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages])

  // ============================================================
  // CHAT
  // ============================================================

  async function submitMessage(nextMessage?: string) {
    if (submittingRef.current) return
    const text = (nextMessage ?? message).trim()
    if (!text) return
    submittingRef.current = true

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", text }
    setMessages((prev) => [...prev, userMessage])
    setMessage("")
    setLoading(true)
    setError(null)

    try {
      const response: AssistantResponse = await api.chat({ message: text })
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: response.message,
        response,
        speakable: true,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const message = errorMessage(err)
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
      submittingRef.current = false
    }
  }

  async function loadBooking(bookingId: string) {
    const booking = await api.getBooking(bookingId)
    setActiveBooking(booking)
    return booking
  }

  async function runAction(action: AssistantAction) {
    if (actionRunningRef.current) return
    actionRunningRef.current = true
    const payload = action.payload ?? {}
    const actionName = action.action.toLowerCase()
    setError(null)

    try {
      if (actionName === "select_booking") {
        const request = bookingRequestFromPayload(payload)
        if (!request) throw new Error("This facility option is missing booking details.")
        const quote = await api.quote(request)
        appendAssistantResponse({
          type: "price_breakdown",
          message: "Here is the live price for that facility. Confirm when you are ready.",
          data: { price_breakdown: quote, booking_request: request },
          actions: [{ label: "Confirm booking", action: "confirm_booking", payload: request as unknown as Record<string, unknown> }],
        })
        return
      }

      if (actionName === "confirm_equipment") {
        const bookingId = stringValue(payload.booking_id)
        const equipmentId = stringValue(payload.equipment_id)
        const quantity = Number(payload.quantity)
        if (!bookingId || !equipmentId || !Number.isInteger(quantity) || quantity <= 0) {
          throw new Error("This equipment action is missing booking details.")
        }
        const booking = await api.addEquipmentToBooking(bookingId, {
          equipment_id: equipmentId,
          quantity,
        })
        toast.success("Equipment added to your booking.")
        bookings.reload()
        notifyBookingsChanged()
        appendAssistantResponse({
          type: "confirmation",
          message: `Equipment added to booking ${booking._id}. Updated total: ${formatCurrency(booking.price_breakdown?.total_amount)}.`,
          data: { booking },
        })
        return
      }

      if (actionName.includes("cancel")) {
        const bookingId = stringValue(payload.booking_id ?? payload.id)
        if (!bookingId) throw new Error("This cancellation action is missing a booking ID.")
        await loadBooking(bookingId)
        setDialog("cancel")
        return
      }

      if (actionName.includes("reschedule") || actionName.includes("move")) {
        const bookingId = stringValue(payload.booking_id ?? payload.id)
        if (!bookingId) throw new Error("This reschedule action is missing a booking ID.")
        await loadBooking(bookingId)
        setRescheduleTarget({
          date: stringValue(payload.date) ?? undefined,
          startTime: stringValue(payload.start_time) ?? undefined,
        })
        setDialog("reschedule")
        return
      }

      if (actionName === "confirm_booking" || actionName === "create_booking" || actionName === "book") {
        const request = bookingRequestFromPayload(payload)
        if (!request) throw new Error("This booking action is missing the facility, date, or time.")
        const booking = await api.createBooking(request)
        toast.success("Booking confirmed.")
        bookings.reload()
        notifyBookingsChanged()
        appendAssistantResponse({
          type: "confirmation",
          message: `Booking ${booking._id} is confirmed.`,
          data: { booking },
        })
        return
      }

      if (actionName === "view_bookings" || actionName === "list_bookings") {
        bookings.reload()
        toast.success("Bookings refreshed.")
        return
      }

      if (actionName === "view_equipment") {
        const equipment = await api.listEquipment()
        appendAssistantResponse({
          type: "text",
          message: equipment.length > 0
            ? equipment.map((item) => `${item.name}: ${item.quantity_available} available`).join("\n")
            : "No equipment is currently available.",
        })
        return
      }

      throw new Error("This assistant action is not available yet.")
    } catch (err) {
      const message = errorMessage(err)
      setError(message)
      toast.error(message)
    } finally {
      actionRunningRef.current = false
    }
  }

  function appendAssistantResponse(response: AssistantResponse) {
    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      text: response.message,
      response,
      speakable: true,
    }
    setMessages((prev) => [...prev, assistantMessage])
  }

  function handleDialogChange(open: boolean) {
    if (!open) {
      setDialog(null)
      setActiveBooking(null)
      setRescheduleTarget({})
    }
  }

  const summaryText = useMemo(() => {
    if (messages.length === 0) return "No messages yet"
    return `${messages.length} messages`
  }, [messages])

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="AI assistant"
        description="Ask for availability, booking ideas, or quick guidance without making a reservation directly."
      />

      <Card className="flex min-h-[70vh] flex-col overflow-hidden">
        <div className="border-b p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <SparklesIcon className="size-4 text-primary" />
            <span>{summaryText}</span>
            {speaking ? <span className="text-xs text-primary">· speaking…</span> : null}
          </div>
        </div>

        <div className="flex-1">
          <MessageScroller>
            <MessageScrollerViewport>
              <MessageScrollerContent className="p-4">
                {messages.map((msg) => (
                  <MessageScrollerItem key={msg.id} className={msg.role === "assistant" ? "max-w-[85%]" : "ml-auto max-w-[85%]"}>
                    <div className={msg.role === "assistant" ? "rounded-2xl rounded-tl-md bg-muted px-4 py-3 text-sm text-foreground" : "rounded-2xl rounded-tr-md bg-primary px-4 py-3 text-sm text-primary-foreground"}>
                      <div className="leading-6">
                        {msg.text.split(/\r?\n/).map((line, index) => (
                          <div key={`${msg.id}-line-${index}`} className={line.trim() ? "min-h-6" : "h-2"}>
                            {line || " "}
                          </div>
                        ))}
                      </div>
                      {msg.role === "assistant" && msg.response ? <AssistantResponseView response={msg.response} onAction={runAction} /> : null}
                    </div>
                  </MessageScrollerItem>
                ))}
              </MessageScrollerContent>
            </MessageScrollerViewport>
          </MessageScroller>
        </div>

        {error ? (
          <div className="border-t p-4">
            <ErrorState message={error} onRetry={() => setError(null)} />
          </div>
        ) : null}

        <CardContent className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  e.stopPropagation()
                  if (canSend) void submitMessage()
                }
              }}
              placeholder={
                recording
                  ? "Recording… tap mic again to stop"
                  : transcribing
                  ? "Transcribing…"
                  : loading
                  ? "Waiting for assistant response…"
                  : "Ask about a sport, date, or booking option…"
              }
              aria-label="Type a message"
            />

            <VoiceButton
              recording={recording}
              transcribing={transcribing}
              onStart={() => startRecording(handleTranscribed)}
              onStop={stopRecording}
            />

            <Button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (canSend) void submitMessage()
              }}
              disabled={!canSend}
            >
              {loading ? <span className="inline-flex items-center gap-2"><MessageSquareTextIcon className="size-4" /> Sending…</span> : <><SendIcon data-icon="inline-start" /> Send</>}
            </Button>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>Safe mode: the assistant only suggests actions; it never books or cancels on its own.</span>
            <Button variant="ghost" size="icon-sm" onClick={() => setMessage(defaultMessage)} aria-label="Use sample prompt">
              <ArrowUpIcon className="size-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {activeBooking && dialog === "cancel" ? (
        <CancelDialog
          booking={activeBooking}
          open
          onOpenChange={handleDialogChange}
          onCancelled={() => {
            bookings.reload()
            notifyBookingsChanged()
            setDialog(null)
            setActiveBooking(null)
            setRescheduleTarget({})
          }}
        />
      ) : null}
      {activeBooking && dialog === "reschedule" ? (
        <RescheduleDialog
          booking={activeBooking}
          open
          initialDate={rescheduleTarget.date}
          initialStartTime={rescheduleTarget.startTime}
          onOpenChange={handleDialogChange}
          onRescheduled={() => {
            bookings.reload()
            notifyBookingsChanged()
            setDialog(null)
            setActiveBooking(null)
            setRescheduleTarget({})
          }}
        />
      ) : null}
    </div>
  )
}

function AssistantResponseView({ response, onAction }: { response: AssistantResponse; onAction: (action: AssistantAction) => void }) {
  const data = response.data ?? {}

  switch (response.type) {
    case "availability": {
      const resources = Array.isArray(data.available_resources) ? data.available_resources : []
      return resources.length > 0 ? (
        <div className="mt-3 flex flex-col gap-2">
          {resources.map((resource, index) => {
            const action = response.actions?.[index]
            return (
              <div key={index} className="flex items-center justify-between gap-3 rounded-lg border bg-background/70 p-3 text-xs">
                <div className="flex flex-col gap-1">
                  <span className="font-medium">{formatResource(resource)}</span>
                  <span className="text-muted-foreground">{formatResourcePrice(resource)}</span>
                </div>
                {action ? <Button size="sm" variant="outline" onClick={() => onAction(action)}>{action.label}</Button> : null}
              </div>
            )
          })}
        </div>
      ) : null
    }
    case "booking_summary": {
      const summary = data.summary as Record<string, unknown> | undefined
      const pricing = summary?.pricing
      return summary ? (
        <div className="mt-3 flex flex-col gap-3 rounded-lg bg-background/70 p-3 text-xs">
          <div>{formatBookingSummary((summary.booking ?? {}) as Record<string, unknown>)}</div>
          {isPriceBreakdown(pricing) ? <PriceBreakdownView breakdown={pricing} /> : null}
          <ResponseActions actions={response.actions} onAction={onAction} />
        </div>
      ) : null
    }
    case "price_breakdown": {
      const breakdown = data.price_breakdown ?? data
      return isPriceBreakdown(breakdown) ? (
        <div className="mt-3 rounded-lg bg-background/70 p-3">
          <PriceBreakdownView breakdown={breakdown} />
          <ResponseActions actions={response.actions} onAction={onAction} />
        </div>
      ) : null
    }
    case "confirmation":
    case "cancellation_confirmation":
    case "reschedule_form":
    case "action_buttons":
      return <ResponseActions actions={response.actions} onAction={onAction} />
    case "text":
      return null
    default:
      return null
  }
}

function ResponseActions({ actions, onAction }: { actions?: AssistantAction[]; onAction: (action: AssistantAction) => void }) {
  if (!actions?.length) return null
  return <div className="mt-3 flex flex-wrap gap-2">{actions.map((action, index) => <Button key={`${action.action}-${index}`} size="sm" variant="outline" onClick={() => onAction(action)}><CheckCircle2Icon data-icon="inline-start" />{action.label}</Button>)}</div>
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null
}

function notifyBookingsChanged() {
  if (typeof window !== "undefined") window.dispatchEvent(new Event("turf:bookings-changed"))
}

function bookingRequestFromPayload(payload: Record<string, unknown>): BookingRequest | null {
  const resourceId = stringValue(payload.resource_id)
  const date = stringValue(payload.date ?? payload.booking_date)
  const startTime = stringValue(payload.start_time)
  const endTime = stringValue(payload.end_time)
  if (!resourceId || !date || !startTime || !endTime) return null
  return {
    resource_id: resourceId,
    date,
    start_time: startTime,
    end_time: endTime,
    equipment: Array.isArray(payload.equipment) ? payload.equipment as BookingRequest["equipment"] : [],
    apply_membership: payload.apply_membership === true,
  }
}

function isPriceBreakdown(value: unknown): value is PriceBreakdown {
  return typeof value === "object" && value !== null && typeof (value as PriceBreakdown).total_amount === "number"
}

function formatResource(value: unknown): string {
  if (typeof value !== "object" || value === null) return String(value)
  const resource = value as Record<string, unknown>
  return `${resource.name ?? resource.resource_id ?? "Facility"}${resource.start_time ? ` · ${resource.start_time}${resource.end_time ? `–${resource.end_time}` : ""}` : ""}`
}

function formatResourcePrice(value: unknown): string {
  if (typeof value !== "object" || value === null) return ""
  const resource = value as Record<string, unknown>
  const booking = resource.booking as Record<string, unknown> | undefined
  const amount = booking?.total_amount ?? resource.hourly_rate
  return typeof amount === "number" ? `Estimated facility amount: ${formatCurrency(amount)}` : "Live price available after selection"
}

function formatBookingSummary(booking: Record<string, unknown>): string {
  const date = typeof booking.booking_date === "string" ? formatDate(booking.booking_date) : "Selected booking"
  const start = stringValue(booking.start_time)
  const end = stringValue(booking.end_time)
  return `${date}${start && end ? ` · ${formatTimeRange(start, end)}` : ""}${typeof booking.total_amount === "number" ? ` · ${formatCurrency(booking.total_amount)}` : ""}`
}