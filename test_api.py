"""Test script for the Retail Saleswoman Chatbot API"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("=" * 60)
    print("Testing Retail Saleswoman Chatbot API")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Create session
    print("\n2. Create Session")
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={"price": 5000}
    )
    print(f"Status: {response.status_code}")
    session_data = response.json()
    print(f"Response: {json.dumps(session_data, indent=2)}")
    session_id = session_data["session_id"]
    
    # Test 3: Get session info
    print("\n3. Get Session Info")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 4: Send chat message
    print("\n4. Send Chat Message")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"message": "What are you selling?"}
    )
    print(f"Status: {response.status_code}")
    chat_response = response.json()
    print(f"Response: {json.dumps(chat_response, indent=2)}")
    
    # Test 5: Another chat message
    print("\n5. Send Another Message")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"message": "That sounds interesting. Tell me more about it."}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 6: Update price
    print("\n6. Update Price")
    response = requests.put(
        f"{BASE_URL}/sessions/{session_id}/price",
        json={"price": 4500}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 7: Chat after price update
    print("\n7. Chat After Price Update")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"message": "How much is it again?"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 8: Delete session
    print("\n8. Delete Session")
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 9: Try to access deleted session (should fail)
    print("\n9. Access Deleted Session (Should Fail)")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")
