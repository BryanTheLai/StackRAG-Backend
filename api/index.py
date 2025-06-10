# AWS Lambda/Vercel Serverless handler
from mangum import Mangum
from src.main import app

# Create a handler for AWS Lambda/Vercel serverless functions
handler = Mangum(app)
