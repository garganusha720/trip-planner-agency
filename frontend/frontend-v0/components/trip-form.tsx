"use client"

import type React from "react"
import { useState } from "react"
import { Plane, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { LocationAutocomplete } from "@/components/location-autocomplete"
import type {
  Currency,
  FlightClass,
  HotelRating,
  TripInput,
} from "@/lib/trip-planner"

interface TripFormProps {
  onSubmit: (input: TripInput) => void
  loading: boolean
}

export function TripForm({ onSubmit, loading }: TripFormProps) {
  const [origin, setOrigin] = useState("San Francisco, CA, USA")
  const [destination, setDestination] = useState("Tokyo, Japan")
  const [startDate, setStartDate] = useState("")
  const [days, setDays] = useState("5")
  const [currency, setCurrency] = useState<Currency>("USD")
  const [budget, setBudget] = useState("3000")
  const [flightClass, setFlightClass] = useState<FlightClass>("economy")
  const [hotelRating, setHotelRating] = useState<HotelRating>("4")
  const [interests, setInterests] = useState("food, museums, hiking, nightlife")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      startDate,
      days: Math.max(1, Math.min(30, Number(days) || 1)),
      currency,
      budget: Math.max(0, Number(budget) || 0),
      flightClass,
      hotelRating,
      interests,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Origin" htmlFor="origin">
          <LocationAutocomplete
            id="origin"
            value={origin}
            onChange={setOrigin}
            placeholder="Start typing a city..."
            required
          />
        </Field>

        <Field label="Destination" htmlFor="destination">
          <LocationAutocomplete
            id="destination"
            value={destination}
            onChange={setDestination}
            placeholder="Start typing a city..."
            required
          />
        </Field>

        <Field label="Start date" htmlFor="startDate">
          <Input
            id="startDate"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </Field>

        <Field label="Trip length (days)" htmlFor="days">
          <Input
            id="days"
            type="number"
            min={1}
            max={30}
            value={days}
            onChange={(e) => setDays(e.target.value)}
            required
          />
        </Field>

        <Field label="Currency" htmlFor="currency">
          <Select value={currency} onValueChange={(v) => setCurrency(v as Currency)}>
            <SelectTrigger id="currency" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="USD">USD — US Dollar</SelectItem>
              <SelectItem value="INR">INR — Indian Rupee</SelectItem>
              <SelectItem value="EUR">EUR — Euro</SelectItem>
              <SelectItem value="GBP">GBP — British Pound</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field label="Total budget" htmlFor="budget">
          <Input
            id="budget"
            type="number"
            min={0}
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            placeholder="3000"
            required
          />
        </Field>

        <Field label="Flight class" htmlFor="flightClass">
          <Select
            value={flightClass}
            onValueChange={(v) => setFlightClass(v as FlightClass)}
          >
            <SelectTrigger id="flightClass" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="economy">Economy</SelectItem>
              <SelectItem value="premium_economy">Premium Economy</SelectItem>
              <SelectItem value="business">Business</SelectItem>
              <SelectItem value="first">First</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field label="Minimum hotel rating" htmlFor="hotelRating">
          <Select
            value={hotelRating}
            onValueChange={(v) => setHotelRating(v as HotelRating)}
          >
            <SelectTrigger id="hotelRating" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Any</SelectItem>
              <SelectItem value="3">3.0★ and up</SelectItem>
              <SelectItem value="3.5">3.5★ and up</SelectItem>
              <SelectItem value="4">4.0★ and up</SelectItem>
              <SelectItem value="4.5">4.5★ and up</SelectItem>
            </SelectContent>
          </Select>
        </Field>
      </div>

      <Field label="Interests" htmlFor="interests">
        <Input
          id="interests"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          placeholder="food, museums, hiking, nightlife"
        />
        <p className="mt-1.5 text-xs text-muted-foreground">
          Separate with commas — we&apos;ll weave these into your days.
        </p>
      </Field>

      <Button type="submit" size="lg" disabled={loading} className="w-full gap-2">
        {loading ? (
          <>
            <Plane className="size-4 animate-pulse" />
            Planning your trip…
          </>
        ) : (
          <>
            <Search className="size-4" />
            Plan my trip
          </>
        )}
      </Button>
    </form>
  )
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  )
}
