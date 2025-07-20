#!/usr/bin/env python
"""
Test script to verify Swagger schema generation works correctly
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from drf_yasg.generators import OpenAPISchemaGenerator
from core.urls import urlpatterns

def test_swagger_generation():
    """Test that Swagger schema can be generated without errors"""
    try:
        # Create a mock request for schema generation
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        # Test schema generation
        generator = OpenAPISchemaGenerator(
            patterns=urlpatterns,
        )
        
        schema = generator.get_schema(request=request, public=True)
        
        # Check if schema was generated successfully
        if schema:
            print("✅ Swagger schema generation successful!")
            print(f"📊 Generated {len(schema.paths)} API endpoints")
            return True
        else:
            print("❌ Swagger schema generation failed - no schema returned")
            return False
            
    except Exception as e:
        print(f"❌ Swagger schema generation failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Swagger schema generation...")
    success = test_swagger_generation()
    
    if success:
        print("\n🎉 All tests passed! Swagger documentation should work correctly.")
    else:
        print("\n💥 Tests failed. Please check the errors above.")
        sys.exit(1) 