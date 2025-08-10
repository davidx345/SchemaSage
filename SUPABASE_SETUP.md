# Supabase Authentication Setup Guide

## Step 1: Get Your Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and sign in
2. Go to your SchemaSage project (or create one if you haven't)
3. Navigate to **Settings** → **API**
4. Copy these two values:
   - **Project URL** (this is your SUPABASE_URL)
   - **anon public** key (this is your SUPABASE_ANON_KEY)

## Step 2: Set Environment Variables on Heroku

Replace the placeholder values with your actual Supabase credentials:

```bash
heroku config:set SUPABASE_URL="https://your-project-id.supabase.co" --app schemasage-api-gateway
heroku config:set SUPABASE_ANON_KEY="your-anon-key-here" --app schemasage-api-gateway
```

## Step 3: Configure Supabase Authentication

1. In your Supabase dashboard, go to **Authentication** → **Settings**
2. Set your **Site URL** to: `https://schemasage.vercel.app`
3. Add redirect URLs:
   - `https://schemasage.vercel.app`
   - `https://schemasage.vercel.app/auth/callback` (if you use OAuth)
   - `http://localhost:3000` (for development)

## Step 4: Enable Email Confirmation (Optional)

1. Go to **Authentication** → **Settings**
2. Under **Email Confirmation**, you can:
   - **Enable** if you want users to verify their email
   - **Disable** for simpler signup flow

## Step 5: Update Your Frontend

Your frontend should now make requests to:
- **Signup**: `https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/auth/signup`
- **Signin**: `https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/auth/signin`
- **Get User**: `https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/auth/me`
- **Signout**: `https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/auth/signout`

## Request/Response Examples

### Signup Request:
```json
POST /api/auth/signup
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

### Response:
```json
{
  "access_token": "jwt-token-here",
  "refresh_token": "refresh-token-here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "user_metadata": {
      "name": "John Doe"
    }
  }
}
```

### Using the Access Token:
For protected routes, include the token in the Authorization header:
```
Authorization: Bearer your-jwt-token-here
```

## Benefits of This Setup

✅ **No custom auth service needed** - Supabase handles everything
✅ **Built-in email verification** - if you enable it
✅ **Password reset** - built into Supabase
✅ **Social logins** - can be added easily later
✅ **JWT tokens** - secure and standard
✅ **User management** - through Supabase dashboard
✅ **Real-time subscriptions** - for future features
