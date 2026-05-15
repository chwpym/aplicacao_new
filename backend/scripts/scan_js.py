import asyncio
import httpx
import re

async def find_js_endpoints():
    base_url = "https://vehiclelifetimesolutions.schaeffler.com.br"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(base_url, headers=headers)
        js_files = re.findall(r'src="([^"]+\.js[^"]*)"', r.text)
        
        for js in js_files:
            js_url = js if js.startswith("http") else f"{base_url}{js if js.startswith('/') else '/' + js}"
            try:
                js_content = await client.get(js_url, headers=headers)
                text = js_content.text
                
                matches = re.finditer(r'.{0,150}(products/\$\{productCode\}/references).{0,150}', text)
                for m in matches:
                    print("Context:", m.group(0))
                    print("---")
            except Exception as e:
                pass

asyncio.run(find_js_endpoints())
