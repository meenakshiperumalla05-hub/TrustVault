
import getpass
import sys
import httpx

BASE_URL = "http://127.0.0.1:8001"


def check(condition, message):
    if not condition:
        print(f"FAILED: {message}")
        raise RuntimeError(message)
    print(f"PASSED: {message}")


def login(client, email, password):
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    check(response.status_code == 200, f"Login: {email}")
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def main():
    print("=== TrustVault Security Checks ===")

    admin_email = input("Admin email: ").strip()
    admin_password = getpass.getpass("Admin password: ")
    viewer_email = input("Viewer email: ").strip()
    viewer_password = getpass.getpass("Viewer password: ")

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        admin_headers = login(client, admin_email, admin_password)
        viewer_headers = login(client, viewer_email, viewer_password)

        # Existing private document owned by the Admin account.
        document_id = 2
        original_description = "Private document access test"

        # 1. Viewer must not access a private document.
        response = client.get(
            f"/documents/{document_id}",
            headers=viewer_headers,
        )
        check(response.status_code == 403, "Viewer blocked from private document")

        # 2. Confirm denied view was audited.
        logs = client.get(
            "/admin/audit-logs",
            headers=admin_headers,
            params={"limit": 50},
        )
        check(logs.status_code == 200, "Admin can retrieve audit logs")

        denied_found = any(
            item["actor_id"] == 3
            and item["document_id"] == document_id
            and item["action"] == "access_denied"
            for item in logs.json()["audit_logs"]
        )
        check(denied_found, "Unauthorized document view recorded in audit log")

        # 3. Grant EDIT permission.
        response = client.post(
            f"/documents/{document_id}/share",
            headers=admin_headers,
            json={
                "user_email": viewer_email,
                "permission": "edit",
            },
        )
        check(response.status_code == 200, "Owner grants EDIT permission")

        # 4. Viewer can edit document metadata.
        response = client.put(
            f"/documents/{document_id}",
            headers=viewer_headers,
            json={"description": "Edited by TrustVault security test"},
        )
        check(response.status_code == 200, "Viewer with EDIT permission can edit")

        # Restore original description.
        response = client.put(
            f"/documents/{document_id}",
            headers=admin_headers,
            json={"description": original_description},
        )
        check(response.status_code == 200, "Original document description restored")

        # 5. Revoke access.
        response = client.delete(
            f"/documents/{document_id}/share/3",
            headers=admin_headers,
        )
        check(response.status_code == 200, "Owner revokes Viewer permission")

        response = client.get(
            f"/documents/{document_id}",
            headers=viewer_headers,
        )
        check(response.status_code == 403, "Revoked Viewer access blocked immediately")

        # 6. Create a temporary document for deletion testing.
        response = client.post(
            "/documents/upload",
            headers=admin_headers,
            data={
                "category": "SecurityTest",
                "description": "Temporary automated deletion test",
            },
            files={
                "file": (
                    "trustvault-delete-test.txt",
                    b"Temporary TrustVault deletion test.",
                    "text/plain",
                )
            },
        )
        check(response.status_code == 201, "Temporary test document uploaded")

        temporary_id = response.json()["document"]["id"]

        # 7. Viewer cannot delete another user's document.
        response = client.delete(
            f"/documents/{temporary_id}",
            headers=viewer_headers,
        )
        check(response.status_code == 403, "Viewer cannot delete owner's document")

        # 8. Owner deletes the temporary document.
        response = client.delete(
            f"/documents/{temporary_id}",
            headers=admin_headers,
        )
        check(response.status_code == 200, "Owner can delete own document")

        # 9. Verify delete audit entry.
        logs = client.get(
            "/admin/audit-logs",
            headers=admin_headers,
            params={"limit": 50},
        )
        check(logs.status_code == 200, "Final audit log retrieval")

        delete_found = any(
    item["action"] == "delete"
    and item.get("metadata")
    and item["metadata"].get("deleted_document_id") == temporary_id
    for item in logs.json()["audit_logs"]
)
        check(delete_found, "Document deletion recorded in audit log")

    print("\n=== ALL SECURITY CHECKS PASSED ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nSecurity checks stopped: {error}")
        sys.exit(1)
