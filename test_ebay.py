import asyncio
from backend.services.price.providers.ebay import get_ebay_token, fetch_ebay_market_price

async def main():
    print("Testing eBay Token...")
    token = await get_ebay_token()
    if token:
        print("Success! Token starts with:", token[:15] + "...")
        print("Testing eBay Search for 'Super Mario 64 nintendo 64'...")
        price = await fetch_ebay_market_price("Super Mario 64", "nintendo 64")
        print("Price Result:", price)
    else:
        print("Failed to get eBay token. Credentials might be missing or invalid.")

if __name__ == "__main__":
    asyncio.run(main())
