#!/usr/bin/env python3
"""
Simple test to verify the next_page_token method is implemented correctly.
This test doesn't require the full Airbyte CDK to be installed.
"""

import sys
import os

# Add the source_point directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source_point'))

def test_next_page_token_method_exists():
    """Test that the PointStream class has the next_page_token method"""
    try:
        # Import the class definition (this will work even without airbyte_cdk installed)
        import inspect
        import ast
        
        # Read the streams.py file and parse it
        with open('source_point/streams.py', 'r') as f:
            content = f.read()
        
        # Parse the AST to find the PointStream class and its methods
        tree = ast.parse(content)
        
        point_stream_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'PointStream':
                point_stream_class = node
                break
        
        if not point_stream_class:
            print("❌ PointStream class not found")
            return False
        
        # Check if next_page_token method exists
        next_page_token_method = None
        for item in point_stream_class.body:
            if isinstance(item, ast.FunctionDef) and item.name == 'next_page_token':
                next_page_token_method = item
                break
        
        if not next_page_token_method:
            print("❌ next_page_token method not found in PointStream class")
            return False
        
        print("✅ next_page_token method found in PointStream class")
        
        # Check the method signature
        args = [arg.arg for arg in next_page_token_method.args.args]
        expected_args = ['self', 'response']
        
        if args != expected_args:
            print(f"❌ next_page_token method has incorrect signature. Expected {expected_args}, got {args}")
            return False
        
        print("✅ next_page_token method has correct signature")
        
        # Check that it returns None (for no pagination)
        # Look for return statements
        return_statements = []
        for node in ast.walk(next_page_token_method):
            if isinstance(node, ast.Return):
                return_statements.append(node)
        
        if not return_statements:
            print("❌ next_page_token method has no return statement")
            return False
        
        # Check if it returns None
        for ret in return_statements:
            if isinstance(ret.value, ast.Constant) and ret.value.value is None:
                print("✅ next_page_token method returns None (correct for non-paginated API)")
                return True
            elif isinstance(ret.value, ast.NameConstant) and ret.value.value is None:  # Python < 3.8
                print("✅ next_page_token method returns None (correct for non-paginated API)")
                return True
        
        print("❌ next_page_token method doesn't return None")
        return False
        
    except Exception as e:
        print(f"❌ Error testing next_page_token method: {e}")
        return False

def test_class_inheritance():
    """Test that PointStream inherits from HttpStream"""
    try:
        with open('source_point/streams.py', 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'PointStream':
                if node.bases:
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'HttpStream':
                            print("✅ PointStream correctly inherits from HttpStream")
                            return True
        
        print("❌ PointStream doesn't inherit from HttpStream")
        return False
        
    except Exception as e:
        print(f"❌ Error checking class inheritance: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing next_page_token implementation")
    print("=" * 50)
    
    test1_passed = test_class_inheritance()
    test2_passed = test_next_page_token_method_exists()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! The next_page_token method is correctly implemented.")
        print("✅ The abstract method error should be resolved.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. The implementation needs to be fixed.")
        sys.exit(1)