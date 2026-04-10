import requests
import sys
import json
from datetime import datetime

class NumStoreAPITester:
    def __init__(self, base_url="https://numstore.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_product_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_api_root(self):
        """Test API root endpoint"""
        print("\n🏠 Testing API root...")
        result = self.run_test(
            "API root endpoint",
            "GET",
            "",
            200
        )
        return result is not None

    def test_seed_data(self):
        """Initialize seed data"""
        print("\n🌱 Testing seed data initialization...")
        result = self.run_test(
            "Seed data initialization",
            "POST",
            "seed",
            200
        )
        return result is not None

    def test_products_api(self):
        """Test products endpoints"""
        print("\n📦 Testing products API...")
        
        # Get all products
        products = self.run_test(
            "Get all products",
            "GET",
            "products",
            200
        )
        
        if not products:
            return False
            
        # Test category filtering
        self.run_test(
            "Get products by category (ebook)",
            "GET",
            "products?category=ebook",
            200
        )
        
        # Get specific product
        if products and len(products) > 0:
            product_id = products[0]['id']
            self.run_test(
                "Get specific product",
                "GET",
                f"products/{product_id}",
                200
            )
            
            # Test invalid product ID
            self.run_test(
                "Get invalid product",
                "GET",
                "products/invalid-id",
                404
            )
        
        return True

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔐 Testing admin authentication...")
        
        # Test correct password
        result = self.run_test(
            "Admin login with correct password",
            "POST",
            "admin/login",
            200,
            data={"password": "admin123"}
        )
        
        if result and 'token' in result:
            self.admin_token = result['token']
            self.log_test("Admin token received", True)
        else:
            self.log_test("Admin token received", False, "No token in response")
            
        # Test incorrect password
        self.run_test(
            "Admin login with incorrect password",
            "POST",
            "admin/login",
            401,
            data={"password": "wrongpassword"}
        )
        
        return self.admin_token is not None

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        print("\n📊 Testing admin stats...")
        
        result = self.run_test(
            "Get admin stats",
            "GET",
            "admin/stats",
            200
        )
        
        if result:
            # Check required stats fields
            required_fields = ['total_revenue', 'total_sales', 'products_count', 'recent_transactions']
            for field in required_fields:
                if field in result:
                    self.log_test(f"Stats field: {field}", True)
                else:
                    self.log_test(f"Stats field: {field}", False, "Field missing")
        
        return result is not None

    def test_admin_products_crud(self):
        """Test admin products CRUD operations"""
        print("\n🛠️ Testing admin products CRUD...")
        
        # Get all products (admin view)
        products = self.run_test(
            "Get all products (admin)",
            "GET",
            "admin/products",
            200
        )
        
        # Create a test product
        test_product = {
            "name": "Test Product API",
            "description": "A test product for API testing",
            "price": 19.99,
            "category": "ebook",
            "image_url": "https://example.com/test.jpg",
            "file_size": "5 MB"
        }
        
        created_product = self.run_test(
            "Create test product",
            "POST",
            "admin/products",
            200,
            data=test_product
        )
        
        if not created_product:
            return False
            
        self.created_product_id = created_product['id']
        
        # Update the product
        update_data = {
            "name": "Updated Test Product API",
            "description": "Updated description",
            "price": 29.99,
            "category": "ebook",
            "image_url": "https://example.com/updated.jpg",
            "file_size": "10 MB"
        }
        
        self.run_test(
            "Update test product",
            "PUT",
            f"admin/products/{self.created_product_id}",
            200,
            data=update_data
        )
        
        # Test update non-existent product
        self.run_test(
            "Update non-existent product",
            "PUT",
            "admin/products/invalid-id",
            404,
            data=update_data
        )
        
        return True

    def test_payment_session_creation(self):
        """Test payment session creation"""
        print("\n💳 Testing payment session creation...")
        
        # First get a product
        products = self.run_test(
            "Get products for payment",
            "GET",
            "products",
            200
        )
        
        if not products or len(products) == 0:
            self.log_test("Payment session creation", False, "No products available")
            return False
            
        # Create payment session
        payment_data = {
            "product_id": products[0]['id'],
            "email": "test@example.com",
            "origin_url": "https://numstore.preview.emergentagent.com"
        }
        
        result = self.run_test(
            "Create payment session",
            "POST",
            "payment/create-session",
            200,
            data=payment_data
        )
        
        if result and 'checkout_url' in result and 'session_id' in result:
            self.log_test("Payment session created with checkout URL", True)
            session_id = result['session_id']
            
            # Test payment status check
            self.run_test(
                "Check payment status",
                "GET",
                f"payment/status/{session_id}",
                200
            )
        else:
            self.log_test("Payment session created with checkout URL", False, "Missing checkout_url or session_id")
        
        # Test invalid product ID
        invalid_payment_data = {
            "product_id": "invalid-id",
            "email": "test@example.com",
            "origin_url": "https://numstore.preview.emergentagent.com"
        }
        
        self.run_test(
            "Create payment session with invalid product",
            "POST",
            "payment/create-session",
            404,
            data=invalid_payment_data
        )
        
        return True

    def test_access_code_verification(self):
        """Test access code verification"""
        print("\n🔑 Testing access code verification...")
        
        # Test invalid access code
        self.run_test(
            "Verify invalid access code",
            "POST",
            "access/verify",
            404,
            data={"code": "INVALID"}
        )
        
        # Test empty code
        self.run_test(
            "Verify empty access code",
            "POST",
            "access/verify",
            404,
            data={"code": ""}
        )
        
        return True

    def test_access_code_resend(self):
        """Test access code resend"""
        print("\n📧 Testing access code resend...")
        
        # Get a product for testing
        products = self.run_test(
            "Get products for resend test",
            "GET",
            "products",
            200
        )
        
        if not products or len(products) == 0:
            self.log_test("Access code resend", False, "No products available")
            return False
        
        # Test resend for non-existent purchase
        resend_data = {
            "email": "nonexistent@example.com",
            "product_id": products[0]['id']
        }
        
        self.run_test(
            "Resend code for non-existent purchase",
            "POST",
            "access/resend",
            404,
            data=resend_data
        )
        
        # Test invalid product ID
        invalid_resend_data = {
            "email": "test@example.com",
            "product_id": "invalid-id"
        }
        
        self.run_test(
            "Resend code for invalid product",
            "POST",
            "access/resend",
            404,
            data=invalid_resend_data
        )
        
        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_product_id:
            self.run_test(
                "Delete test product",
                "DELETE",
                f"admin/products/{self.created_product_id}",
                200
            )
        
        # Test delete non-existent product
        self.run_test(
            "Delete non-existent product",
            "DELETE",
            "admin/products/invalid-id",
            404
        )

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting NumStore v2 API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)
        
        # Test sequence
        self.test_api_root()
        self.test_seed_data()
        self.test_products_api()
        self.test_admin_login()
        self.test_admin_stats()
        self.test_admin_products_crud()
        self.test_payment_session_creation()
        self.test_access_code_verification()
        self.test_access_code_resend()
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

def main():
    tester = NumStoreAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())