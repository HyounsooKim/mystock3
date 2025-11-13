import asyncio
from src.external.alpha_vantage_client import AlphaVantageClient
from src.config import get_settings

async def test():
    settings = get_settings()
    async with AlphaVantageClient(settings.alpha_vantage_api_key) as client:
        try:
            quote = await client.get_quote('META')
            print(f'✅ META Price: ${quote.current_price}')
            print(f'   Company: {quote.company_name}')
            print(f'   Change: {quote.change}')
        except Exception as e:
            print(f'❌ Failed to get META: {type(e).__name__}: {e}')

if __name__ == '__main__':
    asyncio.run(test())
