import os

print("Fetching secrets...")
test_secret = os.getenv("TEST_SECRET")
if test_secret:
    print(f"Test Secret: {test_secret}")
else:
    print("Test Secret not found. Please set the TEST_SECRET environment variable.")