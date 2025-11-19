

SECTION 1 — GENERAL BEHAVIOR RULES

Always track progress and avoid getting stuck.
Keep a clear, step-by-step execution path for every feature.

Think before coding.
Always produce a high-level plan, verify the plan, then implement.

No hallucinations.
No invented APIs.
No fake functions.
If unsure, state uncertainty and request clarification.

Stay within the boundaries of the chosen tech stack.
Do not introduce tools not discussed by the user.

Maintain consistency across all modules.

SECTION 2 — ARCHITECTURE RULES

Enforce modular architecture always.
Every feature = separate module/service/component.

No file should exceed 500–600 lines.
Split logically into controllers, services, repositories, models, utils, config.

Ensure all microservices follow the same structure, including:

folder layout

naming conventions

API style

error-handling format

logging strategy

Use dependency injection patterns suitable for the language
(Spring Boot DI for Java, FastAPI dependency injection for Python).

SECTION 3 — CODE QUALITY RULES

Generate clean, readable code with no duplication.
If a pattern repeats, extract it into a helper/util.

Follow the official style guide:

Java → Google Java Style

Python → PEP8

Use proper naming conventions.
ClassNames, methodNames, variable_names, CONSTANTS.

Keep functions small and single-purpose.

Avoid unnecessary abstractions or complexity.

Never leave unused imports, dead code, or commented-out blocks.

SECTION 4 — RELIABILITY + ERROR HANDLING

Wrap all external calls in robust error handling, including:

DB queries

network requests

file access

cache operations

queue consumers

Use language-appropriate exception types
(no generic Exception unless unavoidable).

Always validate all user input before processing.

Never trust external data sources without sanitizing them.

Ensure graceful fallback behavior for microservices.

SECTION 5 — SECURITY RULES

No plaintext passwords. No secrets in code.

Every service must include:

authentication

authorization

request validation

rate limiting if public-facing

Never expose internal errors to the client.
Return clean, standardized responses.

Use correct hashing, encryption, CSRF protection, and proper CORS config where applicable.

SECTION 6 — PERFORMANCE RULES

Avoid N+1 queries.
Batch operations when needed.

Cache expensive operations (Redis, memory cache, etc).

Keep APIs fast, predictable, and scalable.

Respect async/await or reactive patterns where suitable.

Optimize database access, indexes, and query patterns.

SECTION 7 — TESTING REQUIREMENTS

For each module, generate:

unit tests

integration tests

edge-case tests

negative tests

All generated code must include tests unless explicitly skipped.

Tests must be realistic and executable (no imaginary methods).

Before finalizing, mentally simulate test execution to ensure logic correctness.

SECTION 8 — DOCUMENTATION + COMMENTS

Provide docstrings for every function.
Include parameters, return types, and purpose.

Add comments only when needed, not for obvious code.

Provide API documentation (OpenAPI/Swagger for backend).

SECTION 9 — REVIEW + VERIFICATION

At the end of coding, perform a full project-wide review, checking:

architecture consistency

errors

duplications

security issues

performance bottlenecks

logical correctness

naming consistency

missing tests

Confirm alignment with the initial plan.

Fix all found issues before finalizing.

SECTION 10 — OUTPUT STRICTNESS

No partial code unless requested.
If producing a file, produce it fully.

No guesses about undefined APIs, libraries, endpoints.
Ask the user to specify missing information.

Always return code that can realistically compile and run.

