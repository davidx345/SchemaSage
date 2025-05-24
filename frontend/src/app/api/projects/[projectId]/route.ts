import { NextRequest, NextResponse } from 'next/server';

// Updated route parameter type to match Next.js 15.3.2 expectations
export async function GET(
  req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const { projectId } = params;
  try {
    const response = await fetch(`http://localhost:8000/api/database/projects/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to parse error response from API' }));
      return NextResponse.json(
        {
          success: false,
          message: error.message || error.detail || `Failed to retrieve project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ success: true, data });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error occurred during project retrieval';
    console.error(`Error in GET /api/projects/${projectId}:`, error);
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}

// PUT handler with inline type definition
export async function PUT(
  request: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const { projectId } = params;
  try {
    const updateData = await request.json();
    const response = await fetch(`http://localhost:8000/api/database/projects/${projectId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to parse error response from API' }));
      return NextResponse.json(
        {
          success: false,
          message: error.message || error.detail || `Failed to update project ${projectId}`,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ success: true, data });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error occurred during project update';
    console.error(`Error in PUT /api/projects/${projectId}:`, error);
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}

// DELETE handler with inline type definition
export async function DELETE(
  request: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const { projectId } = params;
  try {
    const response = await fetch(`http://localhost:8000/api/database/projects/${projectId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to parse error response from API' }));
      return NextResponse.json(
        {
          success: false,
          message: error.message || error.detail || `Failed to delete project ${projectId}`,
        },
        { status: response.status }
      );
    }

    // DELETE requests might not return a body or return a confirmation message
    try {
        const data = await response.json();
        return NextResponse.json({ success: true, data });
    } catch (e) {
        // Handle cases where DELETE might return no content or non-JSON response on success
        if (response.status === 204 || response.status === 200) {
             return NextResponse.json({ success: true, message: `Project ${projectId} deleted successfully.` });
        }
        // If it's an actual error parsing what should have been an error response
        const errorMsg = e instanceof Error ? e.message : 'Failed to parse API response after delete attempt';
        console.error(`Error parsing response for DELETE /api/projects/${projectId} (after non-ok status was not hit):`, e);
        return NextResponse.json(
          { success: false, message: `Project ${projectId} deleted, but response parsing failed: ${errorMsg}` },
          { status: response.status }
        );
    }

  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error occurred during project deletion';
    console.error(`Error in DELETE /api/projects/${projectId}:`, error);
    return NextResponse.json(
      { success: false, message },
      { status: 500 }
    );
  }
}