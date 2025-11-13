/**
 * TypeScript interfaces for application data models.
 */

// User related types
export interface User {
  user_id: string
  email: string
  created_at: string
  is_active: boolean
  dark_mode: boolean
  language: string
}

export interface UserUpdate {
  email?: string
  password?: string
  is_active?: boolean
  dark_mode?: boolean
  language?: string
}

// Authentication types
export interface LoginRequest {
  email: string
  password: string
}

export interface SignupRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// Stock types
export interface StockQuote {
  symbol: string
  company_name: string
  current_price: number
  change: number
  change_percent: number
  open: number
  high: number
  low: number
  volume: number
  last_updated: string
  currency: string
}

// Watchlist types
export interface WatchlistItem {
  id: string
  user_id: string
  symbol: string
  company_name: string
  memo: string
  display_order: number
  created_at: string
  updated_at: string
}

export interface WatchlistItemWithQuote extends WatchlistItem {
  current_price: number | null
  change: number | null
  change_percent: number | null
}

export interface WatchlistItemCreate {
  symbol: string
  company_name: string
  memo?: string
}

export interface WatchlistItemUpdate {
  memo?: string
  display_order?: number
}

// Portfolio types
export type PortfolioCategory = '장기' | '단기' | '정찰병'

export interface PortfolioEntry {
  entry_id: string
  user_id: string
  symbol: string
  company_name: string
  category: PortfolioCategory
  purchase_price: number
  quantity: number
  created_at: string
  updated_at: string
}

export interface PortfolioEntryWithMetrics extends PortfolioEntry {
  current_price: number | null
  market_value: number | null
  profit_loss: number | null
  profit_loss_percent: number | null
}

export interface PortfolioEntryCreate {
  symbol: string
  company_name: string
  category: PortfolioCategory
  purchase_price: number
  quantity: number
}

export interface PortfolioEntryUpdate {
  purchase_price?: number
  quantity?: number
}

// API Error types
export interface ApiError {
  detail: string
  error_code?: string
  timestamp: string
}
