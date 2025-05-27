import { NextRequest, NextResponse } from 'next/server';
import type { DatabaseConfig } from '@/lib/types';
import { handleProxyRequest } from '@/lib/apiProxy';

// The POST handler in this file is redundant as api/database/connect/route.ts handles it.
// We will remove the POST handler from this file to avoid duplication.
// If POST requests to /api/database were intended for a different backend endpoint,
// this would need to be adjusted. Assuming /api/database/connect is the sole target for this type of POST.

export async function PUT(req: NextRequest) {
  try {
    // The body { config, tables } needs to be proxied.
    // handleProxyRequest will read this body from `req` directly.
    const originalBody: { config: DatabaseConfig; tables: string[] } = await req.json();

    // The backend endpoint for import is /api/database/import and it expects a POST request
    // according to the original fetch call. The frontend route uses PUT.
    // We should align the method or ensure the backend handles PUT for this path if that's intended.
    // For now, we will proxy as PUT to /api/database/import, assuming backend can handle it or will be updated.
    // If backend strictly expects POST for import, then this frontend route should be POST or the proxy needs to change method.

    // Let's assume the backend /api/database/import can handle PUT, or this frontend route should be POST.
    // For minimal changes to this route handler logic, we'll proxy as PUT.
    // If the backend strictly requires POST for import, this should be changed.

    // The original code was sending a POST to /api/database/import.
    // This route is PUT /api/database.
    // This implies the backend /api/database/import should be called with POST.
    // This is a mismatch. Let's clarify: the frontend route is PUT /api/database.
    // The backend target is POST /api/database/import.
    // The proxy should send a POST to the backendPath.

    // The `handleProxyRequest` sends the method specified. So if we say PUT here, it sends PUT.
    // The original code in this PUT handler was actually making a POST to the backend.
    // This means the `handleProxyRequest` should be called with method: 'POST' for this specific case,
    // even though the Next.js route is PUT.

    // Create a new Request object with the original body for the proxy function,
    // ensuring the body is correctly formatted for the proxy.
    const modifiedRequest = new NextRequest(req.url, {
        method: 'POST', // We are calling the backend's POST import endpoint
        headers: req.headers,
        body: JSON.stringify(originalBody),
        duplex: 'half' 
    });

    return handleProxyRequest({
      method: 'POST', // Explicitly POST to the backend import endpoint
      backendPath: '/api/database/import',
      request: modifiedRequest, // Pass the request that has the correct body and now also the correct method for the proxy target
    });

  } catch (error) {
    console.error('Schema import error in route handler:', error);
    const message = error instanceof Error ? error.message : 'Internal server error in schema import route';
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}

// To remove the redundant POST handler:
// Delete the existing POST function from this file.
// If this file should ONLY handle PUT, then the POST function should be removed entirely.
// For now, I will comment it out to indicate it's being deprecated in favor of /api/database/connect/route.ts

/*
export async function POST(req: NextRequest) {
  // This functionality is now handled by /api/database/connect/route.ts
  // If you need a POST to /api/database for a different purpose, implement it here.
  // Otherwise, this can be removed.
  return NextResponse.json(
    { success: false, message: 'This POST endpoint is deprecated. Use /api/database/connect.' },
    { status: 404 }
  );
}
*/