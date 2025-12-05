import httpx
import asyncio

async def test_embed():
    async with httpx.AsyncClient() as client:
        # Test with query params
        response = await client.post(
            'http://localhost:8001/utility/embed',
            params={'text': 'Hello World'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            result = response.json()
            print(f"Embedding dimensions: {len(result['embedding'])}")

asyncio.run(test_embed())
