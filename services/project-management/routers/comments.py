"""
Comments and Feedback API Routes

Handles user comments, feedback, and collaboration features for schemas and projects.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router for comments and feedback
router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/schema/{schema_id}")
async def add_schema_comment(
    schema_id: int,
    comment_data: Dict[str, Any]
):
    """Add a comment to a schema"""
    try:
        # Mock comment creation
        comment = {
            "id": 1001,
            "schema_id": schema_id,
            "user_id": comment_data.get("user_id", 1),
            "username": comment_data.get("username", "anonymous"),
            "content": comment_data.get("content", ""),
            "comment_type": comment_data.get("type", "general"),  # general, question, suggestion, issue
            "parent_id": comment_data.get("parent_id"),  # For replies
            "metadata": {
                "context": comment_data.get("context"),  # What part of schema this relates to
                "priority": comment_data.get("priority", "medium"),
                "tags": comment_data.get("tags", [])
            },
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "likes": 0,
            "replies_count": 0
        }
        
        return {
            "comment": comment,
            "message": "Comment added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding schema comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.get("/schema/{schema_id}")
async def get_schema_comments(
    schema_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    comment_type: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|likes)$")
):
    """Get comments for a schema"""
    try:
        # Mock comments data
        mock_comments = [
            {
                "id": 1001,
                "schema_id": schema_id,
                "user_id": 1,
                "username": "john_doe",
                "content": "This schema looks great! The user table structure is well-designed.",
                "comment_type": "general",
                "parent_id": None,
                "metadata": {
                    "context": "table:users",
                    "priority": "low",
                    "tags": ["approval", "design"]
                },
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "likes": 3,
                "replies_count": 1,
                "replies": [
                    {
                        "id": 1002,
                        "user_id": 2,
                        "username": "jane_smith",
                        "content": "I agree! The indexes are particularly well thought out.",
                        "created_at": "2024-01-15T11:00:00Z",
                        "likes": 1
                    }
                ]
            },
            {
                "id": 1003,
                "schema_id": schema_id,
                "user_id": 3,
                "username": "mike_wilson",
                "content": "Should we consider adding a soft delete column to the orders table?",
                "comment_type": "suggestion",
                "parent_id": None,
                "metadata": {
                    "context": "table:orders",
                    "priority": "medium",
                    "tags": ["suggestion", "data-integrity"]
                },
                "status": "active",
                "created_at": "2024-01-15T14:20:00Z",
                "updated_at": "2024-01-15T14:20:00Z",
                "likes": 5,
                "replies_count": 0,
                "replies": []
            }
        ]
        
        # Filter by type if specified
        if comment_type:
            mock_comments = [c for c in mock_comments if c["comment_type"] == comment_type]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_comments = mock_comments[start_idx:end_idx]
        
        return {
            "comments": paginated_comments,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_comments),
                "pages": (len(mock_comments) + limit - 1) // limit
            },
            "summary": {
                "total_comments": len(mock_comments),
                "by_type": {
                    "general": len([c for c in mock_comments if c["comment_type"] == "general"]),
                    "question": len([c for c in mock_comments if c["comment_type"] == "question"]),
                    "suggestion": len([c for c in mock_comments if c["comment_type"] == "suggestion"]),
                    "issue": len([c for c in mock_comments if c["comment_type"] == "issue"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting schema comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comments")


@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    update_data: Dict[str, Any]
):
    """Update a comment"""
    try:
        # Mock comment update
        updated_comment = {
            "id": comment_id,
            "content": update_data.get("content", "Updated comment content"),
            "comment_type": update_data.get("type", "general"),
            "metadata": update_data.get("metadata", {}),
            "updated_at": datetime.now().isoformat(),
            "edit_history": [
                {
                    "edited_at": datetime.now().isoformat(),
                    "edited_by": update_data.get("user_id", 1),
                    "changes": "Content updated"
                }
            ]
        }
        
        return {
            "comment": updated_comment,
            "message": "Comment updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment")


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, user_id: int):
    """Delete a comment"""
    try:
        return {
            "message": "Comment deleted successfully",
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": user_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")


@router.post("/{comment_id}/like")
async def like_comment(comment_id: int, user_id: int):
    """Like or unlike a comment"""
    try:
        # Mock like toggle
        return {
            "comment_id": comment_id,
            "user_id": user_id,
            "liked": True,
            "total_likes": 4,
            "action": "liked"
        }
        
    except Exception as e:
        logger.error(f"Error liking comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to like comment")


@router.post("/{comment_id}/reply")
async def reply_to_comment(
    comment_id: int,
    reply_data: Dict[str, Any]
):
    """Reply to a comment"""
    try:
        reply = {
            "id": 2001,
            "parent_id": comment_id,
            "user_id": reply_data.get("user_id", 1),
            "username": reply_data.get("username", "anonymous"),
            "content": reply_data.get("content", ""),
            "created_at": datetime.now().isoformat(),
            "likes": 0
        }
        
        return {
            "reply": reply,
            "message": "Reply added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reply")


@router.post("/feedback/schema/{schema_id}")
async def submit_schema_feedback(
    schema_id: int,
    feedback_data: Dict[str, Any]
):
    """Submit feedback for a schema"""
    try:
        feedback = {
            "id": 3001,
            "schema_id": schema_id,
            "user_id": feedback_data.get("user_id", 1),
            "feedback_type": feedback_data.get("type", "general"),  # general, bug, feature_request, improvement
            "subject": feedback_data.get("subject", ""),
            "description": feedback_data.get("description", ""),
            "rating": feedback_data.get("rating"),  # 1-5 stars
            "metadata": {
                "affected_components": feedback_data.get("affected_components", []),
                "severity": feedback_data.get("severity", "medium"),
                "browser": feedback_data.get("browser"),
                "environment": feedback_data.get("environment")
            },
            "status": "open",
            "priority": "medium",
            "created_at": datetime.now().isoformat(),
            "assignee": None
        }
        
        return {
            "feedback": feedback,
            "message": "Feedback submitted successfully",
            "ticket_number": f"FB-{feedback['id']}"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/feedback/schema/{schema_id}")
async def get_schema_feedback(
    schema_id: int,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Get feedback for a schema"""
    try:
        # Mock feedback data
        mock_feedback = [
            {
                "id": 3001,
                "schema_id": schema_id,
                "user_id": 1,
                "feedback_type": "improvement",
                "subject": "Add validation rules",
                "description": "Would be great to have built-in validation rules for email and phone fields",
                "rating": 4,
                "status": "open",
                "priority": "medium",
                "created_at": "2024-01-15T09:00:00Z",
                "assignee": "dev_team"
            },
            {
                "id": 3002,
                "schema_id": schema_id,
                "user_id": 2,
                "feedback_type": "bug",
                "subject": "Relationship issue",
                "description": "The foreign key relationship between orders and customers seems incorrect",
                "rating": 2,
                "status": "in_progress",
                "priority": "high",
                "created_at": "2024-01-14T16:30:00Z",
                "assignee": "john_doe"
            }
        ]
        
        # Apply filters
        if status:
            mock_feedback = [f for f in mock_feedback if f["status"] == status]
        if feedback_type:
            mock_feedback = [f for f in mock_feedback if f["feedback_type"] == feedback_type]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_feedback = mock_feedback[start_idx:end_idx]
        
        return {
            "feedback": paginated_feedback,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_feedback),
                "pages": (len(mock_feedback) + limit - 1) // limit
            },
            "summary": {
                "total_feedback": len(mock_feedback),
                "by_status": {
                    "open": len([f for f in mock_feedback if f["status"] == "open"]),
                    "in_progress": len([f for f in mock_feedback if f["status"] == "in_progress"]),
                    "resolved": len([f for f in mock_feedback if f["status"] == "resolved"]),
                    "closed": len([f for f in mock_feedback if f["status"] == "closed"])
                },
                "average_rating": 3.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting schema feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


@router.get("/mentions/{user_id}")
async def get_user_mentions(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False
):
    """Get mentions for a user across comments and feedback"""
    try:
        # Mock mentions data
        mock_mentions = [
            {
                "id": 4001,
                "type": "comment",
                "comment_id": 1001,
                "schema_id": 123,
                "mentioned_by": {
                    "user_id": 2,
                    "username": "jane_smith"
                },
                "content": "Hey @john_doe, what do you think about this approach?",
                "context": "table:users",
                "read": False,
                "created_at": "2024-01-15T14:30:00Z"
            },
            {
                "id": 4002,
                "type": "feedback",
                "feedback_id": 3001,
                "schema_id": 456,
                "mentioned_by": {
                    "user_id": 3,
                    "username": "mike_wilson"
                },
                "content": "Assigning this to @john_doe for review",
                "context": "feedback",
                "read": True,
                "created_at": "2024-01-15T12:00:00Z"
            }
        ]
        
        # Filter unread only if requested
        if unread_only:
            mock_mentions = [m for m in mock_mentions if not m["read"]]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_mentions = mock_mentions[start_idx:end_idx]
        
        return {
            "mentions": paginated_mentions,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_mentions),
                "pages": (len(mock_mentions) + limit - 1) // limit
            },
            "unread_count": len([m for m in mock_mentions if not m["read"]])
        }
        
    except Exception as e:
        logger.error(f"Error getting user mentions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mentions")


@router.post("/mentions/{mention_id}/mark-read")
async def mark_mention_read(mention_id: int, user_id: int):
    """Mark a mention as read"""
    try:
        return {
            "mention_id": mention_id,
            "user_id": user_id,
            "read": True,
            "marked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error marking mention as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark mention as read")
