# Core Project Management Endpoints

This list includes only the endpoints directly related to project management (creating, updating, listing, and managing projects, files, and activities). It excludes compliance, marketplace, integrations, glossary, and unrelated features.

---

## Main Project Endpoints

- **POST /api/projects** — Create a new project
- **GET /api/projects** — List user projects
- **GET /api/projects/{project_id}** — Get project by ID
- **PUT /api/projects/{project_id}** — Update project
- **POST /api/projects/{project_id}/files** — Add file to project
- **POST /api/projects/{project_id}/activity** — Log project activity

## Collaboration (Teams & Projects)
- **POST /** — Create a team
- **GET /{team_id}** — Get team info
- **GET /{team_id}/members** — List team members
- **POST /{team_id}/invite** — Invite member to team
- **POST /{team_id}/members/{user_id}/role** — Update member role
- **DELETE /{team_id}/members/{user_id}** — Remove member
- **GET /{team_id}/projects** — List projects for a team
- **GET /{team_id}/activity** — Team activity log
- **PUT /{team_id}/settings** — Update team settings
- **POST /{team_id}/share-schema** — Share schema with team
- **GET /user/{user_id}** — List teams for a user

## Activity Tracking (Project-related)
- **POST /track** — Track activity (if used for project actions)
- **GET /recent** — Recent activities
- **GET /stats** — Activity stats

---

For request/response details, see the router and main service code. This list is focused on endpoints for managing projects, project files, activities, and team collaboration only.
