"use client"

import { useEffect, useRef, useState } from "react"
import { Input } from "@/components/ui/input"
import { searchPlaces, type PlaceSuggestion } from "@/lib/geocode"

interface LocationAutocompleteProps {
  id: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
}

export function LocationAutocomplete({
  id,
  value,
  onChange,
  placeholder,
  required,
}: LocationAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Close the dropdown when clicking anywhere outside it.
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  function handleInputChange(newValue: string) {
    onChange(newValue)
    setOpen(true)

    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (newValue.trim().length < 2) {
      setSuggestions([])
      return
    }

    // Debounce so we're not firing a request on every keystroke.
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      const results = await searchPlaces(newValue)
      setSuggestions(results)
      setLoading(false)
    }, 400)
  }

  function handleSelect(suggestion: PlaceSuggestion) {
    onChange(suggestion.label)
    setSuggestions([])
    setOpen(false)
  }

  return (
    <div ref={containerRef} className="relative">
      <Input
        id={id}
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={() => value.trim().length >= 2 && setOpen(true)}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
      />
      {open && (loading || suggestions.length > 0) && (
        <div className="absolute z-50 mt-1 max-h-64 w-full overflow-y-auto rounded-md border border-border bg-popover shadow-md">
          {loading && (
            <div className="px-3 py-2 text-sm text-muted-foreground">Searching…</div>
          )}
          {!loading &&
            suggestions.map((s, i) => (
              <button
                key={`${s.label}-${i}`}
                type="button"
                onClick={() => handleSelect(s)}
                className="block w-full truncate px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                title={s.label}
              >
                {s.label}
              </button>
            ))}
        </div>
      )}
    </div>
  )
}
