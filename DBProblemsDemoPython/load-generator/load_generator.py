#!/usr/bin/env python3
"""
Load Generator for Database Problems App

This script generates load against the database problems API to test performance,
logging, and monitoring. It simulates multiple users accessing the API concurrently
and provides real-time statistics.
"""

import requests
import time
import random
import threading
import argparse
import json
import os
import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Default settings from environment or hardcoded defaults
DEFAULT_HOST = os.environ.get("TARGET_HOST", "http://backend:5001")
DEFAULT_DURATION = int(os.environ.get("DEFAULT_DURATION", "300"))  # seconds
DEFAULT_USERS = int(os.environ.get("DEFAULT_USERS", "10"))
DEFAULT_THINK_TIME = (0.5, 3.0)  # min and max think time between requests

# Track stats
stats = {
    "requests": 0,
    "errors": 0,
    "total_time": 0,
    "min_time": float('inf'),
    "max_time": 0,
    "response_times": [],
    "timestamps": [],
    "endpoints": {},
    "status_codes": {},
    "errors_detail": []
}

# Track whether test is running
running = True

def make_request(session, host, endpoint, method="GET", data=None):
    """Make a request to the API and record stats"""
    global stats
    
    url = f"{host}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = session.get(url, timeout=10)
        elif method == "POST":
            response = session.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        duration = time.time() - start_time
        timestamp = time.time()
        
        # Update global stats
        stats["requests"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration) if stats["min_time"] != float('inf') else duration
        stats["max_time"] = max(stats["max_time"], duration)
        stats["response_times"].append(duration)
        stats["timestamps"].append(timestamp)
        
        # Update endpoint stats
        if endpoint not in stats["endpoints"]:
            stats["endpoints"][endpoint] = {
                "requests": 0,
                "errors": 0,
                "total_time": 0,
                "times": []
            }
        stats["endpoints"][endpoint]["requests"] += 1
        stats["endpoints"][endpoint]["total_time"] += duration
        stats["endpoints"][endpoint]["times"].append(duration)
        
        # Update status code stats
        status_code = str(response.status_code)
        if status_code not in stats["status_codes"]:
            stats["status_codes"][status_code] = 0
        stats["status_codes"][status_code] += 1
        
        if response.status_code >= 400:
            stats["errors"] += 1
            stats["endpoints"][endpoint]["errors"] += 1
            stats["errors_detail"].append({
                "timestamp": timestamp,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "message": response.text[:200]
            })
            print(f"Error: {response.status_code} - {response.text[:100]}")
            
        return response
        
    except Exception as e:
        stats["errors"] += 1
        if endpoint in stats["endpoints"]:
            stats["endpoints"][endpoint]["errors"] += 1
        
        error_message = str(e)
        stats["errors_detail"].append({
            "timestamp": time.time(),
            "endpoint": endpoint,
            "status_code": "Exception",
            "message": error_message
        })
        
        print(f"Request exception: {e}")
        return None

def user_session(user_id, host, duration, think_time):
    """Simulate a user session"""
    session = requests.Session()
    problems = None
    
    # Generate load until the test duration is reached
    end_time = time.time() + duration
    
    while time.time() < end_time and running:
        try:
            # First get the list of problems
            if not problems:
                response = make_request(session, host, "/api/problems")
                if response and response.status_code == 200:
                    problems = response.json().get("problems", [])
                
            # Get users
            make_request(session, host, "/api/users")
            
            # Randomly trigger a problem simulation
            if problems:
                problem_id = random.choice(problems)
                make_request(session, host, f"/api/problem/{problem_id}", method="POST")
            
            # Health check occasionally
            if random.random() < 0.2:  # 20% chance
                make_request(session, host, "/health")
            
            # Random think time
            sleep_time = random.uniform(think_time[0], think_time[1])
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Session exception for user {user_id}: {e}")
            time.sleep(1)  # Back off on errors

