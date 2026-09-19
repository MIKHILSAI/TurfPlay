// Time helpers for slot selection. Times are "HH:MM" 24-hour strings.

function normalizeHHMM(value: string | number | null | undefined): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return toHHMM(value)
  }

  const text = typeof value === "string" ? value.trim() : ""
  if (!text || !text.includes(":")) return "00:00"
  return text
}

export function toMinutes(hhmm: string | number | null | undefined): number {
  const value = normalizeHHMM(hhmm)
  const [h, m] = value.split(":").map(Number)
  return (Number.isFinite(h) ? h : 0) * 60 + (Number.isFinite(m) ? m : 0)
}

export function toHHMM(mins: number): string {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`
}

// Generates start-time options in `step` minute increments between open and
// close, ensuring a full `duration` fits before close.
export function startTimeOptions(open: string, close: string, duration: number, step = 30): string[] {
  const start = toMinutes(open)
  const end = toMinutes(close)
  const options: string[] = []
  for (let t = start; t + duration <= end; t += step) {
    options.push(toHHMM(t))
  }
  return options
}

export function addMinutes(hhmm: string, mins: number): string {
  return toHHMM(toMinutes(hhmm) + mins)
}

export function formatClock(hhmm: string | number | null | undefined): string {
  const value = normalizeHHMM(hhmm)
  const [h, m] = value.split(":").map(Number)
  const safeHour = Number.isFinite(h) ? h : 0
  const safeMinute = Number.isFinite(m) ? m : 0
  const period = safeHour >= 12 ? "PM" : "AM"
  const hour12 = safeHour % 12 === 0 ? 12 : safeHour % 12
  return `${hour12}:${String(safeMinute).padStart(2, "0")} ${period}`
}

export function todayISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
}

export function addDaysISO(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T00:00:00`)
  date.setDate(date.getDate() + days)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
}
