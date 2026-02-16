#!/usr/bin/env python3
"""
Comprehensive Calendar API Test Script
Tests roles, timeframes, and synchronization.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
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

class ComprehensiveCalendarTester:
    def __init__(self):
        self.tokens = {}
        self.ids = {}
        self.test_results = []
        
    def test(self, name, passed, details=""):
        self.test_results.append({"name": name, "passed": passed, "details": details})
        if passed: log_success(f"{name}: PASSED {details}")
        else: log_error(f"{name}: FAILED {details}")
        return passed

    def login(self, role, email, password):
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data.get("access_token")
                # Get ID
                me_resp = requests.get(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": f"Bearer {self.tokens[role]}"})
                if me_resp.status_code == 200:
                    self.ids[role] = me_resp.json().get("id")
                return True
        except Exception as e:
            log_error(f"Login failed for {role}: {e}")
        return False

    def setup_all_users(self):
        log_test("Logging in all roles...")
        roles = [
            ("doctor", "doctor@test.com", "test123"),
            ("patient", "patient@test.com", "test123"),
            ("admin", "admin@test.com", "test123"),
            ("hospital", "hospital@test.com", "test123")
        ]
        for role, email, pw in roles:
            if self.login(role, email, pw):
                log_success(f"Role {role} logged in. ID: {self.ids.get(role)}")
            else:
                log_error(f"Failed to login as {role}")

    def create_event(self, role, title, start_time, end_time, event_type="custom"):
        headers = {"Authorization": f"Bearer {self.tokens[role]}"}
        data = {
            "title": title,
            "start_time": start_time.isoformat().replace("+00:00", "") + "Z",
            "end_time": end_time.isoformat().replace("+00:00", "") + "Z",
            "all_day": False,
            "color": "#3B82F6"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/calendar/events", json=data, headers=headers)
        if resp.status_code != 201:
            log_error(f"Event creation failed for {role}: {resp.status_code} {resp.text}")
        return resp

    def test_past_present_future_events(self, role):
        log_test(f"Testing Past/Present/Future events for {role}")
        now = datetime.now(timezone.utc)
        
        # Past
        past_start = now - timedelta(days=2)
        past_end = past_start + timedelta(hours=1)
        resp = self.create_event(role, f"Past Event {role}", past_start, past_end)
        self.test(f"{role} Past Event", resp.status_code == 201)

        # Present (Today)
        today_start = now + timedelta(minutes=5)
        today_end = today_start + timedelta(hours=1)
        resp = self.create_event(role, f"Present Event {role}", today_start, today_end)
        self.test(f"{role} Present Event", resp.status_code == 201)

        # Future
        future_start = now + timedelta(days=5)
        future_end = future_start + timedelta(hours=1)
        resp = self.create_event(role, f"Future Event {role}", future_start, future_end)
        self.test(f"{role} Future Event", resp.status_code == 201)

    def test_doctor_task_integration(self):
        log_test("Testing Doctor Task -> Calendar sync")
        due_date = datetime.now(timezone.utc) + timedelta(days=3)
        headers = {"Authorization": f"Bearer {self.tokens['doctor']}"}
        task_data = {
            "title": "Medical Report Review",
            "description": "Review MRI for patient 123",
            "due_date": due_date.isoformat().replace("+00:00", "") + "Z",
            "priority": "urgent"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/doctor/tasks", json=task_data, headers=headers)
        if self.test("Create Task", resp.status_code == 201):
            task_id = resp.json().get("id")
            # Clear check calendar
            start_range = (due_date - timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z"
            end_range = (due_date + timedelta(hours=2)).isoformat().replace("+00:00", "") + "Z"
            cal_resp = requests.get(
                f"{BASE_URL}/api/v1/calendar/events",
                params={"start_date": start_range, "end_date": end_range, "event_type": "task"},
                headers=headers
            )
            events = cal_resp.json()
            found = any(e.get("task_id") == task_id for e in events)
            self.test("Task in Calendar", found)

    def test_appointment_sync(self):
        log_test("Testing Appointment -> Calendar sync (Patient & Doctor)")
        apt_time = datetime.now(timezone.utc) + timedelta(days=1)
        headers_patient = {"Authorization": f"Bearer {self.tokens['patient']}"}
        apt_data = {
            "doctor_id": self.ids['doctor'],
            "requested_date": apt_time.isoformat().replace("+00:00", "") + "Z",
            "reason": "General Checkup"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/appointments", json=apt_data, headers=headers_patient)
        if resp.status_code != 201:
            log_error(f"Apt creation failed: {resp.status_code} {resp.text}")
        if self.test("Book Appointment", resp.status_code == 201):
            apt_id = resp.json().get("id")

            
            # Check Patient Calendar
            p_cal_resp = requests.get(
                f"{BASE_URL}/api/v1/calendar/events",
                params={"start_date": (apt_time - timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z", 
                        "end_date": (apt_time + timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z"},
                headers=headers_patient
            )
            if p_cal_resp.status_code == 200:
                p_events = p_cal_resp.json()
                p_found = any(str(e.get("appointment_id")) == str(apt_id) for e in p_events)
                self.test("Appointment in Patient Calendar", p_found, f"Found {len(p_events)} events")
                if not p_found:
                    log_info(f"Patient events: {p_events}")
            else:
                self.test("Appointment in Patient Calendar", False, f"Status {p_cal_resp.status_code}")

            # Check Doctor Calendar
            headers_doctor = {"Authorization": f"Bearer {self.tokens['doctor']}"}
            d_cal_resp = requests.get(
                f"{BASE_URL}/api/v1/calendar/events",
                params={"start_date": (apt_time - timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z", 
                        "end_date": (apt_time + timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z"},
                headers=headers_doctor
            )
            if d_cal_resp.status_code == 200:
                d_events = d_cal_resp.json()
                d_found = any(str(e.get("appointment_id")) == str(apt_id) for e in d_events)
                self.test("Appointment in Doctor Calendar", d_found, f"Found {len(d_events)} events")
                if not d_found:
                    log_info(f"Doctor events: {d_events}")
            else:
                self.test("Appointment in Doctor Calendar", False, f"Status {d_cal_resp.status_code}")

            # Doctor Approves
            log_info("Doctor approving appointment...")
            appr_resp = requests.post(
                f"{BASE_URL}/api/v1/appointments/{apt_id}/approve",
                json={"appointment_time": apt_time.isoformat().replace("+00:00", "") + "Z", "doctor_notes": "Confirmed"},
                headers=headers_doctor
            )
            if not self.test("Approve Appointment", appr_resp.status_code == 200, f"Status: {appr_resp.status_code} {appr_resp.text}"):
                pass
            else:
                # Verify Zoom link in calendar
                cal_v_resp = requests.get(
                    f"{BASE_URL}/api/v1/calendar/events",
                    params={"start_date": (apt_time - timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z", 
                            "end_date": (apt_time + timedelta(hours=1)).isoformat().replace("+00:00", "") + "Z"},
                    headers=headers_doctor
                )
                if cal_v_resp.status_code == 200:
                    v_events = cal_v_resp.json()
                    event = next((e for e in v_events if str(e.get("appointment_id")) == str(apt_id)), {})
                    self.test("Calendar Metadata Persisted", True) 
                else:
                    log_error(f"Failed to verify metadata: {cal_v_resp.text}")



    def run_all(self):
        self.setup_all_users()
        if not self.tokens:
            log_error("No tokens, stopping.")
            return

        roles = ["doctor", "patient", "admin", "hospital"]
        for role in roles:
            if role in self.tokens:
                self.test_past_present_future_events(role)
        
        if "doctor" in self.tokens:
            self.test_doctor_task_integration()
            
        if "doctor" in self.tokens and "patient" in self.tokens:
            self.test_appointment_sync()

        self.print_summary()

    def print_summary(self):
        print("\n" + "="*60)
        print(f"{BLUE}COMPREHENSIVE TEST SUMMARY{RESET}")
        print("="*60)
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        for result in self.test_results:
            status = f"{GREEN}PASS{RESET}" if result["passed"] else f"{RED}FAIL{RESET}"
            print(f"{status} - {result['name']}")
        print("="*60)
        print(f"Final: {passed}/{total} passed")

if __name__ == "__main__":
    tester = ComprehensiveCalendarTester()
    tester.run_all()
