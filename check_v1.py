from app.api.v1 import api_router
print(f"api_router has {len(api_router.routes)} routes")
for route in api_router.routes:
    print(f"{route.path} [{route.methods}]")
