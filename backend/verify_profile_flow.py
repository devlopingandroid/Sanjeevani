"""
Real User Profile & Avatar Verification Script.

Tests the exact flow requested:
1. Register with Full Name = "Yash", Email = "yash_test_<ts>@example.com"
2. Confirm full_name is persisted and returned by /auth/register
3. Login with credentials
4. Call GET /api/v1/users/me -> Verify returns "Yash" and profile_image_url is null
5. Call PATCH /api/v1/users/me with Full Name = "Yash Goel"
6. Call GET /api/v1/users/me -> Verify returns "Yash Goel"
7. Upload real avatar image to POST /api/v1/users/me/avatar
8. Call GET /api/v1/users/me -> Verify returns updated profile_image_url
9. Fetch uploaded image via GET <profile_image_url> -> Verify 200 OK and valid image bytes
10. Simulate app restart: re-fetch GET /api/v1/users/me with stored token -> Verify "Yash Goel" and photo still present
"""
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    ts = int(time.time())
    email = f"yash_{ts}@example.com"
    password = "SecurePassword123!"

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        print(f"--- 1 & 2. Registering real user with Full Name = 'Yash', Email = '{email}' ---")
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Yash"},
        )
        print(f"Register status: {reg_resp.status_code}")
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        reg_data = reg_resp.json()
        print(f"Register response: {reg_data}")
        assert reg_data["full_name"] == "Yash", f"Expected 'Yash', got {reg_data.get('full_name')}"
        assert "password" not in reg_data
        assert "hashed_password" not in reg_data

        print("\n--- 3. Logging in ---")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        print(f"Login status: {login_resp.status_code}")
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("\n--- 4. Calling GET /api/v1/users/me ---")
        me_resp = client.get("/api/v1/users/me", headers=headers)
        print(f"GET /users/me status: {me_resp.status_code}")
        assert me_resp.status_code == 200, f"GET /users/me failed: {me_resp.text}"
        me_data = me_resp.json()
        print(f"Profile data: {me_data}")
        assert me_data["full_name"] == "Yash", f"Expected 'Yash', got {me_data.get('full_name')}"
        assert me_data["profile_image_url"] is None, f"Expected None, got {me_data.get('profile_image_url')}"

        print("\n--- 5, 6 & 7. Editing profile: PATCH full_name to 'Yash Goel' ---")
        patch_resp = client.patch(
            "/api/v1/users/me",
            json={"full_name": "Yash Goel"},
            headers=headers,
        )
        print(f"PATCH status: {patch_resp.status_code}")
        assert patch_resp.status_code == 200, f"PATCH failed: {patch_resp.text}"
        patch_data = patch_resp.json()
        print(f"Updated Profile: {patch_data}")
        assert patch_data["full_name"] == "Yash Goel", f"Expected 'Yash Goel', got {patch_data.get('full_name')}"

        print("\n--- 8. Simulating app restart / re-fetch after name change ---")
        restart_resp = client.get("/api/v1/users/me", headers=headers)
        assert restart_resp.json()["full_name"] == "Yash Goel"
        print("Persistent name verified across simulated restart: 'Yash Goel'")

        print("\n--- 9. Uploading real avatar photo (PNG) ---")
        sample_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"file": ("yash_avatar.png", sample_png, "image/png")}
        upload_resp = client.post(
            "/api/v1/users/me/avatar",
            files=files,
            headers=headers,
        )
        print(f"Avatar upload status: {upload_resp.status_code}")
        assert upload_resp.status_code == 200, f"Avatar upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        avatar_url = upload_data["profile_image_url"]
        print(f"Avatar persisted URL: {avatar_url}")
        assert avatar_url is not None and avatar_url.startswith("/uploads/avatars/"), f"Unexpected url: {avatar_url}"

        print("\n--- 10. Downloading uploaded avatar from static files endpoint ---")
        img_resp = client.get(avatar_url)
        print(f"Static file GET status: {img_resp.status_code}, content length: {len(img_resp.content)} bytes")
        assert img_resp.status_code == 200
        assert img_resp.content == sample_png, "Served image content does not match uploaded file!"

        print("\n--- 11. Final Verification: Simulated app restart session restore ---")
        final_me = client.get("/api/v1/users/me", headers=headers)
        final_data = final_me.json()
        print(f"Final session restore profile: {final_data}")
        assert final_data["full_name"] == "Yash Goel", f"Failed: name not persisted"
        assert final_data["profile_image_url"] == avatar_url, f"Failed: avatar url not persisted"

        print("\n>>> ALL VERIFICATION CHECKS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    run_verification()
