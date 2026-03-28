from app.api.v1 import api_router
print(f"api_router has {len(api_router.routes)} routes")
for route in api_router.routes:
    try:
        methods = route.methods if hasattr(route, 'methods') else 'N/A'
        print(f"{route.path} {methods}")
    except:
        print(f"{route.path} (Unknown type)")
