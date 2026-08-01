"use client"

import { Plane } from "lucide-react"

export function TripLoading({ destination }: { destination: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-16 text-center">
      <div className="relative flex size-20 items-center justify-center">
        <span className="absolute inline-flex size-20 animate-ping rounded-full bg-primary/20" />
        <span className="flex size-16 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Plane className="size-7" />
        </span>
      </div>
      <div className="space-y-1">
        <p className="text-lg font-semibold">
          Mapping out {destination || "your trip"}…
        </p>
        <p className="text-sm text-muted-foreground">
          Balancing your budget, hotels, and daily plans.
        </p>
      </div>
      <div className="flex gap-1.5" aria-hidden>
        <span className="size-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
        <span className="size-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
        <span className="size-2 animate-bounce rounded-full bg-primary" />
      </div>
    </div>
  )
}
