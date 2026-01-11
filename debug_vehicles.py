"""Debug script to test vehicle data lookup."""
import asyncio
import aiohttp

API_VEHICLES = "https://files.cloudgdansk.pl/d/otwarte-dane/ztm/baza-pojazdow.json"

async def main():
    vehicles_cache = {}

    try:
        async with aiohttp.ClientSession() as session:
            print(f"Fetching from: {API_VEHICLES}")
            async with session.get(
                API_VEHICLES, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                print(f"Status: {response.status}")
                print(f"Final URL: {response.url}")
                response.raise_for_status()
                data = await response.json(content_type=None)

        vehicles = data.get("results", [])
        print(f"\nTotal vehicles in API: {len(vehicles)}")

        for vehicle in vehicles:
            vehicle_code = str(vehicle.get("vehicleCode", ""))
            if vehicle_code:
                vehicles_cache[vehicle_code] = {
                    "wheelchair_accessible": vehicle.get("wheelchairsRamp", False),
                    "bike_holders": vehicle.get("bikeHolders", 0),
                }

        print(f"Vehicles cached: {len(vehicles_cache)}")

        # Test lookups
        test_codes = [2746, "2746", 1152, "1152"]
        print("\n=== Testing vehicle lookups ===")
        for code in test_codes:
            result = vehicles_cache.get(str(code), {})
            print(f"Vehicle {code!r} (str={str(code)!r}): {result}")

        # Show sample of cache keys
        print("\n=== Sample cache keys ===")
        for key in list(vehicles_cache.keys())[:10]:
            print(f"  Key: {key!r} (type: {type(key).__name__})")

    except Exception as err:
        print(f"ERROR: {err}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
