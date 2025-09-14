import requests
import json

# Base URL of the deployed backend
BASE_URL = "https://customer-care-backend-v2n0.onrender.com"

# Test data for authentication
TEST_USER = {
    "email": "admin@company.com",
    "password": "admin123"
}

def test_health_check():
    """Test the health check endpoint"""
    url = f"{BASE_URL}/api/health"
    try:
        response = requests.get(url)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print("✗ Health check failed")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def authenticate():
    """Authenticate and get JWT token"""
    url = f"{BASE_URL}/api/auth/login"
    try:
        response = requests.post(url, json=TEST_USER)
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("✓ Authentication successful")
            return token
        else:
            print(f"✗ Authentication failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None

def test_route(url, method='GET', token=None, data=None, expected_status=200):
    """Test a single route"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        print(f"  Sending token: {token[:20]}...")  # Debug: show first 20 chars of token

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            print(f"✗ Unsupported method: {method}")
            return False

        status_ok = response.status_code == expected_status
        print(f"{method} {url}: {response.status_code} {'✓' if status_ok else '✗'}")
        if not status_ok:
            print(f"  Response: {response.text[:200]}...")
        return status_ok
    except Exception as e:
        print(f"✗ Error testing {method} {url}: {e}")
        return False

def main():
    print("Testing Customer Care Backend Routes")
    print("=" * 50)

    # Test health check (no auth required)
    health_ok = test_health_check()
    print()

    # Authenticate
    token = authenticate()
    if not token:
        print("Cannot proceed without authentication token")
        return
    print()

    # Define routes to test (public routes)
    public_routes = [
        (f"{BASE_URL}/api/auth/login", "POST", {"email": "test@example.com", "password": "test"}, 401),  # Should fail with wrong credentials
        (f"{BASE_URL}/api/auth/register", "POST", {"name": "Test User", "email": "test@example.com", "password": "test123"}, 201),
    ]

    # Define routes to test (protected routes)
    protected_routes = [
        # Auth routes
        (f"{BASE_URL}/api/auth/profile", "GET", None, 200),

        # Tickets routes
        (f"{BASE_URL}/api/tickets", "GET", None, 200),
        (f"{BASE_URL}/api/tickets", "POST", {"title": "Test Ticket", "client_id": 1}, 201),  # May fail if client doesn't exist

        # Clients routes
        (f"{BASE_URL}/api/clients", "GET", None, 200),
        (f"{BASE_URL}/api/clients", "POST", {"name": "Test Client", "email": "testclient@example.com", "phone": "1234567890", "address": "Test Address"}, 201),

        # Users routes (admin only)
        (f"{BASE_URL}/api/users", "GET", None, 200),  # May fail if not admin
        (f"{BASE_URL}/api/users/technicians", "GET", None, 200),

        # Sites routes
        (f"{BASE_URL}/api/sites", "GET", None, 200),
        (f"{BASE_URL}/api/sites", "POST", {"name": "Test Site", "latitude": 40.7128, "longitude": -74.0060}, 201),

        # Routers routes
        (f"{BASE_URL}/api/routers", "GET", None, 200),

        # Analytics routes
        (f"{BASE_URL}/api/analytics/dashboard", "GET", None, 200),
    ]

    print("Testing public routes:")
    public_passed = 0
    for url, method, data, expected in public_routes:
        if test_route(url, method, None, data, expected):
            public_passed += 1
    print(f"Public routes: {public_passed}/{len(public_routes)} passed\n")

    print("Testing protected routes:")
    protected_passed = 0
    for url, method, data, expected in protected_routes:
        # First check if route exists (without auth)
        try:
            if method == 'GET':
                check_response = requests.get(url)
            elif method == 'POST':
                check_response = requests.post(url, json=data or {})
            else:
                check_response = requests.get(url)  # fallback
            if check_response.status_code == 404:
                print(f"{method} {url}: 404 ✗ (Route not found)")
                continue
            elif check_response.status_code == 401 and "Missing Authorization Header" in check_response.text:
                print(f"{method} {url}: Route exists and requires auth")
            else:
                print(f"{method} {url}: Unexpected response without auth: {check_response.status_code}")
        except Exception as e:
            print(f"{method} {url}: Error checking route existence: {e}")
            continue

        if test_route(url, method, token, data, expected):
            protected_passed += 1
    print(f"Protected routes: {protected_passed}/{len(protected_routes)} passed\n")

    total_passed = public_passed + protected_passed
    total_routes = len(public_routes) + len(protected_routes)

    print("=" * 50)
    print(f"Overall: {total_passed}/{total_routes} routes accessible")
    if total_passed == total_routes:
        print("✓ All tested routes are accessible!")
    else:
        print("✗ Some routes are not accessible. Check the output above for details.")

if __name__ == "__main__":
    main()
