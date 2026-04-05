#!/usr/bin/env python3
"""
Complete authentication test script
Tests dashboard login and upload portal login
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.models import UserProfile

def test_prerana_auth():
    """Test prerana authentication"""
    print("\n" + "="*50)
    print("Testing Prerana Authentication")
    print("="*50)
    
    # Test authentication
    user = authenticate(username='prerana', password='prerana@123')
    
    if user is None:
        print("✗ FAILED: Authentication returned None")
        return False
    
    if user.username != 'prerana':
        print("✗ FAILED: Username mismatch")
        return False
    
    if not user.is_active:
        print("✗ FAILED: User is not active")
        return False
    
    # Check profile
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.get_role_display() != 'Leader':
            print("✗ FAILED: Role is not Leader")
            return False
    except UserProfile.DoesNotExist:
        print("✗ FAILED: UserProfile doesn't exist")
        return False
    
    print("✓ Prerana authentication: PASSED")
    print(f"  - Username: {user.username}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Role: {profile.get_role_display()}")
    return True

def test_dashboard_users():
    """Test dashboard user accounts"""
    print("\n" + "="*50)
    print("Testing Dashboard Users")
    print("="*50)
    
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    if users.count() == 0:
        print("✗ FAILED: No users found")
        return False
    
    print("✓ Users exist in database")
    
    # Show user list
    for user in users[:5]:
        try:
            profile = user.profile
            status = "✓" if user.is_active else "✗"
            print(f"  {status} {user.username}: {profile.get_role_display()}")
        except:
            print(f"  - {user.username}: (no profile)")
    
    if users.count() > 5:
        print(f"  ... and {users.count() - 5} more users")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("SALES DASHBOARD - COMPLETE AUTHENTICATION TEST")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Prerana Authentication", test_prerana_auth()))
    results.append(("Dashboard Users", test_dashboard_users()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED! Your login system is working correctly!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    exit(main())
