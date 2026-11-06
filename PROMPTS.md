# \# AI Usage Log

# 

# This file records AI assistance used during TrustVault development. Entries describe actual development requests, generated guidance, verification and corrections.

# 

# \## Entry 1 – 2026-11-05 – Backend architecture and database models

# 

# \- \*\*Prompt / request:\*\* Help build a secure document-sharing application with Admin, Owner and Viewer roles, document permissions and an audit trail.

# \- \*\*AI output:\*\* Suggested a FastAPI backend, PostgreSQL database, SQLAlchemy models and separate modules for authentication, documents, permissions and audit events.

# \- \*\*What was wrong or needed verification:\*\* The initial scaffold did not implement the challenge's full authentication, document workflows or authorization requirements.

# \- \*\*What I changed:\*\* Implemented the database models for users, documents, document permissions and audit logs. Verified that all four models imported and their database tables were created successfully.

# \- \*\*Commit:\*\* Pending GitHub push.

# 

# \## Entry 2 – 2026-11-05 – Authentication and password security

# 

# \- \*\*Prompt / request:\*\* Implement registration, login, password hashing and JWT-based authentication.

# \- \*\*AI output:\*\* Provided guidance for FastAPI authentication, Argon2 password hashing, JWT creation and token validation.

# \- \*\*What was wrong or needed verification:\*\* Registration must not allow users to assign themselves Admin or Owner privileges. Passwords must not be stored in plain text.

# \- \*\*What I changed:\*\* Registration assigns the Viewer role by default. Passwords are hashed with Argon2. Login and the authenticated profile endpoint were tested successfully.

# \- \*\*Commit:\*\* Pending GitHub push.

# 

# \## Entry 3 – 2026-11-05 – Document authorization and permission revocation

# 

# \- \*\*Prompt / request:\*\* Implement document-level READ and EDIT permissions, sharing and revocation, and prevent unauthorized cross-user access.

# \- \*\*AI output:\*\* Suggested backend access-control checks for ownership and explicit permission grants.

# \- \*\*What was wrong or needed verification:\*\* Frontend controls alone cannot protect documents. Access must be checked on every backend request, and revoked access must stop working immediately.

# \- \*\*What I changed:\*\* Implemented backend access-control checks and permission grant/revoke endpoints. The integrated security script verified private document isolation, EDIT access, revocation and denial after revocation.

# \- \*\*Commit:\*\* Pending GitHub push.

# 

# \## Entry 4 – 2026-11-05 – Audit logging and document security

# 

# \- \*\*Prompt / request:\*\* Implement document activity logging, Admin audit retrieval and secure upload/download handling.

# \- \*\*AI output:\*\* Suggested audit event types, private file storage, upload validation and SHA-256 integrity verification.

# \- \*\*What was wrong or needed verification:\*\* Audit retrieval does not automatically provide tamper-proof storage. Upload validation also needs negative tests for malicious and spoofed files.

# \- \*\*What I changed:\*\* Implemented audit event recording and the Admin audit endpoint. Added file size, extension and content validation and SHA-256 verification on download. Verified audit retrieval and denied-access recording. Tamper-resistant audit storage remains future work.

# \- \*\*Commit:\*\* Pending GitHub push.

# 

# \## Entry 5 – 2026-11-06 – Frontend integration and security checks

# 

# \- \*\*Prompt / request:\*\* Fix frontend sharing integration and safely handle backend API errors.

# \- \*\*AI output:\*\* Identified that the frontend was sending a user ID while the backend expected a recipient email. Suggested safe error formatting to prevent React rendering failures.

# \- \*\*What was wrong or needed verification:\*\* The mismatched request field caused sharing to fail, and API error responses could contain objects that React could not render as text.

# \- \*\*What I changed:\*\* Updated the sharing request to send the recipient email and added safe error formatting. Verified successful sharing and Viewer access restrictions. The frontend production build passed, backend tests reported 1 passed, and all 14 integrated security checks passed.

# \- \*\*Commit:\*\* Pending GitHub push.

# 

# \## AI Assistance and Ownership

# 

# AI assistance was used for implementation guidance, code generation, debugging and documentation. Project code and behavior were verified locally through API checks, frontend builds, backend tests and the integrated security script.

# 

# The developer remains responsible for understanding, reviewing, testing and maintaining the submitted implementation.

