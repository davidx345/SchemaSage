# Project Management Service Endpoints

This document lists every endpoint implemented in the `project-management` service, including all routers. For each endpoint, the HTTP method, path, and (where possible) a short description are provided. For detailed request/response formats, see the code or OpenAPI docs.

---

## Main Project Endpoints

- **POST /api/projects** — Create a new project
- **GET /api/projects** — List user projects
- **GET /api/projects/{project_id}** — Get project by ID
- **PUT /api/projects/{project_id}** — Update project
- **POST /api/projects/{project_id}/files** — Add file to project
- **POST /api/projects/{project_id}/activity** — Log project activity

## Activity Tracking
- **POST /track**
- **GET /recent**
- **GET /stats**

## Marketplace
- **GET /templates**
- **GET /templates/{template_id}**
- **POST /purchase**
- **GET /my-purchases**
- **POST /templates**
- **PUT /templates/{template_id}**
- **GET /my-templates**
- **GET /categories**
- **GET /stats**

## Integrations
- **GET /webhooks**
- **POST /webhooks**
- **POST /webhooks/enable**
- **POST /webhooks/disable**
- **POST /webhooks/trigger**
- **GET /notifications**
- **POST /notifications**
- **POST /notifications/enable**
- **POST /notifications/disable**
- **POST /notifications/trigger**
- **GET /cloud-storage**
- **POST /cloud-storage**
- **POST /cloud-storage/enable**
- **POST /cloud-storage/disable**
- **POST /cloud-storage/trigger**
- **GET /bi-tools**
- **POST /bi-tools**
- **POST /bi-tools/enable**
- **POST /bi-tools/disable**
- **POST /bi-tools/trigger**
- **GET /data-catalogs**
- **POST /data-catalogs**
- **POST /data-catalogs/enable**
- **POST /data-catalogs/disable**
- **POST /data-catalogs/trigger**
- **GET /custom-api**
- **POST /custom-api**
- **POST /custom-api/enable**
- **POST /custom-api/disable**
- **POST /custom-api/trigger**

## Glossary
- **GET /glossary**
- **POST /glossary**
- **PUT /glossary/{term_id}**
- **DELETE /glossary/{term_id}**
- **POST /schema/consistency-check**

## Data Dictionary Integration
- **POST /project/{project_id}/generate**
- **GET /project/{project_id}**
- **PUT /project/{project_id}/table/{table_name}**
- **POST /project/{project_id}/table/{table_name}/auto-document**
- **GET /project/{project_id}/coverage-report**
- **POST /project/{project_id}/export**
- **GET /project/{project_id}/compare-versions**

## Compliance & Alerts
- **GET /frameworks**
- **GET /frameworks/{framework}**
- **POST /assess**
- **GET /cross-analysis**
- **GET /templates**
- **POST /multi-framework-detection**
- **POST /generate-compliant-code**
- **GET /project/{project_id}/status**
- **GET /industry/{industry}/recommendations**
- **GET /health**
- **POST /webhooks**
- **GET /webhooks**
- **DELETE /webhooks/{webhook_id}**
- **POST /send-alert**
- **GET /notifications/history**
- **POST /test-webhook/{webhook_id}**
- **GET /events**
- **GET /stats**

## Comments
- **POST /schema/{schema_id}**
- **GET /schema/{schema_id}**
- **PUT /{comment_id}**
- **DELETE /{comment_id}**
- **POST /{comment_id}/like**
- **POST /{comment_id}/reply**
- **POST /feedback/schema/{schema_id}**
- **GET /feedback/schema/{schema_id}**
- **GET /mentions/{user_id}**
- **POST /mentions/{mention_id}/mark-read**

## Collaboration (Teams)
- **POST /**
- **GET /{team_id}**
- **GET /{team_id}/members**
- **POST /{team_id}/invite**
- **POST /{team_id}/members/{user_id}/role**
- **DELETE /{team_id}/members/{user_id}**
- **GET /{team_id}/projects**
- **GET /{team_id}/activity**
- **PUT /{team_id}/settings**
- **POST /{team_id}/share-schema**
- **GET /user/{user_id}**

---

For each endpoint, see the router file for request/response details. This list covers all implemented endpoints as of November 2025.
