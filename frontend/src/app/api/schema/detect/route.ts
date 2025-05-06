import { NextResponse } from 'next/server';
import type { DetectedSchema } from '@/lib/types';

export async function POST(req: Request) {
  try {
    const { data, options } = await req.json();
    
    // Fix: Rename options to settings to match backend's expected format
    const response = await fetch('http://localhost:8000/api/schema/detect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        data, 
        settings: options // Map options to settings
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || error.detail || 'Failed to detect schema' },
        { status: response.status }
      );
    }

    const result: DetectedSchema = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Schema detection error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}