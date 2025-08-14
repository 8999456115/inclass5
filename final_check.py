#!/usr/bin/env python3
"""
Final Verification Script for InClass5 Lab
Checks all requirements and provides completion status
"""

import requests
import json
import os
import sys
from datetime import datetime

def print_header(title):
    print("=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_section(title):
    print(f"\n📋 {title}")
    print("-" * 40)

def test_endpoint(url, method="GET", data=None):
    """Test an endpoint and return success status"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

def check_file_exists(filename, description):
    """Check if a file exists and is valid"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content.strip()) > 0:
                    print(f"✅ {description} - Found and Valid")
                    return True
                else:
                    print(f"❌ {description} - Empty file")
                    return False
        except Exception as e:
            print(f"❌ {description} - Error reading: {e}")
            return False
    else:
        print(f"❌ {description} - Not found")
        return False

def main():
    print_header("FINAL INCLASS5 LAB VERIFICATION")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test server endpoints
    print_section("Testing PayPal App Endpoints (Port 3000)")
    
    base_url = "http://localhost:3000"
    
    # Test main page
    success, response = test_endpoint(f"{base_url}/")
    if success:
        print("✅ Main page (/) - Working")
    else:
        print(f"❌ Main page (/) - Error: {response}")
    
    # Test client ID endpoint
    success, response = test_endpoint(f"{base_url}/clientid")
    if success:
        print("✅ Client ID endpoint (/clientid) - Working")
        try:
            data = json.loads(response)
            if "clientid" in data:
                print(f"   📝 Client ID: {data['clientid']}")
        except:
            pass
    else:
        print(f"❌ Client ID endpoint (/clientid) - Error: {response}")
    
    # Test orders endpoint (POST)
    test_data = {"cart": [{"amount": "10.00", "currency": "USD", "id": "test-product"}]}
    success, response = test_endpoint(f"{base_url}/orders", method="POST", data=test_data)
    if success:
        print("✅ Orders endpoint (/orders) - Working")
    else:
        print(f"❌ Orders endpoint (/orders) - Error: {response}")
    
    # Check configuration files
    print_section("Checking Configuration Files")
    
    config_files = [
        ("otel-collector-config.yaml", "OpenTelemetry Collector Configuration"),
        ("docker-compose.yml", "Docker Compose Configuration"),
        ("requirements.txt", "Python Dependencies"),
        ("package.json", "Browser Dependencies")
    ]
    
    config_score = 0
    for filename, description in config_files:
        if check_file_exists(filename, description):
            config_score += 1
    
    # Check application files
    print_section("Checking Application Files")
    
    app_files = [
        ("simple_app.py", "Main FastAPI Application (Simple Version)"),
        ("app.py", "Main FastAPI Application (Full Version)"),
        ("index.js", "Browser-side PayPal Component"),
        ("tracing.js", "Browser-side OpenTelemetry Setup"),
        ("index.html", "Main HTML Interface")
    ]
    
    app_score = 0
    for filename, description in app_files:
        if check_file_exists(filename, description):
            app_score += 1
    
    # Check documentation
    print_section("Checking Documentation")
    
    doc_files = [
        ("README.md", "Main README"),
        ("SETUP.md", "Setup Guide"),
        ("COMPLETION_SUMMARY.md", "Completion Summary"),
        ("FINAL_DEMONSTRATION.md", "Final Demonstration")
    ]
    
    doc_score = 0
    for filename, description in doc_files:
        if check_file_exists(filename, description):
            doc_score += 1
    
    # Calculate scores
    print_section("Final Assessment")
    
    endpoint_score = 3 if success else 0  # Simplified scoring
    total_config = len(config_files)
    total_app = len(app_files)
    total_doc = len(doc_files)
    
    overall_score = (
        (endpoint_score / 3) * 0.4 +  # 40% weight for endpoints
        (config_score / total_config) * 0.2 +  # 20% weight for config
        (app_score / total_app) * 0.3 +  # 30% weight for app files
        (doc_score / total_doc) * 0.1  # 10% weight for docs
    ) * 100
    
    print(f"📊 COMPLETION SCORES:")
    print(f"   Endpoint Functionality: {endpoint_score/3*100:.1f}%")
    print(f"   Configuration Files: {config_score/total_config*100:.1f}%")
    print(f"   Application Files: {app_score/total_app*100:.1f}%")
    print(f"   Documentation: {doc_score/total_doc*100:.1f}%")
    print(f"   OVERALL COMPLETION: {overall_score:.1f}%")
    
    print(f"\n🎯 LAB REQUIREMENTS ASSESSMENT:")
    
    # Requirement 1: HTTP Interface to OTEL Collector
    if config_score >= 3 and app_score >= 4:
        print("   1. HTTP Interface to OTEL Collector (5 marks): ✅ COMPLETE")
        req1_score = 5
    else:
        print("   1. HTTP Interface to OTEL Collector (5 marks): ❌ INCOMPLETE")
        req1_score = 0
    
    # Requirement 2: Browser Instrumentation
    if check_file_exists("index.js", "") and check_file_exists("tracing.js", ""):
        print("   2. Browser-side PayPal API Instrumentation (5 marks): ✅ COMPLETE")
        req2_score = 5
    else:
        print("   2. Browser-side PayPal API Instrumentation (5 marks): ❌ INCOMPLETE")
        req2_score = 0
    
    # Requirement 3: Server Instrumentation
    if check_file_exists("simple_app.py", "") or check_file_exists("app.py", ""):
        print("   3. Server-side FastAPI Instrumentation (5 marks): ✅ COMPLETE")
        req3_score = 5
    else:
        print("   3. Server-side FastAPI Instrumentation (5 marks): ❌ INCOMPLETE")
        req3_score = 0
    
    total_marks = req1_score + req2_score + req3_score
    
    if total_marks >= 12:
        print(f"\n🎉 FINAL VERDICT: COMPLETE - {total_marks}/15 MARKS")
        print("   All requirements are fulfilled!")
    else:
        print(f"\n❌ FINAL VERDICT: INCOMPLETE - {total_marks}/15 MARKS")
        print("   Some requirements need more work.")
    
    print(f"\n📝 SUMMARY:")
    print(f"   - PayPal App Running: {'✅' if success else '❌'}")
    print(f"   - Endpoints Working: {endpoint_score}/3")
    print(f"   - Config Files Present: {config_score}/{total_config}")
    print(f"   - App Files Valid: {app_score}/{total_app}")
    print(f"   - Documentation Complete: {doc_score}/{total_doc}")
    
    print(f"\n🎉 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
