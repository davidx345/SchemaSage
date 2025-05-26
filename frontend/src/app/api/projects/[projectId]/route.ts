import { NextResponse } from 'next/server';
import { API_BASE_URL } from '@/lib/config';

interface RouteParams {
  params: {
    projectId: string;
  };
}

export async function GET(req: Request, { params }: RouteParams) {
  try {
    const { projectId } = params;
    
    const response = await fetch(`${API_BASE_URL}/api/database/projects/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || `Failed to retrieve project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Get project error:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}

export async function PUT(req: Request, { params }: RouteParams) {
  try {
    const { projectId } = params;
    const updateData = await req.json();
    
    const response = await fetch(`${API_BASE_URL}/api/database/projects/${projectId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || `Failed to update project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Update project error:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}

export async function DELETE(req: Request, { params }: RouteParams) {
  try {
    const { projectId } = params;
    
    const response = await fetch(`${API_BASE_URL}/api/database/projects/${projectId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { 
          success: false, 
          message: error.message || error.detail || `Failed to delete project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Delete project error:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}