import { NextResponse, NextRequest } from 'next/server';
import type { SchemaResponse, CodeGenOptions } from '@/lib/types';
import { handleProxyRequest } from '@/lib/apiProxy';

export async function POST(req: NextRequest) {
  try {
    const originalBody: { 
      schema: SchemaResponse; 
      options: CodeGenOptions;
    } = await req.json();

    const { schema, options } = originalBody;

    // Restructure request to match backend's expected format
    const backendRequestBody = {
      schema_data: schema,
      format: options.format,
      options: {
        includeComments: options.includeComments,
        includeValidation: options.includeValidation,
        language: options.language
      }
    };

    // Create a new Request object with the transformed body for the proxy function
    const modifiedRequest = new NextRequest(req.url, {
      method: req.method,
      headers: req.headers, // Pass original headers
      body: JSON.stringify(backendRequestBody),
      duplex: 'half' // Required for ReadableStream body in some environments
    });

    return handleProxyRequest({
      method: 'POST',
      backendPath: '/api/schema/generate-code', // Corrected backend path
      request: modifiedRequest, // Pass the new request with the transformed body
    });

  } catch (error) {
    console.error('Code generation error in route handler:', error);
    const message = error instanceof Error ? error.message : 'Internal server error in code generation route';
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}