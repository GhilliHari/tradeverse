import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        # We test localhost to ensure the backend is setting headers properly
        res = await client.options("http://127.0.0.1:8000/api/settings/update", headers={
            "Origin": "https://tradeverse-lilac.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type, ngrok-skip-browser-warning, bypass-tunnel-reminder"
        })
        print(f"Status: {res.status_code}")
        print("Headers:")
        for k, v in res.headers.items():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
                
asyncio.run(test())
