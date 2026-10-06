/**
 * Core domain types for Collectabase.
 * These mirror the Pydantic schemas on the FastAPI backend.
 */

export interface Platform {
  id: number
  name: string
  manufacturer?: string | null
  type?: string | null
}

export interface Game {
  id: number
  title: string
  platform_id: number | null
  platform_name?: string | null
  item_type: 'game' | 'console' | 'accessory' | 'misc' | string
  barcode?: string | null
  igdb_id?: number | null
  release_date?: string | null
  publisher?: string | null
  developer?: string | null
  genre?: string | null
  description?: string | null
  cover_url?: string | null
  region?: string | null
  condition?: string | null
  completeness?: string | null
  location?: string | null
  purchase_date?: string | null
  purchase_price?: number | null
  current_value?: number | null
  last_price_at?: string | null
  notes?: string | null
  alt_titles?: string | string[] | null
  alt_titles_list?: string[]
  is_wishlist: number | boolean
  wishlist_max_price?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PriceEntry {
  id: number
  game_id: number
  source: string
  loose_price?: number | null
  complete_price?: number | null
  new_price?: number | null
  eur_rate?: number | null
  pricecharting_id?: string | null
  fetched_at?: string | null
}

export interface Stats {
  total_games: number
  total_value: number
  purchase_value: number
  profit_loss: number
  wishlist_count: number
  by_platform: Array<{ name: string; count: number; value: number; invested: number; profit_loss: number }>
  by_condition: Array<{ condition: string; count: number }>
  by_type: Array<{ item_type: string; count: number; value: number; invested: number }>
}

export interface ApiResponse<T> {
  ok: boolean
  status: number
  data: T
}
