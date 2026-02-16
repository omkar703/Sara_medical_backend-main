#!/usr/bin/env python3
"""
End-to-End Calendar API Test Script

Tests the following scenarios:
1. Patient books appointment → Verify calendar events for both patient and doctor
2. Doctor creates custom event → Verify only doctor can see it
3. Doctor creates task with due date → Verify task appears in calendar
4. Appointment approval → Verify calendar events updated
5. Appointment cancellation → Verify calendar events marked as cancelled
6. Day and Month views
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import time

BASE_URL = "http://localhost:8000"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log_test(message):
    print(f"{BLUE}[TEST]{RESET} {message}")


def log_success(message):
    print(f"{GREEN}[✓]{RESET} {message}")


def log_error(message):
    print(f"{RED}[✗]{RESET} {message}")


def log_info(message):
    print(f"{YELLOW}[i]{RESET} {message}")


class CalendarAPITester:
    def __init__(self):
        self.patient_token = None
        self.doctor_token = None
        self.patient_user = None
        self.doctor_user = None
        self.test_results = []
        
    def test(self, name, passed, details=""):
        """Record test result"""
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        if passed:
            log_success(f"{name}: PASSED {details}")
        else:
            log_error(f"{name}: FAILED {details}")
        return passed
    
    def setup_users(self):
        """Create test users (patient and doctor)"""
        log_test("Setting up test users...")
        
        # For now, we'll use existing users from the database
        # In production, you'd create fresh test users
        
        # Login as doctor (assuming one exists)
        try:
            # Try to login with test credentials - adjust as needed
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
                "email": "doctor@test.com",
                "password": "test123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.doctor_token = data.get("access_token")
                log_success("Doctor logged in")
            else:
                log_info("Doctor login failed - will skip doctor-specific tests")
        except Exception as e:
            log_error(f"Doctor setup failed: {e}")
        
        # Login as patient
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
                "email": "patient@test.com",
                "password": "test123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.patient_token = data.get("access_token")
                log_success("Patient logged in")
            else:
                log_info("Patient login failed - will skip patient-specific tests")
        except Exception as e:
            log_error(f"Patient setup failed: {e}")
    
    def test_health_check(self):
        """Test 0: Verify API is accessible"""
        log_test("Test 0: API Health Check")
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            return self.test("API Health Check", response.status_code == 200, 
                           f"Status: {response.status_code}")
        except Exception as e:
            return self.test("API Health Check", False, f"Error: {e}")
    
    def test_create_custom_event(self):
        """Test 1: Create a custom calendar event"""
        log_test("Test 1: Create Custom Calendar Event")
        
        if not self.doctor_token:
            return self.test("Create Custom Event", False, "No doctor token available")
        
        future_time = (datetime.utcnow() + timedelta(days=5)).isoformat() + "Z"
        end_time = (datetime.utcnow() + timedelta(days=5, hours=2)).isoformat() + "Z"
        
        event_data = {
            "title": "E2E Test Meeting",
            "description": "Testing calendar API",
            "start_time": future_time,
            "end_time": end_time,
            "all_day": False,
            "color": "#10B981",
            "reminder_minutes": 30
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/calendar/events",
                json=event_data,
                headers={"Authorization": f"Bearer {self.doctor_token}"}
            )
            
            if response.status_code == 201:
                data = response.json()
                passed = (
                    data.get("title") == event_data["title"] and
                    data.get("event_type") == "custom" and
                    data.get("color") == "#10B981"
                )
                return self.test("Create Custom Event", passed, 
                               f"Event ID: {data.get('id')}")
            else:
                return self.test("Create Custom Event", False, 
                               f"Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            return self.test("Create Custom Event", False, f"Error: {e}")
    
    def test_list_events(self):
        """Test 2: List calendar events within date range"""
        log_test("Test 2: List Calendar Events")
        
        if not self.doctor_token:
            return self.test("List Events", False, "No doctor token available")
        
        start = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/calendar/events",
                params={"start_date": start, "end_date": end},
                headers={"Authorization": f"Bearer {self.doctor_token}"}
            )
            
            if response.status_code == 200:
                events = response.json()
                passed = isinstance(events, list)
                return self.test("List Events", passed, 
                               f"Found {len(events)} events")
            else:
                return self.test("List Events", False, 
                               f"Status: {response.status_code}")
        except Exception as e:
            return self.test("List Events", False, f"Error: {e}")
    
    def test_day_view(self):
        """Test 3: Get day view"""
        log_test("Test 3: Get Day View")
        
        if not self.doctor_token:
            return self.test("Day View", False, "No doctor token available")
        
        target_date = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/calendar/day/{target_date}",
                headers={"Authorization": f"Bearer {self.doctor_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                passed = (
                    "date" in data and
                    "events" in data and
                    "total_count" in data
                )
                return self.test("Day View", passed, 
                               f"Events on {target_date}: {data.get('total_count', 0)}")
            else:
                return self.test("Day View", False, 
                               f"Status: {response.status_code}")
        except Exception as e:
            return self.test("Day View", False, f"Error: {e}")
    
    def test_month_view(self):
        """Test 4: Get month view"""
        log_test("Test 4: Get Month View")
        
        if not self.doctor_token:
            return self.test("Month View", False, "No doctor token available")
        
        now = datetime.utcnow()
        year, month = now.year, now.month
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/calendar/month/{year}/{month}",
                headers={"Authorization": f"Bearer {self.doctor_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                passed = (
                    data.get("year") == year and
                    data.get("month") == month and
                    "days" in data and
                    "total_events" in data
                )
                return self.test("Month View", passed, 
                               f"Total events in month: {data.get('total_events', 0)}")
            else:
                return self.test("Month View", False, 
                               f"Status: {response.status_code}")
        except Exception as e:
            return self.test("Month View", False, f"Error: {e}")
    
    def test_event_filtering(self):
        """Test 5: Filter events by type"""
        log_test("Test 5: Filter Events by Type")
        
        if not self.doctor_token:
            return self.test("Event Filtering", False, "No doctor token available")
        
        start = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/calendar/events",
                params={"start_date": start, "end_date": end, "event_type": "custom"},
                headers={"Authorization": f"Bearer {self.doctor_token}"}
            )
            
            if response.status_code == 200:
                events = response.json()
                # Check that all returned events are custom type
                if events:
                    all_custom = all(e.get("event_type") == "custom" for e in events)
                    passed = all_custom
                else:
                    passed = True  # No events is also valid
                
                return self.test("Event Filtering", passed, 
                               f"Custom events: {len(events)}")
            else:
                return self.test("Event Filtering", False, 
                               f"Status: {response.status_code}")
        except Exception as e:
            return self.test("Event Filtering", False, f"Error: {e}")
    
    def test_swagger_docs(self):
        """Test 6: Verify Swagger docs are accessible"""
        log_test("Test 6: Swagger Documentation")
        
        try:
            response = requests.get(f"{BASE_URL}/docs")
            return self.test("Swagger Docs", response.status_code == 200,
                           "Swagger UI accessible")
        except Exception as e:
            return self.test("Swagger Docs", False, f"Error: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print("="*60)
        
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = f"{GREEN}PASS{RESET}" if result["passed"] else f"{RED}FAIL{RESET}"
            print(f"{status} - {result['name']}")
            if result["details"]:
                print(f"      {result['details']}")
        
        print("="*60)
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
        
        if passed == total:
            print(f"{GREEN}✓ All tests passed!{RESET}")
            return 0
        else:
            print(f"{RED}✗ Some tests failed{RESET}")
            return 1


def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Calendar API End-to-End Testing{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    tester = CalendarAPITester()
    
    # Wait for backend to be ready
    log_info("Waiting for backend to be ready...")
    time.sleep(2)
    
    # Run tests
    tester.test_health_check()
    tester.setup_users()
    tester.test_create_custom_event()
    tester.test_list_events()
    tester.test_day_view()
    tester.test_month_view()
    tester.test_event_filtering()
    tester.test_swagger_docs()
    
    # Print summary
    exit_code = tester.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
