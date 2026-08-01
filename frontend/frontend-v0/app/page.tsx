"use client"

import { useState } from "react"
import {
  Compass,
  Globe,
  Sparkles,
  Wallet,
  Briefcase,
  ShieldCheck,
  Star,
  Lock,
  RefreshCw,
  Headphones,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TripForm } from "@/components/trip-form"
import { TripResults } from "@/components/trip-results"
import { TripLoading } from "@/components/trip-loading"
import { planTrip, type TripInput, type TripPlan } from "@/lib/trip-planner"

export default function Page() {
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<TripPlan | null>(null)
  const [pendingDestination, setPendingDestination] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(input: TripInput) {
    setLoading(true)
    setPlan(null)
    setError(null)
    setPendingDestination(input.destination)
    window.scrollTo({ top: 0, behavior: "smooth" })

    try {
      const result = await planTrip(input)
      setPlan(result)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while planning your trip. Make sure the backend is running.",
      )
    } finally {
      setLoading(false)
    }
  }

  if (loading || plan || error) {
    return (
      <main className="mx-auto min-h-screen w-full max-w-3xl px-4 py-10 sm:py-14">
        <Brand />
        <div className="mt-8">
          {loading && <TripLoading destination={pendingDestination} />}
          {!loading && error && (
            <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-6 text-sm text-destructive">
              <p className="font-semibold">Couldn&apos;t plan this trip</p>
              <p className="mt-1">{error}</p>
            </div>
          )}
          {!loading && !error && plan && <TripResults plan={plan} />}
        </div>
        {!loading && (plan || error) && (
          <div className="mt-8 flex justify-center">
            <Button
              variant="outline"
              onClick={() => {
                setPlan(null)
                setError(null)
                window.scrollTo({ top: 0, behavior: "smooth" })
              }}
            >
              Plan another trip
            </Button>
          </div>
        )}
      </main>
    )
  }

  return (
    <main className="relative min-h-screen w-full overflow-hidden">
      {/* Background */}
      <div
        className="pointer-events-none absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url(/hero-travel.png)" }}
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background/90 via-background/60 to-background/20"
        aria-hidden="true"
      />

      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-8 sm:px-6 lg:px-10">
        <Brand />

        <div className="mt-8 grid flex-1 items-center gap-8 lg:mt-6 lg:grid-cols-2 lg:gap-12">
          {/* Left column */}
          <div className="max-w-xl">
            <h2 className="text-pretty text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              Your journey,{" "}
              <span className="text-primary">perfectly planned</span>
            </h2>
            <p className="mt-4 max-w-md text-lg leading-relaxed text-muted-foreground">
              Let Trip Planner craft the perfect itinerary that fits your budget
              and matches your travel style.
            </p>

            <div className="mt-8 grid max-w-md gap-3">
              <Feature
                icon={<Wallet className="size-5" />}
                title="Budget Smart"
                desc="Get the best experiences within your budget"
              />
              <Feature
                icon={<Briefcase className="size-5" />}
                title="Personalized"
                desc="Tailored recommendations just for you"
              />
              <Feature
                icon={<ShieldCheck className="size-5" />}
                title="Hassle Free"
                desc="Save hours of planning and travel stress"
              />
            </div>

            <div className="mt-8 inline-flex items-center gap-3 rounded-2xl border border-border bg-card/80 px-4 py-3 backdrop-blur">
              <div className="flex -space-x-2">
                {["a", "b", "c", "d"].map((k, i) => (
                  <span
                    key={k}
                    className="flex size-8 items-center justify-center rounded-full border-2 border-card bg-secondary text-xs font-semibold text-secondary-foreground"
                  >
                    {String.fromCharCode(65 + i)}
                  </span>
                ))}
              </div>
              <div>
                <p className="text-sm font-medium text-primary">
                  Loved by 10,000+ travelers
                </p>
                <div className="flex items-center gap-1 text-sm">
                  <span className="flex text-accent">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className="size-3.5 fill-current" />
                    ))}
                  </span>
                  <span className="font-semibold">4.8/5</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right column: form card */}
          <Card className="border-border/60 bg-card/95 shadow-xl backdrop-blur">
            <CardContent className="p-6 sm:p-8">
              <div className="mb-6 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <Globe className="size-6 text-primary" />
                  <h3 className="text-xl font-bold tracking-tight">
                    Plan your next trip
                  </h3>
                </div>
                <span className="hidden items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground sm:inline-flex">
                  <Sparkles className="size-3.5" />
                  Let&apos;s make it amazing
                </span>
              </div>
              <TripForm onSubmit={handleSubmit} loading={loading} />
            </CardContent>
          </Card>
        </div>

        {/* Footer trust badges */}
        <footer className="mt-10 grid gap-6 border-t border-border/60 pt-6 sm:grid-cols-3">
          <TrustBadge
            icon={<Lock className="size-5" />}
            title="Secure & Private"
            desc="Your data is 100% safe with us"
          />
          <TrustBadge
            icon={<RefreshCw className="size-5" />}
            title="Real-time Updates"
            desc="Prices & availability refreshed in real time"
          />
          <TrustBadge
            icon={<Headphones className="size-5" />}
            title="24/7 Support"
            desc="We're here to help anytime"
          />
        </footer>
      </div>
    </main>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <Compass className="size-6" />
      </span>
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trip Planner</h1>
        <p className="text-sm text-muted-foreground">
          Smart, budget-aware trip planning
        </p>
      </div>
    </div>
  )
}

function Feature({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode
  title: string
  desc: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-border/60 bg-card/80 p-4 backdrop-blur">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        {icon}
      </span>
      <div>
        <p className="font-semibold leading-tight">{title}</p>
        <p className="text-sm leading-relaxed text-muted-foreground">{desc}</p>
      </div>
    </div>
  )
}

function TrustBadge({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode
  title: string
  desc: string
}) {
  return (
    <div className="flex items-start gap-3">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-secondary text-primary">
        {icon}
      </span>
      <div>
        <p className="font-semibold leading-tight">{title}</p>
        <p className="text-sm leading-relaxed text-muted-foreground">{desc}</p>
      </div>
    </div>
  )
}
