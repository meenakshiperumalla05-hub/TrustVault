# \# TrustVault Threat Model

# 

# This document records the main security threats, implemented controls, available test evidence and remaining risks.

# 

# | Threat | Attack path | Mitigation / current implementation | Test evidence | Status and residual risk |

# |---|---|---|---|---|

# | IDOR / cross-user document access | A user changes a document ID in an API request to access another user's document. | Backend checks document ownership or an explicit permission grant before allowing access. | Integrated security check: Viewer was blocked from accessing a private document; unauthorized view was recorded. | Tested for the checked scenario. Other endpoint and edge-case combinations still require broader coverage. |

# | Revoked access | A user attempts to reuse access after the owner revokes a permission. | Current document permission is checked on each request. | Integrated security check: access was revoked and the Viewer was immediately blocked. | Tested for the checked scenario. Continue testing concurrent requests and all document endpoints. |

# | Viewer performs unauthorized changes | A Viewer attempts to modify or delete another user's document. | Backend edit and ownership checks enforce permissions independently of frontend controls. | Integrated security check: Viewer could not delete the owner's document. A user with EDIT permission successfully updated metadata. | Partial evidence. Add a dedicated test proving a Viewer without EDIT permission receives 403 on metadata updates. |

# | Audit tampering | An attacker with database access attempts to modify or delete audit records. | Audit events are recorded and the Admin audit retrieval API is available. Database-level append-only enforcement and cryptographic hash-chain verification are not established. | Audit retrieval and event recording were verified. No tamper-resistance test has been completed. | Open risk. Implement database restrictions and tamper-evidence controls, then test alteration and deletion attempts. |

# | Malicious upload | An attacker uploads an executable, spoofed or oversized file. | File extension allowlist, size limit, content inspection and private storage are implemented. | Upload workflow was tested, but dedicated rejection tests for malicious, spoofed and oversized files have not been recorded. | Partial implementation. Add negative upload tests and consider malware scanning before production. |

# | Credential compromise | An attacker obtains a password or access token. | Argon2 password hashing, JWT authentication and token expiry are implemented. | Admin and Viewer login were successful during integrated security checks. | Password/token attack scenarios, rate limiting, refresh/revocation and brute-force protections need further review. |

# | File integrity violation | A stored document is changed outside the application. | SHA-256 hash is calculated during upload and verified during download. | Integrity verification failure is represented in the audit workflow; dedicated tampering coverage should be retained in the test suite. | Requires additional automated coverage and secure storage permissions. |

# 

# \## General Security Requirements

# 

# \- Never rely only on frontend role checks.

# \- Authorize every document read and mutation on the backend.

# \- Do not expose private document storage through static web hosting.

# \- Keep secrets outside source control.

# \- Use HTTPS and secure production configuration.

# \- Avoid real confidential documents and real credentials in development data.

# \- Keep audit records protected from unauthorized modification and deletion.

# 

# \## Verification Summary

# 

# The integrated security script completed 14 checks successfully, covering authentication, private document access, permission grants, permission revocation, document updates, deletion restrictions and audit event retrieval.

# 

# This does not establish that every possible attack path has been tested. Open risks above must be addressed before describing the application as production-ready.

