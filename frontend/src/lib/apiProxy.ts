import { NextResponse, NextRequest } from 'next/server';
import { API_BASE_URL } from '@/lib/config';

interface ProxyRequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  backendPath: string; // e.g., "/api/users" or "/api/projects/123"
  request: NextRequest; // Original NextRequest to get body, headers, etc.
  // Add any specific transformation functions if needed, or handle them outside
  // requestBodyTransformer?: (body: any) => any;
  // responseBodyTransformer?: (body: any) => any;
}

export async function handleProxyRequest({
  method,
  backendPath,
  request,
}: ProxyRequestOptions): Promise<NextResponse> {
  let bodyPayload: FormData | Record<string, unknown> | null = null;
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');

  // Forward Authorization header if present (useful if auth is handled by Next.js middleware or similar)
  const authorizationHeader = request.headers.get('Authorization');
  if (authorizationHeader) {
    headers.set('Authorization', authorizationHeader);
  }
  
  // Add other headers you might want to forward or set by default
  // For example, an API key if your backend requires it and it's not sensitive to expose from server components
  // if (process.env.BACKEND_API_KEY) {
  //   headers.set('X-API-Key', process.env.BACKEND_API_KEY);
  // }

  if (request.body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    try {
      // Check if the request body is FormData
      const contentType = request.headers.get('Content-Type');
      if (contentType && contentType.startsWith('multipart/form-data')) {
        bodyPayload = await request.formData();
        headers.delete('Content-Type'); // Let fetch set the correct Content-Type for FormData
      } else {
        bodyPayload = await request.json();
      }
    } catch (error) {
      // Ignore error if body is empty or not JSON, fetch will handle it or it's not needed for this method
      console.warn("Could not parse JSON body for proxy request:", error);
    }
  }

  const targetUrl = `${API_BASE_URL}${backendPath}`;
  // console.log(`Proxying ${method} request to ${targetUrl}`);

  try {
    const response = await fetch(targetUrl, {
      method: method,
      headers: headers,
      body: bodyPayload instanceof FormData ? bodyPayload : (bodyPayload ? JSON.stringify(bodyPayload) : undefined),
      // duplex: 'half' might be needed for streaming with POST/PUT if you ever use it with ReadableStream bodies
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (errorParsing) {
        console.warn(`Failed to parse error response from backend for ${method} ${targetUrl}:`, errorParsing);
        errorData = { 
          message: `Backend error: ${response.status} ${response.statusText}`,
          detail: 'Failed to parse error response from backend, or no error body provided.'
        };
      }
      // console.error(`Backend error for ${method} ${targetUrl}:`, response.status, errorData);
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || errorData.detail || `An unknown error occurred (status: ${response.status})`,
          details: errorData.details || errorData, // Send the whole errorData as details if no specific structure
        },
        { status: response.status }
      );
    }

    if (response.status === 204) { // No Content
      return NextResponse.json({ success: true, message: "Operation successful, no content." }, { status: 204 });
    }
    
    const responseData = await response.json();
    // Ensure a consistent success wrapper if backend doesn't provide one
    // Some of your backend routes might already return a structure like { success: true, data: ... }
    // If not, you might want to wrap it here. For now, assume backend provides a reasonable structure or just pass it through.
    return NextResponse.json(responseData);

  } catch (error) {
    console.error(`API proxy fetch error for ${method} ${targetUrl}:`, error);
    const message = error instanceof Error ? error.message : 'Internal Server Error in API proxy';
    return NextResponse.json(
      { success: false, message: `Proxy error: ${message}` },
      { status: 500 }
    );
  }
}
