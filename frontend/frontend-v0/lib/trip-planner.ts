export type Currency = "USD" | "INR" | "EUR" | "GBP"
export type FlightClass = "economy" | "premium_economy" | "business" | "first"
export type HotelRating = "any" | "3" | "3.5" | "4" | "4.5"

export interface TripInput {
  origin: string
  destination: string
  startDate: string
  days: number
  currency: Currency
  budget: number
  flightClass: FlightClass
  hotelRating: HotelRating
  interests: string
}

export interface BudgetSummary {
  flight: number
  hotel: number
  hotelPerNight: number
  dailyBudget: number
  activitiesTotal: number
  total: number
  remaining: number
}

export interface ItineraryActivity {
  time: string
  name: string
  category: string
}

export interface ItineraryDay {
  day: number
  date: string
  title: string
  activities: ItineraryActivity[]
}

export interface TripPlan {
  input: TripInput
  budget: BudgetSummary
  itinerary: ItineraryDay[]
  tips: string[]
}

export const CURRENCY_SYMBOLS: Record<Currency, string> = {
  USD: "$",
  INR: "₹",
  EUR: "€",
  GBP: "£",
}

const FLIGHT_CLASS_LABEL: Record<FlightClass, string> = {
  economy: "Economy",
  premium_economy: "Premium Economy",
  business: "Business",
  first: "First",
}

export function flightClassLabel(fc: FlightClass) {
  return FLIGHT_CLASS_LABEL[fc]
}

export function formatMoney(amount: number, currency: Currency) {
  const symbol = CURRENCY_SYMBOLS[currency]
  return `${symbol}${Math.round(amount).toLocaleString()}`
}

function formatDate(base: Date, offsetDays: number) {
  const d = new Date(base)
  d.setDate(d.getDate() + offsetDays)
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  })
}

// ---------------------------------------------------------------------------
// Backend response shapes — minimal typing for the fields we actually read.
// Source of truth is the FastAPI backend's Pydantic schemas
// (backend/app/schemas/state.py) — keep in sync if that changes.
// ---------------------------------------------------------------------------

interface BackendFlight {
  airline: string
  price: number
  cabin_class: string
  stops: number
}

interface BackendHotel {
  name: string
  price_per_night: number
  rating: number
}

interface BackendBudget {
  currency: string
  chosen_flight: BackendFlight
  chosen_hotel: BackendHotel
  flight_cost_total: number
  hotel_cost_total: number
  remaining_daily_budget: number
  feasible: boolean
  feasibility_note: string | null
}

interface BackendActivity {
  name: string
  start_time: string
  end_time: string
  neighborhood: string
  category: string
  est_cost: number
}

interface BackendItineraryDay {
  day_number: number
  activities: BackendActivity[]
}

interface BackendResponse {
  budget: BackendBudget
  itinerary: { destination: string; days: BackendItineraryDay[] }
  research: { best_time_to_visit: string | null; local_tips: string[] }
  validation: { status: string; conflicts: { detail: string }[] }
  retry_count: number
}

// Set NEXT_PUBLIC_BACKEND_URL in .env.local, or this default is used.
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001"

function hotelRatingToNumber(r: HotelRating): number {
  return r === "any" ? 0 : Number(r)
}

export async function planTrip(input: TripInput): Promise<TripPlan> {
  const response = await fetch(`${BACKEND_URL}/plan-trip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin: input.origin,
      destination: input.destination,
      start_date: input.startDate,
      trip_length_days: input.days,
      total_budget: input.budget,
      currency: input.currency,
      interests: input.interests.split(",").map((s) => s.trim()).filter(Boolean),
      cabin_class: input.flightClass,
      hotel_min_rating: hotelRatingToNumber(input.hotelRating),
    }),
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new Error(detail)
  }

  const result: BackendResponse = await response.json()

  // --- Budget ---
  const activitiesTotal = result.itinerary.days.reduce(
    (sum, day) => sum + day.activities.reduce((daySum, a) => daySum + a.est_cost, 0),
    0,
  )
  const flight = result.budget.flight_cost_total
  const hotel = result.budget.hotel_cost_total
  const total = flight + hotel + activitiesTotal

  const budget: BudgetSummary = {
    flight,
    hotel,
    hotelPerNight: result.budget.chosen_hotel.price_per_night,
    dailyBudget: result.budget.remaining_daily_budget,
    activitiesTotal,
    total,
    remaining: input.budget - total,
  }

  // --- Itinerary ---
  const base = input.startDate ? new Date(input.startDate + "T00:00:00") : new Date()
  const lastIndex = result.itinerary.days.length - 1

  const itinerary: ItineraryDay[] = result.itinerary.days.map((day, i) => ({
    day: day.day_number,
    date: formatDate(base, i),
    title:
      i === 0
        ? "Arrival & first impressions"
        : i === lastIndex
          ? "Farewell & departure"
          : `Exploring ${result.itinerary.destination}`,
    activities: day.activities.map((a) => ({
      time: a.start_time,
      name: a.name,
      category: a.category.charAt(0).toUpperCase() + a.category.slice(1),
    })),
  }))

  // --- Tips (plus any warnings worth surfacing) ---
  const tips: string[] = []

  if (!result.budget.feasible && result.budget.feasibility_note) {
    tips.push(`⚠️ Over budget: ${result.budget.feasibility_note}`)
  } else if (result.budget.feasibility_note) {
    tips.push(`ℹ️ ${result.budget.feasibility_note}`)
  }

  if (result.validation.status === "conflict") {
    tips.push(
      `⚠️ This itinerary still has ${result.validation.conflicts.length} unresolved scheduling conflict(s) after ${result.retry_count} retries.`,
    )
  }

  if (result.research.best_time_to_visit) {
    tips.push(`Best time to visit: ${result.research.best_time_to_visit}`)
  }

  tips.push(...result.research.local_tips)

  return { input, budget, itinerary, tips }
}
