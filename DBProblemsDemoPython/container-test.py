#!/usr/bin/env python3
"""
Container Test Script for OpenTelemetry Logging

This script helps diagnose connectivity and logging issues inside the container.
"""

import os
import sys
import time
import requests
import logging
import subprocess
import json

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test")

def check_network():
    """Check network connectivity to the collector"""
    print("\n=== Network Connectivity Check ===")
    
    # Get the collector endpoint from environment variables
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", 
                            os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", 
                                          "http://otel-collector:4318"))
    
    # Extract host and port
    if '//' in endpoint:
        host = endpoint.split('//')[1].split(':')[0]
    else:
        host = endpoint.split(':')[0]
    
    print(f"OpenTelemetry collector host: {host}")
    
    # Try ping
    print("\nPinging collector:")
    try:
        subprocess.run(["ping", "-c", "2", host], check=False, text=True)
    except Exception as e:
        print(f"Error pinging: {e}")
    
    # Try HTTP connection
    print("\nTesting HTTP connection:")
    url = endpoint
    if not url.startswith('http'):
        url = f"http://{url}"
    
    print(f"Testing connection to: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"HTTP status code: {response.status_code}")
        
        # Even a 404 is okay as it means the server is responding
        if response.status_code < 500:
            print("✅ Collector is responding to HTTP requests")
        else:
            print(f"❌ Collector returned error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error connecting to collector: {e}")

def test_direct_logging():
    """Test direct HTTP logs to the collector"""
    print("\n=== Direct HTTP Logging Test ===")
    
    # Get the collector endpoint
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", 
                            os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", 
                                          "http://otel-collector:4318"))
    
    # Make sure it includes /v1/logs
    if not endpoint.endswith('/v1/logs'):
        if endpoint.endswith('/'):
            endpoint += 'v1/logs'
        else:
            endpoint += '/v1/logs'
    
    print(f"Sending test log to: {endpoint}")
    
    # Create a simple log record
    log_data = {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "test-script"}},
                        {"key": "service.version", "value": {"stringValue": "1.0.0"}}
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {
                            "name": "test-script",
                            "version": "1.0"
                        },
                        "logRecords": [
                            {
                                "timeUnixNano": str(int(time.time() * 1e9)),
                                "severityNumber": 9,
                                "severityText": "INFO",
                                "body": {
                                    "stringValue": "Test log message from container"
                                },
                                "attributes": [
                                    {"key": "test.source", "value": {"stringValue": "container_script"}}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Send the log
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(endpoint, json=log_data, headers=headers, timeout=5)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code < 300:
            print("✅ Successfully sent test log to collector")
        else:
            print(f"❌ Error sending log: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error sending log: {e}")

def test_otel_sdk():
    """Test logging through the OpenTelemetry SDK"""
    print("\n=== OpenTelemetry SDK Test ===")
    
    try:
        # Try to import our logging configuration
        from logging_config import setup_otel_logging, log_to_otel, force_flush_logs
        
        print("✅ Successfully imported logging_config module")
        
        # Setup the logger provider
        logger_provider = setup_otel_logging()
        print(f"✅ Created logger provider: {logger_provider}")
        
        # Send a test log
        log_to_otel(logging.INFO, "Test log message via SDK", "test_script", 
                  {"test.method": "sdk_test"})
        print("✅ Sent test log via OpenTelemetry SDK")
        
        # Force flush logs
        result = force_flush_logs()
        print(f"✅ Forced flush of logs: {result}")
        
    except Exception as e:
        print(f"❌ Error testing OpenTelemetry SDK: {e}")
        import traceback
        traceback.print_exc()

def test_standard_logging():
    """Test standard Python logging"""
    print("\n=== Standard Logging Test ===")
    
    try:
        # Send logs through standard Python logging
        logger.info("Test INFO message via standard logging")
        logger.warning("Test WARNING message via standard logging")
        logger.error("Test ERROR message via standard logging")
        
        print("✅ Sent test logs via standard Python logging")
        
        # Try to force flush from logging_config
        try:
            from logging_config import force_flush_logs
            force_flush_logs()
            print("✅ Forced flush of logs")
        except:
            print("⚠️ Could not force flush logs")
            
    except Exception as e:
        print(f"❌ Error testing standard logging: {e}")

def main():
    print("\n🔍 OpenTelemetry Container Test Script")
    print("======================================")
    print(f"Running at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print relevant environment variables
    print("\n=== Environment Variables ===")
    for var in os.environ:
        if 'OTEL' in var:
            print(f"{var}: {os.environ[var]}")
    
    # Run tests
    check_network()
    test_direct_logging()
    test_otel_sdk()
    test_standard_logging()
    
    print("\n=== Test Summary ===")
    print("All tests completed. If tests show successful connections")
    print("but logs are still not appearing in your collector, the issue")
    print("might be with the collector's processing pipeline or exporters.")
    print("Check the collector's logs and configuration for more information.")

if __name__ == "__main__":
    main()