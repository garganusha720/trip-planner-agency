// Free, no-API-key place search using OpenStreetMap's Nominatim service.
// Good enough for a portfolio/demo project's autocomplete needs. For a
// production app with real traffic, Nominatim's usage policy asks for
// caching and rate-limiting (max ~1 request/sec) — debouncing in the
// autocomplete component below covers that for normal typing speed.

export interface PlaceSuggestion {
  label: string
  lat: number
  lon: number
}

export async function searchPlaces(query: string): Promise<PlaceSuggestion[]> {
  if (!query || query.trim().length < 2) return []

  const url = `https://nominatim.openstreetmap.org/search?format=json&addressdetails=0&limit=6&q=${encodeURIComponent(
    query,
  )}`

  try {
    const res = await fetch(url, {
      headers: { "Accept-Language": "en" },
    })
    if (!res.ok) return []

    const data: Array<{ display_name: string; lat: string; lon: string }> = await res.json()

    return data.map((d) => ({
      label: d.display_name,
      lat: Number.parseFloat(d.lat),
      lon: Number.parseFloat(d.lon),
    }))
  } catch {
    // Network hiccup or Nominatim briefly down — fail quietly, the user
    // can still just type the destination manually.
    return []
  }
}
