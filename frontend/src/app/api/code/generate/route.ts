import { NextResponse } from 'next/server';
import type { SchemaResponse, CodeGenOptions } from '@/lib/types';
import { API_BASE_URL } from '@/lib/config';

export async function POST(req: Request) {
  try {
    const { schema, options }: { 
      schema: SchemaResponse; 
      options: CodeGenOptions;
    } = await req.json();

    // Fix: Update path and restructure request to match backend's expected format
    const response = await fetch(`${API_BASE_URL}/api/schema/generate-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        schema_data: schema,
        format: options.format,
        options: {
          includeComments: options.includeComments,
          includeValidation: options.includeValidation,
          language: options.language
        }
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || error.detail || 'Failed to generate code' },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Code generation error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}