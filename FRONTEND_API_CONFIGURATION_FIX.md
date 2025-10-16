# Frontend API Configuration Fix

## Problem
Your frontend is calling the AI Chat service directly:
```
https://schemasage-ai-chat-b619aa05a30e.herokuapp.com/chat
```

This bypasses the API Gateway, causing authentication failures (401 Unauthorized).

## Solution
Update your frontend to route ALL API requests through the API Gateway instead of calling microservices directly.

### Required Changes

#### 1. Update Frontend Environment Variables

**Current (WRONG):**
```bash
# Don't use these direct service URLs
NEXT_PUBLIC_AI_CHAT_URL=https://schemasage-ai-chat-b619aa05a30e.herokuapp.com
NEXT_PUBLIC_AUTH_URL=https://schemasage-auth-9d6de1a32af9.herokuapp.com
```

**Correct:**
```bash
# Single API Gateway URL
NEXT_PUBLIC_API_GATEWAY_URL=https://schemasage-api-gateway-<YOUR-ID>.herokuapp.com
# OR if you've deployed it, get the actual URL with:
# heroku info --app schemasage-api-gateway
```

#### 2. Update API Client Code

**Find your API client file** (likely `lib/api.ts`, `utils/api.js`, or similar) and update it:

**Before (WRONG):**
```typescript
// Don't call services directly
const AI_CHAT_URL = process.env.NEXT_PUBLIC_AI_CHAT_URL;

export async function chat(message: string) {
  const response = await fetch(`${AI_CHAT_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message })
  });
  return response.json();
}
```

**After (CORRECT):**
```typescript
// Route through API Gateway
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

export async function chat(message: string) {
  // Use /api/chat route - gateway will forward to AI Chat service
  const response = await fetch(`${API_GATEWAY_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message })
  });
  return response.json();
}
```

### API Gateway Routes

The API Gateway provides these routes (already configured):

| Frontend Route | Gateway Forwards To | Backend Service |
|----------------|---------------------|-----------------|
| `/api/chat/*` | AI Chat Service | Chat functionality |
| `/api/auth/*` | Authentication Service | Login, signup, OAuth |
| `/api/projects/*` | Project Management | Project CRUD |
| `/api/schema/*` | Schema Detection | Schema analysis |
| `/api/code-generation/*` | Code Generation | Code scaffolding |
| `/api/database/*` | Database Migration | Database operations |

### Step-by-Step Fix

1. **Get your API Gateway URL:**
   ```bash
   heroku info --app schemasage-api-gateway
   ```
   
2. **Update Vercel Environment Variables:**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add/Update: `NEXT_PUBLIC_API_GATEWAY_URL` = `https://your-gateway-url.herokuapp.com`
   - Remove direct service URLs if present
   
3. **Update your frontend code:**
   - Find all API calls in your codebase
   - Change them to use `${API_GATEWAY_URL}/api/chat` instead of direct service URLs
   
4. **Redeploy your frontend:**
   ```bash
   git push origin main  # This should trigger Vercel deployment
   ```

### Testing

After updating, test that requests go through the gateway:

1. Open browser DevTools → Network tab
2. Send a chat message
3. Verify the request URL is: `https://schemasage-api-gateway-<id>.herokuapp.com/api/chat`
4. Check response is 200 OK (not 401)

### Why This Fix Works

- **API Gateway handles authentication:** It validates JWT tokens and forwards them to backend services
- **Single entry point:** All requests go through one URL, easier to manage
- **Consistent routing:** Frontend doesn't need to know individual service URLs
- **Better security:** Backend services can trust requests from the gateway

## Next Steps

1. Find your API Gateway Heroku URL
2. Update frontend environment variables
3. Update frontend API client code
4. Redeploy frontend
5. Test the chat functionality

---

**Note:** The backend services (AI Chat, Authentication, etc.) are already correctly configured. Only the frontend needs updating.
