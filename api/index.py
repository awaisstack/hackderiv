from backend.app.main import app

# Vercel Serverless Function Entry Point
# We wrap the app to strip the /api/py prefix manually if needed

async def handler(scope, receive, send):
    """
    ASGI Handler that strips /api/py from the path to ensure
    FastAPI routing works correctly on Vercel.
    """
    if scope['type'] == 'http':
        # Vercel rewrites /api/py/* -> /api/index.py
        # But the scope['path'] might still be /api/py/scan
        if scope['path'].startswith('/api/py'):
            scope['path'] = scope['path'].replace('/api/py', '', 1)
            # Ensure we don't end up with empty path (should be /)
            if not scope['path']:
                scope['path'] = '/'
    
    await app(scope, receive, send)

# Vercel looks for 'app' or 'handler'
# We expose 'app' as the wrapped handler
# But wait, Vercel might expect 'app' to be the ASGI app instance directly if we don't define a handler function?
# Actually, for Vercel Python, it expects a global 'app' variable.
# If we re-assign 'app' to 'handler', it should work.

app = handler
