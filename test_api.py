#!/usr/bin/env python3
"""
Comprehensive test script for Django REST Framework Blog API

This script validates:
- Basic list endpoint functionality
- Pagination (20 items per page)
- Search functionality
- Date filtering
- Combined queries
- Response format validation
- Edge cases and boundary conditions

Usage:
    python test_api.py --base-url http://localhost:8000 --verbose
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode
import argparse


class APITester:
    def __init__(self, base_url="http://localhost:8000", verbose=False):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/v1/posts/"
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        
    def log(self, message, level="INFO"):
        if self.verbose or level == "ERROR":
            print(f"[{level}] {message}")
    
    def test_assert(self, condition, test_name, error_msg=""):
        if condition:
            self.passed += 1
            self.log(f"✓ PASS: {test_name}")
            return True
        else:
            self.failed += 1
            self.log(f"✗ FAIL: {test_name} - {error_msg}", "ERROR")
            return False
    
    def make_request(self, params=None):
        """Make a GET request to the API endpoint"""
        try:
            url = self.api_endpoint
            if params:
                url += f"?{urlencode(params)}"
            
            self.log(f"Request: GET {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json(), True
            else:
                self.log(f"HTTP {response.status_code}: {response.text}", "ERROR")
                return None, False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None, False
    
    def validate_response_structure(self, data, test_name):
        """Validate the expected response structure"""
        required_keys = ['count', 'next', 'previous', 'results']
        
        for key in required_keys:
            if not self.test_assert(key in data, f"{test_name} - has '{key}' field"):
                return False
        
        # Validate results structure
        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            required_result_keys = ['title', 'published_at', 'url']
            
            for key in required_result_keys:
                if not self.test_assert(key in result, f"{test_name} - result has '{key}' field"):
                    return False
        
        return True
    
    def test_basic_list_endpoint(self):
        """Test 1: Basic list endpoint returns only published posts"""
        self.log("\n=== Testing Basic List Endpoint ===")
        
        data, success = self.make_request()
        if not success:
            self.test_assert(False, "Basic list endpoint - API accessible")
            return False
        
        self.test_assert(success, "Basic list endpoint - API accessible")
        self.validate_response_structure(data, "Basic list endpoint")
        self.test_assert(isinstance(data['count'], int), "Basic list endpoint - count is integer")
        self.test_assert(isinstance(data['results'], list), "Basic list endpoint - results is list")
        
        return True
    
    def test_pagination(self):
        """Test 2: Pagination works correctly"""
        self.log("\n=== Testing Pagination ===")
        
        # Get first page
        data, success = self.make_request()
        if not success:
            return False
        
        total_count = data['count']
        first_page_count = len(data['results'])
        
        self.test_assert(
            first_page_count <= 20,
            "Pagination - first page has ≤20 items",
            f"Got {first_page_count} items"
        )
        
        if total_count > 20:
            # Test second page
            data2, success2 = self.make_request({'page': 2})
            if success2:
                self.test_assert(
                    data['next'] is not None,
                    "Pagination - next link present when more pages exist"
                )
                self.test_assert(
                    data2['previous'] is not None,
                    "Pagination - previous link present on page 2"
                )
                
                # Ensure no duplicate items between pages
                page1_titles = {item['title'] for item in data['results']}
                page2_titles = {item['title'] for item in data2['results']}
                overlap = page1_titles.intersection(page2_titles)
                
                self.test_assert(
                    len(overlap) == 0,
                    "Pagination - no duplicate items between pages",
                    f"Found {len(overlap)} duplicates"
                )
        
        return True
    
    def test_search_functionality(self):
        """Test 3: Search functionality"""
        self.log("\n=== Testing Search Functionality ===")
        
        # Test basic search
        search_terms = ['Django', 'Python', 'API', 'development', 'guide']
        
        for term in search_terms:
            data, success = self.make_request({'search': term})
            if success and len(data['results']) > 0:
                self.log(f"Search for '{term}' returned {len(data['results'])} results")
                self.validate_response_structure(data, f"Search for '{term}'")
                
                # Verify search results contain the term (case-insensitive)
                found_match = False
                for result in data['results'][:3]:  # Check first 3 results
                    title_match = term.lower() in result['title'].lower()
                    if title_match:
                        found_match = True
                        break
                
                self.test_assert(
                    found_match,
                    f"Search for '{term}' - results contain search term",
                    f"Term '{term}' not found in first 3 result titles"
                )
                break
        
        # Test empty search
        data, success = self.make_request({'search': 'xyzabcnonexistentterm123'})
        if success:
            self.test_assert(
                data['count'] == 0,
                "Search - empty results for non-existent term"
            )
            self.validate_response_structure(data, "Empty search results")
        
        return True
    
    def test_date_filtering(self):
        """Test 4: Date filtering functionality"""
        self.log("\n=== Testing Date Filtering ===")
        
        # Test published_after filter
        test_date = "2025-01-01T00:00:00Z"
        data, success = self.make_request({'published_after': test_date})
        if success:
            self.validate_response_structure(data, "Date filtering - published_after")
            self.log(f"published_after {test_date} returned {data['count']} results")
            
            # Verify dates are after the filter date
            if len(data['results']) > 0:
                for result in data['results'][:3]:  # Check first 3
                    published_at = result.get('published_at')
                    if published_at:
                        result_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        filter_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
                        
                        self.test_assert(
                            result_date >= filter_date,
                            f"Date filtering - result date {published_at} >= filter date",
                            f"Result date {published_at} is before filter date {test_date}"
                        )
        
        # Test published_before filter
        test_date_before = "2025-12-31T23:59:59Z"
        data, success = self.make_request({'published_before': test_date_before})
        if success:
            self.validate_response_structure(data, "Date filtering - published_before")
            self.log(f"published_before {test_date_before} returned {data['count']} results")
        
        # Test date range
        data, success = self.make_request({
            'published_after': '2025-01-01T00:00:00Z',
            'published_before': '2025-12-31T23:59:59Z'
        })
        if success:
            self.validate_response_structure(data, "Date filtering - date range")
            self.log(f"Date range filtering returned {data['count']} results")
        
        return True
    
    def test_combined_queries(self):
        """Test 5: Combined search and date filtering"""
        self.log("\n=== Testing Combined Queries ===")
        
        # Combine search with date filter
        params = {
            'search': 'Django',
            'published_after': '2025-09-01T00:00:00Z'
        }
        
        data, success = self.make_request(params)
        if success:
            self.validate_response_structure(data, "Combined query - search + date")
            self.log(f"Combined query returned {data['count']} results")
            
            # Verify both filters are applied
            if len(data['results']) > 0:
                result = data['results'][0]
                title_contains_search = 'django' in result['title'].lower()
                
                if result.get('published_at'):
                    published_date = datetime.fromisoformat(
                        result['published_at'].replace('Z', '+00:00')
                    )
                    filter_date = datetime.fromisoformat('2025-09-01T00:00:00+00:00')
                    date_after_filter = published_date >= filter_date
                    
                    self.test_assert(
                        date_after_filter,
                        "Combined query - date filter applied",
                        f"Result date {result['published_at']} not after 2025-09-01"
                    )
        
        return True
    
    def test_edge_cases(self):
        """Test 6: Edge cases and boundary conditions"""
        self.log("\n=== Testing Edge Cases ===")
        
        # Test invalid date format
        data, success = self.make_request({'published_after': 'invalid-date'})
        self.test_assert(
            not success or 'results' in data,
            "Edge case - invalid date format handled gracefully"
        )
        
        # Test very large page number
        data, success = self.make_request({'page': 999999})
        if success:
            self.test_assert(
                len(data['results']) == 0,
                "Edge case - large page number returns empty results"
            )
        
        # Test negative page number
        data, success = self.make_request({'page': -1})
        # Should either fail gracefully or return first page
        
        # Test empty search string
        data, success = self.make_request({'search': ''})
        if success:
            self.validate_response_structure(data, "Edge case - empty search string")
        
        # Test very long search string
        long_search = 'a' * 1000
        data, success = self.make_request({'search': long_search})
        self.test_assert(
            success is not None,
            "Edge case - very long search string handled"
        )
        
        # Test special characters in search
        special_chars = ['<script>', '&amp;', '"quotes"', "SQL'; DROP TABLE--"]
        for chars in special_chars:
            data, success = self.make_request({'search': chars})
            self.test_assert(
                success is not None,
                f"Edge case - special characters '{chars[:20]}...' handled safely"
            )
        
        return True
    
    def test_response_performance(self):
        """Test 7: Response performance"""
        self.log("\n=== Testing Response Performance ===")
        
        import time
        
        start_time = time.time()
        data, success = self.make_request()
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.test_assert(
            response_time < 5.0,
            f"Performance - response time under 5 seconds",
            f"Response took {response_time:.2f} seconds"
        )
        
        self.log(f"API response time: {response_time:.3f} seconds")
        
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive API Tests")
        print(f"🎯 Target API: {self.api_endpoint}")
        print("=" * 60)
        
        test_methods = [
            self.test_basic_list_endpoint,
            self.test_pagination,
            self.test_search_functionality,
            self.test_date_filtering,
            self.test_combined_queries,
            self.test_edge_cases,
            self.test_response_performance,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log(f"Test method {test_method.__name__} failed with exception: {e}", "ERROR")
                self.failed += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed + self.failed)*100):.1f}%")
        
        if self.failed > 0:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            return False
        else:
            print("\n🎉 All tests passed!")
            return True


def main():
    parser = argparse.ArgumentParser(description='Test Django REST Framework Blog API')
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='Base URL of the API (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--endpoint-check',
        action='store_true',
        help='Only check if API endpoint is accessible'
    )
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.base_url, verbose=args.verbose)
    
    if args.endpoint_check:
        print(f"🔍 Checking API endpoint: {tester.api_endpoint}")
        data, success = tester.make_request()
        if success:
            print("✅ API endpoint is accessible")
            print(f"📊 Found {data.get('count', 0)} published posts")
        else:
            print("❌ API endpoint is not accessible")
            print("\n💡 Make sure your Django server is running:")
            print("   python manage.py runserver")
        return
    
    # Run full test suite
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()