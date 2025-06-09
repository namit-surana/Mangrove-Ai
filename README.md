# Regulatory Certification Search API

A FastAPI-based service that searches for regulatory certifications across multiple domains using the Perplexity AI API.

## Features

- Parallel processing of multiple domain searches
- Asynchronous API calls using aiohttp
- Comprehensive error handling and logging
- Health check endpoint
- Environment-based configuration

## Prerequisites

- Python 3.8+
- Perplexity AI API key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```
PERPLEXITY_API_KEY=your_api_key_here
```

## Running the Application

### Local Development

Run the application locally:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment on AWS EC2

1. Connect to your EC2 instance:
```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

2. Install Python and required packages:
```bash
sudo yum update -y
sudo yum install python3 python3-pip -y
python3 -m pip install -r requirements.txt
```

3. Create the `.env` file with your Perplexity API key

4. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For production, consider using a process manager like `systemd` or `supervisor` to keep the application running.

## API Usage

### Search Endpoint

Send a POST request to `/search` with a JSON body containing domains:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "domains": [
      "honey export to USA",
      "AI-based medical device compliance",
      "organic cosmetic certification"
    ]
  }'
```

### Health Check

Check the API health:
```bash
curl http://localhost:8000/health
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Error Handling

The API includes comprehensive error handling for:
- Invalid requests
- API timeouts
- Perplexity API errors
- Server errors

All errors are logged and returned with appropriate HTTP status codes.

## Security Considerations

- Never commit the `.env` file to version control
- Use HTTPS in production
- Consider implementing rate limiting
- Monitor API usage and logs 