def print_stats(final=False):
    """Print current statistics"""
    global stats
    
    if stats["requests"] == 0:
        return
        
    avg_time = stats["total_time"] / stats["requests"] if stats["requests"] > 0 else 0
    error_rate = (stats["errors"] / stats["requests"]) * 100 if stats["requests"] > 0 else 0
    
    if final:
        print("\n=== Final Load Test Statistics ===")
    else:
        print("\n=== Current Load Test Statistics ===")
        
    print(f"Total requests: {stats['requests']}")
    print(f"Errors: {stats['errors']} ({error_rate:.2f}%)")
    print(f"Average response time: {avg_time:.4f} seconds")
    
    if stats["min_time"] != float('inf'):
        print(f"Min response time: {stats['min_time']:.4f} seconds")
    print(f"Max response time: {stats['max_time']:.4f} seconds")
    
    # Calculate percentiles if we have enough data
    if len(stats["response_times"]) > 10:
        sorted_times = sorted(stats["response_times"])
        p50 = sorted_times[len(sorted_times) // 2]
        p90 = sorted_times[int(len(sorted_times) * 0.9)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"50th percentile: {p50:.4f} seconds")
        print(f"90th percentile: {p90:.4f} seconds")
        print(f"99th percentile: {p99:.4f} seconds")
    
    if final:
        print("\n=== Endpoint Statistics ===")
        for endpoint, data in stats["endpoints"].items():
            if data["requests"] > 0:
                endpoint_avg = data["total_time"] / data["requests"]
                endpoint_error_rate = (data["errors"] / data["requests"]) * 100 if data["requests"] > 0 else 0
                print(f"{endpoint}: {data['requests']} requests, {endpoint_avg:.4f}s avg, {endpoint_error_rate:.2f}% errors")
        
        print("\n=== Status Code Distribution ===")
        for status, count in stats["status_codes"].items():
            percentage = (count / stats["requests"]) * 100
            print(f"Status {status}: {count} ({percentage:.2f}%)")

def stats_reporter(interval=5):
    """Periodically report stats during the test"""
    while running:
        print_stats()
        time.sleep(interval)

def generate_report():
    """Generate a report with graphs and save it to a file"""
    global stats
    
    if stats["requests"] == 0:
        print("No data to generate report")
        return
    
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Report timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"load_test_report_{timestamp}"
    
    # Create dataframe for response times
    if stats["timestamps"] and stats["response_times"]:
        df = pd.DataFrame({
            'timestamp': [datetime.datetime.fromtimestamp(ts) for ts in stats["timestamps"]],
            'response_time': stats["response_times"]
        })
        
        # Plot response times over time
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['response_time'])
        plt.title('Response Times During Load Test')
        plt.xlabel('Time')
        plt.ylabel('Response Time (seconds)')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(reports_dir / f"{report_name}_response_times.png")
        
        # Plot histogram of response times
        plt.figure(figsize=(12, 6))
        plt.hist(df['response_time'], bins=50)
        plt.title('Response Time Distribution')
        plt.xlabel('Response Time (seconds)')
        plt.ylabel('Count')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(reports_dir / f"{report_name}_histogram.png")
        
        # Calculate rolling average for smoothed response time
        if len(df) > 10:
            df['rolling_avg'] = df['response_time'].rolling(window=10).mean()
            
            plt.figure(figsize=(12, 6))
            plt.plot(df['timestamp'], df['rolling_avg'])
            plt.title('Smoothed Response Times (10-point rolling average)')
            plt.xlabel('Time')
            plt.ylabel('Response Time (seconds)')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(reports_dir / f"{report_name}_smoothed.png")
    
    # Create a text report with detailed statistics
    with open(reports_dir / f"{report_name}.txt", 'w') as f:
        f.write(f"=== Load Test Report: {timestamp} ===\n\n")
        
        f.write("=== General Statistics ===\n")
        f.write(f"Total requests: {stats['requests']}\n")
        error_rate = (stats["errors"] / stats["requests"]) * 100 if stats["requests"] > 0 else 0
        f.write(f"Errors: {stats['errors']} ({error_rate:.2f}%)\n")
        
        avg_time = stats["total_time"] / stats["requests"] if stats["requests"] > 0 else 0
        f.write(f"Average response time: {avg_time:.4f} seconds\n")
        
        if stats["min_time"] != float('inf'):
            f.write(f"Min response time: {stats['min_time']:.4f} seconds\n")
        f.write(f"Max response time: {stats['max_time']:.4f} seconds\n")
        
        # Calculate percentiles if we have enough data
        if len(stats["response_times"]) > 10:
            sorted_times = sorted(stats["response_times"])
            p50 = sorted_times[len(sorted_times) // 2]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            f.write(f"50th percentile: {p50:.4f} seconds\n")
            f.write(f"90th percentile: {p90:.4f} seconds\n")
            f.write(f"99th percentile: {p99:.4f} seconds\n")
        
        f.write("\n=== Endpoint Statistics ===\n")
        for endpoint, data in stats["endpoints"].items():
            if data["requests"] > 0:
                endpoint_avg = data["total_time"] / data["requests"]
                endpoint_error_rate = (data["errors"] / data["requests"]) * 100 if data["requests"] > 0 else 0
                f.write(f"{endpoint}: {data['requests']} requests, {endpoint_avg:.4f}s avg, {endpoint_error_rate:.2f}% errors\n")
        
        f.write("\n=== Status Code Distribution ===\n")
        for status, count in stats["status_codes"].items():
            percentage = (count / stats["requests"]) * 100
            f.write(f"Status {status}: {count} ({percentage:.2f}%)\n")
        
        if stats["errors_detail"]:
            f.write("\n=== Error Details ===\n")
            for i, error in enumerate(stats["errors_detail"]):
                f.write(f"Error {i+1}:\n")
                f.write(f"  Timestamp: {datetime.datetime.fromtimestamp(error['timestamp'])}\n")
                f.write(f"  Endpoint: {error['endpoint']}\n")
                f.write(f"  Status: {error['status_code']}\n")
                f.write(f"  Message: {error['message']}\n\n")
    
    print(f"\nReport generated: {reports_dir / report_name}.txt")
    if stats["timestamps"] and stats["response_times"]:
        print(f"Response time graphs saved in the reports directory")

def main():
    global running
    
    parser = argparse.ArgumentParser(description="Load generator for Database Problems API")
    parser.add_argument("--host", default=DEFAULT_HOST, help="API host URL")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help="Test duration in seconds")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of concurrent users")
    parser.add_argument("--min-think", type=float, default=DEFAULT_THINK_TIME[0], help="Minimum think time between requests")
    parser.add_argument("--max-think", type=float, default=DEFAULT_THINK_TIME[1], help="Maximum think time between requests")
    parser.add_argument("--report-only", action="store_true", help="Only generate a report from previous run data")
    
    args = parser.parse_args()
    
    if args.report_only:
        # Generate report from existing stats
        if os.path.exists("stats.json"):
            with open("stats.json", "r") as f:
                global stats
                stats = json.load(f)
            generate_report()
        else:
            print("No previous stats found")
        return
    
    print(f"Starting load test against {args.host}")
    print(f"Duration: {args.duration} seconds")
    print(f"Concurrent users: {args.users}")
    print(f"Think time range: {args.min_think}-{args.max_think} seconds")
    
    # Start stats reporter in a separate thread
    stats_thread = threading.Thread(target=stats_reporter)
    stats_thread.daemon = True
    stats_thread.start()
    
    try:
        # Start user sessions
        with ThreadPoolExecutor(max_workers=args.users) as executor:
            futures = []
            for i in range(args.users):
                futures.append(executor.submit(
                    user_session, 
                    i, 
                    args.host, 
                    args.duration, 
                    (args.min_think, args.max_think)
                ))
            
            # Wait for the test duration
            time.sleep(args.duration)
            running = False
            
            # Wait for all sessions to complete
            for future in futures:
                try:
                    future.result(timeout=5)
                except Exception as e:
                    print(f"Session exception: {e}")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Shutting down...")
        running = False
    
    # Final stats
    print_stats(final=True)
    
    # Save stats to file for later reporting
    with open("stats.json", "w") as f:
        json.dump(stats, f)
    
    # Generate report
    generate_report()

if __name__ == "__main__":
    main()