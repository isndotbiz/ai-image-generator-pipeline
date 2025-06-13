#!/bin/bash

# Upload script template with Smartproxy integration
# Usage: ./upload.sh <file_path> [target_url]

set -e  # Exit on any error

# Configuration
FILE_PATH="$1"
TARGET_URL="${2:-https://example.com/upload}"  # Default target URL if not provided
SMARTPROXY_URL="${SMARTPROXY_URL:-}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [ -z "$FILE_PATH" ]; then
    print_error "Usage: $0 <file_path> [target_url]"
    print_error "Example: $0 ./myfile.zip https://api.example.com/upload"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    print_error "File not found: $FILE_PATH"
    exit 1
fi

# Build curl command
CURL_CMD="curl"
CURL_ARGS=(
    "-X" "POST"
    "-F" "file=@$FILE_PATH"
    "-H" "User-Agent: upload-script/1.0"
    "--progress-bar"
    "--fail"
    "--max-time" "300"  # 5 minute timeout
)

# Add Smartproxy configuration if SMARTPROXY_URL is set
if [ -n "$SMARTPROXY_URL" ]; then
    print_info "Using Smartproxy: $SMARTPROXY_URL"
    CURL_ARGS+=("--proxy" "$SMARTPROXY_URL")
    
    # Add proxy authentication if credentials are provided via environment variables
    if [ -n "$SMARTPROXY_USER" ] && [ -n "$SMARTPROXY_PASS" ]; then
        CURL_ARGS+=("--proxy-user" "$SMARTPROXY_USER:$SMARTPROXY_PASS")
        print_info "Using proxy authentication"
    fi
else
    print_warning "SMARTPROXY_URL not set, uploading directly"
fi

# Add target URL
CURL_ARGS+=("$TARGET_URL")

# Display upload information
print_info "Uploading file: $FILE_PATH"
print_info "Target URL: $TARGET_URL"
print_info "File size: $(du -h "$FILE_PATH" | cut -f1)"

# Execute upload
print_info "Starting upload..."
if "$CURL_CMD" "${CURL_ARGS[@]}"; then
    print_info "Upload completed successfully!"
else
    EXIT_CODE=$?
    print_error "Upload failed with exit code: $EXIT_CODE"
    
    # Provide helpful error messages based on common curl exit codes
    case $EXIT_CODE in
        6)
            print_error "Could not resolve host. Check your internet connection and target URL."
            ;;
        7)
            print_error "Failed to connect to host. Check if the target server is accessible."
            ;;
        22)
            print_error "HTTP error occurred. The server returned an error status."
            ;;
        28)
            print_error "Operation timeout. The upload took too long to complete."
            ;;
        *)
            print_error "See curl manual for exit code details: man curl"
            ;;
    esac
    
    exit $EXIT_CODE
fi

# Optional: Add webhook notification or logging
if [ -n "$WEBHOOK_URL" ]; then
    print_info "Sending notification to webhook..."
    curl -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"File uploaded successfully\", \"file\": \"$(basename "$FILE_PATH")\", \"timestamp\": \"$(date -Iseconds)\"}"
fi

