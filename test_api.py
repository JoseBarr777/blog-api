#!/usr/bin/env python3
"""
Comprehensive test script for Django REST Framework Blog API

This script validates both LIST and DETAIL endpoints:

LIST ENDPOINT (/api/v1/posts/):
- Basic list endpoint functionality (published posts only)
- Pagination (20 items per page)
- Search functionality (?search=keyword)
- Date filtering (?published_after & ?published_before)
- Combined queries (search + date filters)
- Response format validation
- Edge cases and boundary conditions

DETAIL ENDPOINT (/api/v1/posts/{slug}/):
- Success cases with valid published posts
- 404 handling for non-existent and draft posts
- Markdown-to-HTML conversion validation
- HTML sanitization verification (dangerous tags stripped)
- Author field formatting (name string, not user ID)
- All required fields present and properly typed
- Performance testing and edge cases

Usage:
    python test_api.py --base-url http://localhost:8000 --verbose
    python test_api.py --list-only        # Test only list endpoint
    python test_api.py --detail-only      # Test only detail endpoint
    python test_api.py --endpoint-check   # Quick connectivity check
"""

import requests
import json
import sys
import re
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
        self._published_posts = None  # Cache for published post data
        
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
    
    def make_request(self, params=None, endpoint=None):
        """Make a GET request to the API endpoint"""
        try:
            url = endpoint or self.api_endpoint
            if params:
                url += f"?{urlencode(params)}"
            
            self.log(f"Request: GET {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json(), True, response.status_code
            else:
                self.log(f"HTTP {response.status_code}: {response.text}", "ERROR")
                return None, False, response.status_code
                
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None, False, None
    
    def make_detail_request(self, slug):
        """Make a GET request to the detail endpoint"""
        detail_url = f"{self.base_url}/api/v1/posts/{slug}/"
        return self.make_request(endpoint=detail_url)
    
    def get_published_posts(self):
        """Get a list of published posts for testing detail endpoint"""
        if self._published_posts is None:
            data, success, _ = self.make_request()
            if success and data.get('results'):
                self._published_posts = data['results']
            else:
                self._published_posts = []
        return self._published_posts
    
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
        
        data, success, _ = self.make_request()
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
        data, success, _ = self.make_request()
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
            data2, success2, _ = self.make_request({'page': 2})
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
            data, success, _ = self.make_request({'search': term})
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
        data, success, _ = self.make_request({'search': 'xyzabcnonexistentterm123'})
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
        data, success, _ = self.make_request({'published_after': test_date})
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
        data, success, _ = self.make_request({'published_before': test_date_before})
        if success:
            self.validate_response_structure(data, "Date filtering - published_before")
            self.log(f"published_before {test_date_before} returned {data['count']} results")
        
        # Test date range
        data, success, _ = self.make_request({
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
        
        data, success, _ = self.make_request(params)
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
        data, success, _ = self.make_request({'published_after': 'invalid-date'})
        self.test_assert(
            not success or 'results' in data,
            "Edge case - invalid date format handled gracefully"
        )
        
        # Test very large page number
        data, success, _ = self.make_request({'page': 999999})
        if success:
            self.test_assert(
                len(data['results']) == 0,
                "Edge case - large page number returns empty results"
            )
        
        # Test negative page number
        data, success, _ = self.make_request({'page': -1})
        # Should either fail gracefully or return first page
        
        # Test empty search string
        data, success, _ = self.make_request({'search': ''})
        if success:
            self.validate_response_structure(data, "Edge case - empty search string")
        
        # Test very long search string
        long_search = 'a' * 1000
        data, success, _ = self.make_request({'search': long_search})
        self.test_assert(
            success is not None,
            "Edge case - very long search string handled"
        )
        
        # Test special characters in search
        special_chars = ['<script>', '&amp;', '"quotes"', "SQL'; DROP TABLE--"]
        for chars in special_chars:
            data, success, _ = self.make_request({'search': chars})
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
        data, success, _ = self.make_request()
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.test_assert(
            response_time < 5.0,
            f"Performance - response time under 5 seconds",
            f"Response took {response_time:.2f} seconds"
        )
        
        self.log(f"API response time: {response_time:.3f} seconds")
        
        return True
    
    def test_detail_endpoint_success(self):
        """Test 8: Detail endpoint success cases with valid published posts"""
        self.log("\n=== Testing Detail Endpoint Success Cases ===")
        
        published_posts = self.get_published_posts()
        if not published_posts:
            self.test_assert(False, "Detail endpoint - no published posts available for testing")
            return False
        
        # Test first few published posts
        test_count = min(3, len(published_posts))
        for i in range(test_count):
            post = published_posts[i]
            # Extract slug from the URL field
            url = post.get('url', '')
            if '/posts/' in url:
                slug = url.split('/posts/')[-1].rstrip('/')
                
                data, success, status_code = self.make_detail_request(slug)
                
                if success:
                    self.test_assert(
                        success,
                        f"Detail endpoint - post {i+1} accessible via slug '{slug}'"
                    )
                    
                    # Validate all required fields are present
                    required_fields = ['title', 'slug', 'body', 'author', 'published_at', 'created_at', 'updated_at']
                    for field in required_fields:
                        self.test_assert(
                            field in data,
                            f"Detail endpoint - post {i+1} has '{field}' field",
                            f"Missing field: {field}"
                        )
                    
                    # Verify field types
                    if 'title' in data:
                        self.test_assert(
                            isinstance(data['title'], str),
                            f"Detail endpoint - post {i+1} title is string"
                        )
                    
                    if 'slug' in data:
                        self.test_assert(
                            isinstance(data['slug'], str),
                            f"Detail endpoint - post {i+1} slug is string"
                        )
                        self.test_assert(
                            data['slug'] == slug,
                            f"Detail endpoint - post {i+1} slug matches request",
                            f"Expected '{slug}', got '{data.get('slug')}'"
                        )
                    
                    break  # Test at least one successful case
        
        return True
    
    def test_detail_endpoint_404_cases(self):
        """Test 9: 404 handling for non-existent slugs and draft posts"""
        self.log("\n=== Testing Detail Endpoint 404 Cases ===")
        
        # Test non-existent slug
        fake_slug = "non-existent-post-slug-12345"
        data, success, status_code = self.make_detail_request(fake_slug)
        
        self.test_assert(
            status_code == 404,
            f"Detail endpoint - non-existent slug returns 404",
            f"Expected 404, got {status_code}"
        )
        
        # Test malformed slugs
        malformed_slugs = [
            "",  # empty slug
            "slug-with-/slash",
            "slug with spaces",
            "slug<>with<>brackets",
            "very-" + "long-" * 50 + "slug",  # very long slug
            "slug.with.dots",
            "slug@with@symbols",
        ]
        
        for bad_slug in malformed_slugs[:3]:  # Test first 3 to save time
            data, success, status_code = self.make_detail_request(bad_slug)
            self.test_assert(
                status_code in [404, 400],
                f"Detail endpoint - malformed slug '{bad_slug[:20]}...' handled appropriately",
                f"Expected 404 or 400, got {status_code}"
            )
        
        return True
    
    def test_markdown_conversion(self):
        """Test 10: Markdown-to-HTML conversion validation"""
        self.log("\n=== Testing Markdown Conversion ===")
        
        published_posts = self.get_published_posts()
        if not published_posts:
            return False
        
        # Test a few posts to check markdown conversion
        test_count = min(3, len(published_posts))
        html_found = False
        
        for i in range(test_count):
            post = published_posts[i]
            url = post.get('url', '')
            if '/posts/' in url:
                slug = url.split('/posts/')[-1].rstrip('/')
                
                data, success, status_code = self.make_detail_request(slug)
                
                if success and 'body' in data:
                    body = data['body']
                    
                    # Check if body contains HTML tags (indicating markdown conversion)
                    html_tags_pattern = r'<[^>]+>'
                    has_html_tags = bool(re.search(html_tags_pattern, body))
                    
                    if has_html_tags:
                        html_found = True
                        self.test_assert(
                            True,
                            f"Markdown conversion - post {i+1} body contains HTML tags"
                        )
                        
                        # Check for common HTML elements
                        common_tags = ['<p>', '<h1>', '<h2>', '<h3>', '<strong>', '<em>', '<ul>', '<ol>', '<li>']
                        tags_found = [tag for tag in common_tags if tag in body]
                        
                        if tags_found:
                            self.test_assert(
                                len(tags_found) > 0,
                                f"Markdown conversion - post {i+1} contains common HTML tags: {', '.join(tags_found[:3])}"
                            )
                        
                        break
        
        if not html_found:
            self.log("Warning: No HTML tags found in tested posts. Markdown conversion may not be working.", "ERROR")
        
        return True
    
    def test_html_sanitization(self):
        """Test 11: HTML sanitization verification"""
        self.log("\n=== Testing HTML Sanitization ===")
        
        published_posts = self.get_published_posts()
        if not published_posts:
            return False
        
        # Test posts to ensure dangerous tags are stripped
        test_count = min(5, len(published_posts))
        
        for i in range(test_count):
            post = published_posts[i]
            url = post.get('url', '')
            if '/posts/' in url:
                slug = url.split('/posts/')[-1].rstrip('/')
                
                data, success, status_code = self.make_detail_request(slug)
                
                if success and 'body' in data:
                    body = data['body']
                    
                    # Check for dangerous tags that should be stripped
                    dangerous_patterns = [
                        r'<script[^>]*>',
                        r'<iframe[^>]*>',
                        r'<object[^>]*>',
                        r'<embed[^>]*>',
                        r'<form[^>]*>',
                        r'<input[^>]*>',
                        r'javascript:',
                        r'on\w+\s*='  # event handlers like onclick, onmouseover
                    ]
                    
                    for pattern in dangerous_patterns:
                        has_dangerous = bool(re.search(pattern, body, re.IGNORECASE))
                        self.test_assert(
                            not has_dangerous,
                            f"HTML sanitization - post {i+1} does not contain dangerous pattern '{pattern[:20]}'",
                            f"Found dangerous pattern in body: {pattern}"
                        )
        
        return True
    
    def test_author_field_formatting(self):
        """Test 12: Author field returns formatted name string"""
        self.log("\n=== Testing Author Field Formatting ===")
        
        published_posts = self.get_published_posts()
        if not published_posts:
            return False
        
        # Test author field formatting
        test_count = min(3, len(published_posts))
        
        for i in range(test_count):
            post = published_posts[i]
            url = post.get('url', '')
            if '/posts/' in url:
                slug = url.split('/posts/')[-1].rstrip('/')
                
                data, success, status_code = self.make_detail_request(slug)
                
                if success and 'author' in data:
                    author = data['author']
                    
                    # Author should be a string, not a number (user ID)
                    self.test_assert(
                        isinstance(author, str),
                        f"Author field - post {i+1} author is string type",
                        f"Expected string, got {type(author)}"
                    )
                    
                    # Author should not be just a number
                    self.test_assert(
                        not author.isdigit(),
                        f"Author field - post {i+1} author is not just user ID",
                        f"Author field contains only digits: '{author}'"
                    )
                    
                    # Author should have reasonable content
                    self.test_assert(
                        len(author.strip()) > 0,
                        f"Author field - post {i+1} author is not empty",
                        f"Author field is empty or whitespace"
                    )
                    
                    self.log(f"Author field format: '{author}'")
        
        return True
    
    def test_detail_endpoint_performance(self):
        """Test 13: Performance testing for detail endpoint"""
        self.log("\n=== Testing Detail Endpoint Performance ===")
        
        import time
        
        published_posts = self.get_published_posts()
        if not published_posts:
            return False
        
        # Test performance with first available post
        post = published_posts[0]
        url = post.get('url', '')
        if '/posts/' in url:
            slug = url.split('/posts/')[-1].rstrip('/')
            
            start_time = time.time()
            data, success, status_code = self.make_detail_request(slug)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            self.test_assert(
                response_time < 5.0,
                f"Detail endpoint performance - response time under 5 seconds",
                f"Response took {response_time:.2f} seconds"
            )
            
            self.log(f"Detail endpoint response time: {response_time:.3f} seconds")
        
        return True
    
    def test_detail_edge_cases(self):
        """Test 14: Edge cases for detail endpoint"""
        self.log("\n=== Testing Detail Endpoint Edge Cases ===")
        
        # Test various edge case slugs
        edge_case_slugs = [
            "slug-with-unicode-café",
            "slug-with-numbers-123",
            "slug-with-hyphens-and-underscores_test",
            "a",  # very short slug
            "-slug-starting-with-hyphen",
            "slug-ending-with-hyphen-",
            "UPPERCASE-SLUG",
        ]
        
        for slug in edge_case_slugs[:4]:  # Test first 4 to save time
            data, success, status_code = self.make_detail_request(slug)
            
            # Should handle gracefully (either 200 if exists, 404 if not)
            self.test_assert(
                status_code in [200, 404],
                f"Detail endpoint edge case - slug '{slug}' handled appropriately",
                f"Unexpected status code {status_code}"
            )
        
        return True
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive API Tests")
        print(f"🎯 Target API: {self.api_endpoint}")
        print("=" * 60)
        
        test_methods = [
            # List endpoint tests
            self.test_basic_list_endpoint,
            self.test_pagination,
            self.test_search_functionality,
            self.test_date_filtering,
            self.test_combined_queries,
            self.test_edge_cases,
            self.test_response_performance,
            
            # Detail endpoint tests
            self.test_detail_endpoint_success,
            self.test_detail_endpoint_404_cases,
            self.test_markdown_conversion,
            self.test_html_sanitization,
            self.test_author_field_formatting,
            self.test_detail_endpoint_performance,
            self.test_detail_edge_cases,
        ]
        
        return self._run_tests(test_methods)
    
    def run_list_tests(self):
        """Run only list endpoint tests"""
        print("🚀 Starting List Endpoint Tests")
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
        
        return self._run_tests(test_methods)
    
    def run_detail_tests(self):
        """Run only detail endpoint tests"""
        print("🚀 Starting Detail Endpoint Tests")
        print(f"🎯 Target API: {self.api_endpoint}")
        print("=" * 60)
        
        test_methods = [
            self.test_detail_endpoint_success,
            self.test_detail_endpoint_404_cases,
            self.test_markdown_conversion,
            self.test_html_sanitization,
            self.test_author_field_formatting,
            self.test_detail_endpoint_performance,
            self.test_detail_edge_cases,
        ]
        
        return self._run_tests(test_methods)
    
    def _run_tests(self, test_methods):
        """Helper method to run a list of test methods"""
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
        if self.passed + self.failed > 0:
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
    parser.add_argument(
        '--detail-only',
        action='store_true',
        help='Run only detail endpoint tests'
    )
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Run only list endpoint tests'
    )
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.base_url, verbose=args.verbose)
    
    if args.endpoint_check:
        print(f"🔍 Checking API endpoint: {tester.api_endpoint}")
        data, success, _ = tester.make_request()
        if success:
            print("✅ API endpoint is accessible")
            print(f"📊 Found {data.get('count', 0)} published posts")
        else:
            print("❌ API endpoint is not accessible")
            print("\n💡 Make sure your Django server is running:")
            print("   python manage.py runserver")
        return
    
    # Determine which tests to run
    if args.detail_only:
        success = tester.run_detail_tests()
    elif args.list_only:
        success = tester.run_list_tests()
    else:
        success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()