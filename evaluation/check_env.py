import os
print("DEBUG: Checking environment variables...")
print(f"TEST_EMAIL: {os.getenv('TEST_EMAIL', 'NOT SET')}")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')[:30]}..." if os.getenv('SUPABASE_URL') else "NOT SET")
print(f"SUPABASE_ANON_KEY: {'SET' if os.getenv('SUPABASE_ANON_KEY') else 'NOT SET'}")
print(f"TEST_PASSWORD: {'SET' if os.getenv('TEST_PASSWORD') else 'NOT SET'}")

# Try to load from dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("\nAfter loading .env:")
    print(f"TEST_EMAIL: {os.getenv('TEST_EMAIL', 'NOT SET')}")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')[:30]}..." if os.getenv('SUPABASE_URL') else "NOT SET")
    print(f"SUPABASE_ANON_KEY: {'SET' if os.getenv('SUPABASE_ANON_KEY') else 'NOT SET'}")
    print(f"TEST_PASSWORD: {'SET' if os.getenv('TEST_PASSWORD') else 'NOT SET'}")
except Exception as e:
    print(f"Error loading .env: {e}")
