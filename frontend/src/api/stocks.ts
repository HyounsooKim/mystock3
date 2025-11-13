/**
 * Stocks API client - Interface for stock data endpoints
 */

import apiClient from './client'
import type { StockQuote } from '@/types'

export interface StockSearchResult {
  symbol: string
  name: string
  type: string
  region: string
  currency: string
}

export interface StockHistoryDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockHistoryResponse {
  symbol: string
  data: StockHistoryDataPoint[]
}

/**
 * Search for stocks by keyword
 * @param query - Search term (company name or symbol)
 * @returns Array of matching stocks
 */
export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  const response = await apiClient.get<{ results: StockSearchResult[], query: string }>('/stocks/search', {
    params: { keywords: query }
  })
  return response.data.results
}

/**
 * Get real-time quote for a stock symbol
 * @param symbol - Stock symbol (e.g., "AAPL")
 * @returns Stock quote with current price and change data
 */
export async function getStockQuote(symbol: string): Promise<StockQuote> {
  const response = await apiClient.get<StockQuote>(`/stocks/${symbol}/quote`)
  return response.data
}

/**
 * Get historical price data for a stock
 * @param symbol - Stock symbol (e.g., "AAPL")
 * @param period - Time period: "1D", "1W", "1M", "3M", "1Y"
 * @returns Historical data points
 */
export async function getStockHistory(
  symbol: string,
  period: '1D' | '1W' | '1M' | '3M' | '1Y' = '1M'
): Promise<StockHistoryResponse> {
  const response = await apiClient.get<StockHistoryResponse>(
    `/stocks/${symbol}/history`,
    {
      params: { period }
    }
  )
  return response.data
}

/**
 * Get multiple stock quotes (batch request)
 * @param symbols - Array of stock symbols
 * @returns Array of stock quotes
 */
export async function getBatchQuotes(symbols: string[]): Promise<StockQuote[]> {
  const promises = symbols.map(symbol => getStockQuote(symbol))
  const results = await Promise.allSettled(promises)
  
  return results
    .filter((result): result is PromiseFulfilledResult<StockQuote> => result.status === 'fulfilled')
    .map(result => result.value)
}
