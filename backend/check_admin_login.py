
from getpass import getpass
import httpx

email = input("Admin email: ").strip().lower()
password = getpass("Admin password: ")

try:
    response = httpx.post(
        "http://127.0.0.1:8001/auth/login",
        data={
            "username": email,
            "password": password,
        },
        timeout=15,
    )

    print("\nHTTP status:", response.status_code)

    if response.status_code == 200:
        print("Admin login successful.")
        print("Token received:", bool(response.json().get("access_token")))
    else:
        print("Login response:", response.text[:500])

except Exception as error:
    print("Connection error:", str(error))
