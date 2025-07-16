# Error Handling Guide

This guide provides comprehensive information about error handling in the SmartClause API, including common error scenarios, troubleshooting steps, and best practices for error management.

## Table of Contents

- [Error Response Format](#error-response-format)
- [HTTP Status Codes](#http-status-codes)
- [Common Error Scenarios](#common-error-scenarios)
- [Service-Specific Errors](#service-specific-errors)
- [Error Handling Best Practices](#error-handling-best-practices)
- [Debugging and Troubleshooting](#debugging-and-troubleshooting)
- [Recovery Strategies](#recovery-strategies)

## Error Response Format

All SmartClause services follow consistent error response formats to ensure predictable error handling across the platform.

### Standard Error Response

```json
{
  "error": "Brief error description",
  "message": "Detailed error message",
  "timestamp": "2025-01-01T10:00:00.000Z",
  "path": "/api/endpoint",
  "status": 400
}
```

### Validation Error Response (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 6 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 6}
    }
  ]
}
```

### Authentication Error Response (401)

```json
{
  "error": "Authentication required",
  "message": "JWT token is missing or invalid",
  "timestamp": "2025-01-01T10:00:00.000Z"
}
```

## HTTP Status Codes

### Success Codes (2xx)

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, DELETE operations |
| 201 | Created | Successful resource creation (POST) |
| 204 | No Content | Successful operation with no response body |

### Client Error Codes (4xx)

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Invalid request data, malformed JSON |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist or access denied |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 413 | Payload Too Large | File size exceeds limits |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Description | Common Causes |
|------|-------------|---------------|
| 500 | Internal Server Error | Unexpected server errors |
| 502 | Bad Gateway | Service communication issues |
| 503 | Service Unavailable | Service temporarily down |
| 504 | Gateway Timeout | Service response timeout |

## Common Error Scenarios

### 1. Authentication Errors

#### Invalid Credentials
```json
{
  "error": "Invalid credentials",
  "message": "Username or password is incorrect"
}
```

**Causes:**
- Incorrect username/email or password
- Account deactivated or suspended
- Case sensitivity in username

**Solutions:**
```python
def handle_login_error(response):
    """Handle login authentication errors"""
    if response.status_code == 401:
        error_data = response.json()
        
        if "Invalid credentials" in error_data.get("error", ""):
            print("Please check your username and password")
            # Prompt user to re-enter credentials
            return "retry_login"
        elif "Account deactivated" in error_data.get("message", ""):
            print("Account is deactivated. Contact support.")
            return "contact_support"
    
    return "unknown_error"
```

#### Token Expired
```json
{
  "error": "Token expired",
  "message": "JWT token has expired, please re-authenticate"
}
```

**Solutions:**
```python
def handle_token_expiry(session, original_request_func, *args, **kwargs):
    """Automatically handle token expiration and retry"""
    response = original_request_func(*args, **kwargs)
    
    if response.status_code == 401:
        error_data = response.json()
        if "expired" in error_data.get("error", "").lower():
            # Re-authenticate
            login_success = re_authenticate(session)
            if login_success:
                # Retry original request
                return original_request_func(*args, **kwargs)
    
    return response

# Usage
response = handle_token_expiry(session, session.get, "http://localhost:8000/api/auth/profile")
```

### 2. Validation Errors

#### Required Field Missing
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solutions:**
```python
def handle_validation_errors(response):
    """Parse and handle validation errors"""
    if response.status_code == 422:
        validation_errors = response.json().get("detail", [])
        
        for error in validation_errors:
            field_path = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_type = error["type"]
            
            print(f"Validation Error in {field_path}: {message}")
            
            # Handle specific error types
            if error_type == "value_error.missing":
                print(f"  Solution: Provide a value for {field_path}")
            elif error_type == "value_error.email":
                print(f"  Solution: Provide a valid email address")
            elif "min_length" in error_type:
                min_length = error.get("ctx", {}).get("limit_value", "required")
                print(f"  Solution: Ensure minimum length of {min_length}")
        
        return validation_errors
    
    return None
```

#### File Size Too Large
```json
{
  "error": "File size exceeds maximum allowed size",
  "message": "Maximum file size is 50MB"
}
```

**Solutions:**
```python
def validate_file_before_upload(file_path, max_size_mb=50):
    """Validate file size before uploading"""
    import os
    
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise ValueError(f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
    
    return True

# Usage
try:
    validate_file_before_upload("large_document.pdf")
    # Proceed with upload
except ValueError as e:
    print(f"Cannot upload file: {e}")
    # Suggest file compression or splitting
```

### 3. Rate Limiting Errors

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again in 3600 seconds",
  "retry_after": 3600
}
```

**Solutions:**
```python
import time
import random

def handle_rate_limiting(response, max_retries=3):
    """Handle rate limiting with exponential backoff"""
    if response.status_code == 429:
        error_data = response.json()
        retry_after = error_data.get("retry_after", 60)
        
        print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
        
        for attempt in range(max_retries):
            wait_time = retry_after + random.uniform(0, 10)  # Add jitter
            time.sleep(wait_time)
            
            # Check rate limit status
            status_response = requests.get("http://localhost:8000/api/v1/rate-limit/status")
            if status_response.status_code == 200:
                limits = status_response.json()
                if limits["remaining"]["minute"] > 0:
                    print("Rate limit reset. Retrying...")
                    return True
            
            retry_after *= 2  # Exponential backoff
            print(f"Still rate limited. Attempt {attempt + 1}/{max_retries}")
        
        print("Max retries exceeded. Please try again later.")
        return False
    
    return True
```

### 4. Service Unavailable Errors

```json
{
  "error": "Service unavailable",
  "message": "Analyzer service is temporarily unavailable"
}
```

**Solutions:**
```python
def check_service_health(service_url):
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{service_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return health_data.get("status") == "healthy"
    except requests.RequestException:
        pass
    
    return False

def wait_for_service_recovery(service_url, max_wait_time=300):
    """Wait for service to recover"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        if check_service_health(service_url):
            print(f"Service {service_url} is back online")
            return True
        
        print("Service still unavailable, waiting...")
        time.sleep(30)
    
    print(f"Service {service_url} did not recover within {max_wait_time} seconds")
    return False

# Usage
if not check_service_health("http://localhost:8001"):
    print("Analyzer service is down")
    if wait_for_service_recovery("http://localhost:8001"):
        # Retry the operation
        pass
```

## Service-Specific Errors

### Backend Service Errors

#### Database Connection Error
```json
{
  "error": "Database connection failed",
  "message": "Unable to connect to PostgreSQL database"
}
```

#### Space Not Found
```json
{
  "error": "Space not found",
  "message": "Space with ID 'abc123' does not exist or access denied"
}
```

### Analyzer Service Errors

#### Document Processing Error
```json
{
  "detail": "Error processing document: Unsupported file format"
}
```

**Solutions:**
```python
def handle_document_processing_error(response):
    """Handle document processing errors"""
    if response.status_code == 400:
        error_msg = response.json().get("detail", "")
        
        if "Unsupported file format" in error_msg:
            print("Error: File format not supported")
            print("Supported formats: PDF, DOCX, TXT, RTF")
            return "unsupported_format"
        elif "File corrupted" in error_msg:
            print("Error: File appears to be corrupted")
            print("Solution: Try with a different file")
            return "corrupted_file"
        elif "Text extraction failed" in error_msg:
            print("Error: Could not extract text from document")
            print("Solution: Ensure document contains readable text")
            return "extraction_failed"
    
    return "unknown_error"
```

#### Embedding Generation Error
```json
{
  "detail": "Embedding generation failed: Model not available"
}
```

### Chat Service Errors

#### LLM Service Error
```json
{
  "detail": "LLM service error: Request timeout"
}
```

#### Memory Context Error
```json
{
  "detail": "Memory length must be between 1 and 50 messages"
}
```

## Error Handling Best Practices

### 1. Implement Retry Logic

```python
import time
import random
from functools import wraps

def retry_on_error(max_retries=3, backoff_factor=2, retry_codes=[500, 502, 503, 504]):
    """Decorator for automatic retry on specific error codes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_response = None
            
            for attempt in range(max_retries + 1):
                try:
                    response = func(*args, **kwargs)
                    
                    if response.status_code not in retry_codes:
                        return response
                    
                    last_response = response
                    
                    if attempt < max_retries:
                        wait_time = (backoff_factor ** attempt) + random.uniform(0, 1)
                        print(f"Retry {attempt + 1}/{max_retries} in {wait_time:.2f}s")
                        time.sleep(wait_time)
                        
                except requests.RequestException as e:
                    if attempt == max_retries:
                        raise e
                    
                    wait_time = (backoff_factor ** attempt) + random.uniform(0, 1)
                    print(f"Request failed, retry {attempt + 1}/{max_retries} in {wait_time:.2f}s")
                    time.sleep(wait_time)
            
            return last_response
        
        return wrapper
    return decorator

# Usage
@retry_on_error(max_retries=3)
def make_api_request(url, **kwargs):
    return requests.get(url, **kwargs)
```

### 2. Graceful Degradation

```python
class SmartClauseClientWithFallback:
    """Client with fallback mechanisms"""
    
    def __init__(self, primary_url, fallback_url=None):
        self.primary_url = primary_url
        self.fallback_url = fallback_url
        self.session = requests.Session()
    
    def analyze_document_with_fallback(self, document_id, file_content):
        """Try primary service, fallback to cached results or simplified analysis"""
        
        # Try primary analyzer service
        try:
            response = self.session.post(
                f"{self.primary_url}/analyze",
                files={"file": file_content},
                data={"id": document_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
                
        except requests.RequestException as e:
            print(f"Primary analyzer failed: {e}")
        
        # Try fallback service
        if self.fallback_url:
            try:
                response = self.session.post(
                    f"{self.fallback_url}/analyze",
                    files={"file": file_content},
                    data={"id": document_id},
                    timeout=60
                )
                
                if response.status_code == 200:
                    print("Using fallback analyzer service")
                    return response.json()
                    
            except requests.RequestException as e:
                print(f"Fallback analyzer failed: {e}")
        
        # Return basic analysis if all services fail
        print("All analyzer services failed, returning basic analysis")
        return {
            "document_id": document_id,
            "document_points": [],
            "total_points": 0,
            "analysis_timestamp": time.time(),
            "error": "Analysis services unavailable - upload saved for later processing"
        }
```

### 3. Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for service calls"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=requests.RequestException):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                print("Circuit breaker: Attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit breaker
            if self.state == CircuitState.HALF_OPEN:
                print("Circuit breaker: Recovery successful")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"Circuit breaker: OPEN after {self.failure_count} failures")
            
            raise e

# Usage
analyzer_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

def analyze_document_with_circuit_breaker(document_data):
    """Analyze document with circuit breaker protection"""
    try:
        return analyzer_circuit.call(
            requests.post,
            "http://localhost:8001/analyze",
            json=document_data,
            timeout=10
        )
    except Exception as e:
        print(f"Analyzer service call failed: {e}")
        return None
```

## Debugging and Troubleshooting

### 1. Enable Debug Logging

```python
import logging
import requests

# Enable debug logging for requests
logging.basicConfig(level=logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

def debug_api_call(response):
    """Log detailed information about API response"""
    print(f"\n=== API Call Debug Info ===")
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
    
    try:
        response_data = response.json()
        print(f"Response Body: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response Body (raw): {response.text[:500]}...")
    
    print(f"========================\n")
```

### 2. Health Check Monitoring

```python
def comprehensive_health_check():
    """Perform comprehensive health check of all services"""
    services = {
        "backend": "http://localhost:8000/api/v1/health",
        "analyzer": "http://localhost:8001/health", 
        "chat": "http://localhost:8002/api/v1/health"
    }
    
    health_status = {}
    
    for service_name, health_url in services.items():
        try:
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                health_status[service_name] = {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "details": health_data
                }
            else:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                }
                
        except requests.RequestException as e:
            health_status[service_name] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    # Print health summary
    print("=== Service Health Status ===")
    for service, status in health_status.items():
        print(f"{service:10}: {status['status'].upper()}")
        if status['status'] != 'healthy':
            print(f"           Error: {status.get('error', 'Unknown')}")
    
    return health_status
```

### 3. Network Connectivity Testing

```python
def test_network_connectivity():
    """Test network connectivity to all services"""
    import socket
    
    endpoints = [
        ("localhost", 8000, "Backend"),
        ("localhost", 8001, "Analyzer"), 
        ("localhost", 8002, "Chat"),
        ("localhost", 5432, "PostgreSQL")
    ]
    
    connectivity_results = {}
    
    for host, port, service in endpoints:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                connectivity_results[service] = "Connected"
            else:
                connectivity_results[service] = f"Connection failed (error {result})"
                
        except Exception as e:
            connectivity_results[service] = f"Error: {e}"
    
    print("=== Network Connectivity Test ===")
    for service, status in connectivity_results.items():
        print(f"{service:12}: {status}")
    
    return connectivity_results
```

## Recovery Strategies

### 1. Automatic Error Recovery

```python
class SmartClauseClientWithRecovery:
    """Client with automatic error recovery strategies"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.recovery_strategies = {
            401: self._recover_authentication,
            429: self._recover_rate_limit,
            503: self._recover_service_unavailable
        }
    
    def _recover_authentication(self, original_func, *args, **kwargs):
        """Recover from authentication errors"""
        print("Recovering from authentication error...")
        
        # Try to re-authenticate
        if hasattr(self, '_credentials'):
            login_result = self.login(*self._credentials)
            if login_result[0]:  # Success
                print("Re-authentication successful")
                return original_func(*args, **kwargs)
        
        print("Re-authentication failed")
        return None
    
    def _recover_rate_limit(self, original_func, *args, **kwargs):
        """Recover from rate limiting"""
        print("Recovering from rate limit...")
        
        # Check current rate limit status
        status_response = self.session.get(f"{self.base_url}/api/v1/rate-limit/status")
        
        if status_response.status_code == 200:
            limits = status_response.json()
            remaining = limits["remaining"]["minute"]
            
            if remaining > 0:
                print(f"Rate limit recovered ({remaining} requests remaining)")
                return original_func(*args, **kwargs)
            else:
                print("Rate limit still active, waiting...")
                time.sleep(60)  # Wait 1 minute
                return original_func(*args, **kwargs)
        
        return None
    
    def _recover_service_unavailable(self, original_func, *args, **kwargs):
        """Recover from service unavailable errors"""
        print("Recovering from service unavailable...")
        
        # Wait for service to become available
        if wait_for_service_recovery(self.base_url, max_wait_time=120):
            return original_func(*args, **kwargs)
        
        return None
    
    def robust_api_call(self, func, *args, **kwargs):
        """Make API call with automatic recovery"""
        max_recovery_attempts = 2
        
        for attempt in range(max_recovery_attempts + 1):
            try:
                response = func(*args, **kwargs)
                
                if response.status_code in self.recovery_strategies:
                    if attempt < max_recovery_attempts:
                        recovery_func = self.recovery_strategies[response.status_code]
                        recovered_response = recovery_func(func, *args, **kwargs)
                        
                        if recovered_response and recovered_response.status_code == 200:
                            return recovered_response
                        
                        print(f"Recovery attempt {attempt + 1} failed")
                    else:
                        print("Max recovery attempts reached")
                
                return response
                
            except requests.RequestException as e:
                if attempt < max_recovery_attempts:
                    print(f"Request failed, retrying... ({e})")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
        
        return None
```

### 2. Data Persistence During Outages

```python
import pickle
import os
from datetime import datetime

class OfflineDataManager:
    """Manage data persistence during service outages"""
    
    def __init__(self, cache_dir="offline_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def cache_for_later_processing(self, operation_type, data):
        """Cache operations for processing when services recover"""
        timestamp = datetime.now().isoformat()
        cache_entry = {
            "timestamp": timestamp,
            "operation": operation_type,
            "data": data,
            "status": "pending"
        }
        
        cache_file = os.path.join(
            self.cache_dir, 
            f"{operation_type}_{timestamp.replace(':', '-')}.pkl"
        )
        
        with open(cache_file, "wb") as f:
            pickle.dump(cache_entry, f)
        
        print(f"Operation cached for later processing: {cache_file}")
        return cache_file
    
    def process_cached_operations(self, api_client):
        """Process all cached operations when services are available"""
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        
        if not cache_files:
            print("No cached operations to process")
            return
        
        print(f"Processing {len(cache_files)} cached operations...")
        
        for cache_file in cache_files:
            cache_path = os.path.join(self.cache_dir, cache_file)
            
            try:
                with open(cache_path, "rb") as f:
                    cache_entry = pickle.load(f)
                
                operation = cache_entry["operation"]
                data = cache_entry["data"]
                
                print(f"Processing {operation} from {cache_entry['timestamp']}")
                
                # Process based on operation type
                if operation == "document_upload":
                    result = api_client.upload_document(data["space_id"], data["file_path"])
                elif operation == "chat_message":
                    result = api_client.chat(data["space_id"], data["message"])
                elif operation == "analysis_request":
                    result = api_client.get_analysis(data["document_id"])
                
                if result:
                    print(f"✅ Successfully processed {operation}")
                    os.remove(cache_path)
                else:
                    print(f"❌ Failed to process {operation}")
                    
            except Exception as e:
                print(f"Error processing {cache_file}: {e}")

# Usage
offline_manager = OfflineDataManager()

def upload_document_with_offline_support(client, space_id, file_path):
    """Upload document with offline fallback"""
    try:
        result = client.upload_document(space_id, file_path)
        return result
    except Exception as e:
        print(f"Upload failed: {e}")
        
        # Cache for later processing
        offline_manager.cache_for_later_processing("document_upload", {
            "space_id": space_id,
            "file_path": file_path
        })
        
        return {"status": "cached_for_later_processing"}
```

---

*This error handling guide covers the most common scenarios. For service-specific error details, refer to:*
- *[Backend API Documentation](./backend-api.md)*
- *[Analyzer API Documentation](./analyzer-api.md)*
- *[Chat API Documentation](./chat-api.md)*
- *[Authentication Guide](./authentication.md)* 