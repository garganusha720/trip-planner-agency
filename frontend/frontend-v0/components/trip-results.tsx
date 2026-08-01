"use client"

import {
  BedDouble,
  Lightbulb,
  MapPin,
  Plane,
  Wallet,
  CalendarDays,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  flightClassLabel,
  formatMoney,
  type TripPlan,
} from "@/lib/trip-planner"

const CATEGORY_COLORS: Record<string, string> = {
  Food: "bg-chart-5/15 text-chart-5",
  Culture: "bg-chart-4/15 text-chart-4",
  Nature: "bg-chart-3/15 text-chart-3",
  Adventure: "bg-accent/25 text-accent-foreground",
  Nightlife: "bg-chart-4/15 text-chart-4",
  Shopping: "bg-chart-5/15 text-chart-5",
  Relax: "bg-chart-3/15 text-chart-3",
  Wellness: "bg-chart-3/15 text-chart-3",
  Interest: "bg-primary/15 text-primary",
}

export function TripResults({ plan }: { plan: TripPlan }) {
  const { input, budget, itinerary, tips } = plan
  const over = budget.remaining < 0

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-primary">Your trip plan</p>
          <h2 className="text-pretty text-2xl font-bold sm:text-3xl">
            {input.origin.toUpperCase()} → {input.destination}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {input.days} days · {flightClassLabel(input.flightClass)} ·{" "}
            {input.hotelRating === "any"
              ? "Any hotel rating"
              : `${input.hotelRating}★+ hotels`}
          </p>
        </div>
      </header>

      {/* Budget summary */}
      <section aria-labelledby="budget-heading">
        <div className="mb-3 flex items-center gap-2">
          <Wallet className="size-5 text-primary" />
          <h3 id="budget-heading" className="text-lg font-semibold">
            Budget summary
          </h3>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <BudgetCard
            icon={<Plane className="size-4" />}
            label="Round-trip flights"
            value={formatMoney(budget.flight, input.currency)}
            sub={flightClassLabel(input.flightClass)}
          />
          <BudgetCard
            icon={<BedDouble className="size-4" />}
            label="Hotel (total)"
            value={formatMoney(budget.hotel, input.currency)}
            sub={`${formatMoney(budget.hotelPerNight, input.currency)} / night`}
          />
          <BudgetCard
            icon={<CalendarDays className="size-4" />}
            label="Daily budget"
            value={formatMoney(budget.dailyBudget, input.currency)}
            sub="Food, activities & transit"
          />
        </div>

        <Card className="mt-4">
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
            <div>
              <p className="text-sm text-muted-foreground">Total budget</p>
              <p className="text-xl font-bold">
                {formatMoney(input.budget, input.currency)}
              </p>
            </div>
            <div className="h-10 w-px bg-border" aria-hidden />
            <div>
              <p className="text-sm text-muted-foreground">
                Activities & spending
              </p>
              <p className="text-xl font-bold">
                {formatMoney(Math.max(0, budget.activitiesTotal), input.currency)}
              </p>
            </div>
            <div className="h-10 w-px bg-border" aria-hidden />
            <div>
              <p className="text-sm text-muted-foreground">
                {over ? "Over budget by" : "Buffer remaining"}
              </p>
              <p
                className={`text-xl font-bold ${
                  over ? "text-destructive" : "text-chart-3"
                }`}
              >
                {formatMoney(Math.abs(budget.remaining), input.currency)}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Itinerary */}
      <section aria-labelledby="itinerary-heading">
        <div className="mb-3 flex items-center gap-2">
          <MapPin className="size-5 text-primary" />
          <h3 id="itinerary-heading" className="text-lg font-semibold">
            Day-by-day itinerary
          </h3>
        </div>
        <div className="space-y-4">
          {itinerary.map((day) => (
            <Card key={day.day} className="overflow-hidden">
              <CardHeader className="flex flex-row items-center gap-3 border-b bg-muted/40 py-3">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                  {day.day}
                </div>
                <div>
                  <CardTitle className="text-base">{day.title}</CardTitle>
                  <p className="text-xs text-muted-foreground">{day.date}</p>
                </div>
              </CardHeader>
              <CardContent className="py-2">
                <ul className="divide-y">
                  {day.activities.map((act, i) => (
                    <li key={i} className="flex items-center gap-4 py-3">
                      <span className="w-14 shrink-0 font-mono text-sm tabular-nums text-muted-foreground">
                        {act.time}
                      </span>
                      <span className="flex-1 text-sm font-medium">
                        {act.name}
                      </span>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          CATEGORY_COLORS[act.category] ??
                          "bg-secondary text-secondary-foreground"
                        }`}
                      >
                        {act.category}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Tips */}
      <section aria-labelledby="tips-heading">
        <div className="mb-3 flex items-center gap-2">
          <Lightbulb className="size-5 text-primary" />
          <h3 id="tips-heading" className="text-lg font-semibold">
            Local tips
          </h3>
        </div>
        <Card>
          <CardContent className="py-4">
            <ul className="space-y-3">
              {tips.map((tip, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-accent/30 text-xs font-bold text-accent-foreground">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed text-foreground/90">
                    {tip}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

function BudgetCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="mb-2 flex items-center gap-2 text-muted-foreground">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </span>
          <span className="text-sm">{label}</span>
        </div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
      </CardContent>
    </Card>
  )
}
