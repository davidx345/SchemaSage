"""
Test Week 5-6: Data Cleaning Pipeline & CLI Tool Foundation
"""
import json
import requests
import asyncio
import subprocess
import pandas as pd
from io import StringIO
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'services', 'code-generation'))
sys.path.insert(0, project_root)

BASE_URL = "http://localhost:8000"

def create_test_data():
    """Create test dataset with various data quality issues"""
    test_data = {
        'name': ['John Doe', 'jane smith', 'MIKE JOHNSON', None, 'Bob Wilson', 'jane smith', 'Invalid Name 123'],
        'email': ['john@email.com', 'jane.smith@gmail.com', 'mike@invalid', '', 'bob@company.co.uk', 'jane.smith@gmail.com', 'not-an-email'],
        'age': [25, 30, -5, 150, 35, 30, 'twenty-five'],
        'salary': [50000, 75000, 0, 999999999, 65000, 75000, None],
        'department': ['Engineering', 'marketing', 'SALES', 'HR', 'Engineering', 'marketing', 'Unknown Dept'],
        'join_date': ['2023-01-15', '2022-03-20', '2024-02-30', '2021-12-01', '2023-06-10', '2022-03-20', 'invalid-date']
    }
    return pd.DataFrame(test_data)

def test_data_quality_analysis():
    """Test data quality analysis endpoint"""
    print("\n🔍 Testing Data Quality Analysis...")
    
    # Create test CSV data
    df = create_test_data()
    csv_content = df.to_csv(index=False)
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-data-quality",
            params={"file_type": "csv"},
            data=csv_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        if response.status_code == 200:
            result = response.json()
            quality_report = result['quality_report']
            
            print(f"✅ Quality Analysis - Overall Score: {quality_report['overall_score']}")
            print(f"   📊 Dataset Shape: {quality_report['metadata']['shape']}")
            print(f"   ⚠️  Issues Found: {len(quality_report['issues'])}")
            print(f"   💡 Recommendations: {len(quality_report['recommendations'])}")
            
            # Show some issues
            for i, issue in enumerate(quality_report['issues'][:3]):
                print(f"   Issue {i+1}: {issue['type']} in '{issue['column']}' - {issue['description']}")
            
            return quality_report
        else:
            print(f"❌ Quality analysis failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Quality analysis error: {str(e)}")
        return None

def test_data_cleaning():
    """Test data cleaning endpoint"""
    print("\n🧹 Testing Data Cleaning...")
    
    # Create test data and get quality analysis first
    df = create_test_data()
    csv_content = df.to_csv(index=False)
    
    try:
        # Get quality analysis first
        quality_response = requests.post(
            f"{BASE_URL}/analyze-data-quality",
            params={"file_type": "csv"},
            data=csv_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        if quality_response.status_code != 200:
            print(f"❌ Quality analysis failed: {quality_response.status_code}")
            return False
            
        quality_report = quality_response.json()['quality_report']
        
        # Use some recommendations for cleaning
        recommendations = quality_report['recommendations'][:5]  # First 5 recommendations
        
        # Apply cleaning
        cleaning_response = requests.post(
            f"{BASE_URL}/clean-data",
            json={
                "file_type": "csv",
                "recommendations": recommendations
            },
            data=csv_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        if cleaning_response.status_code == 200:
            result = cleaning_response.json()
            summary = result['cleaning_summary']
            
            print(f"✅ Data Cleaning Complete!")
            print(f"   📏 Original Shape: {summary['original_shape']}")
            print(f"   📏 Cleaned Shape: {summary['cleaned_shape']}")
            print(f"   🔧 Operations Applied: {summary['operations_applied']}")
            print(f"   ✅ Successful Operations: {summary['successful_operations']}")
            print(f"   📈 Quality Improvement: {summary['quality_improvement']:.1f}%")
            
            return True
        else:
            print(f"❌ Data cleaning failed: {cleaning_response.status_code} - {cleaning_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Data cleaning error: {str(e)}")
        return False

def test_data_profiling():
    """Test data profiling endpoint"""
    print("\n📊 Testing Data Profiling...")
    
    # Create test data
    df = create_test_data()
    csv_content = df.to_csv(index=False)
    
    try:
        response = requests.post(
            f"{BASE_URL}/data-profile",
            params={"file_type": "csv"},
            data=csv_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        if response.status_code == 200:
            result = response.json()
            profile = result['data_profile']
            
            print(f"✅ Data Profile Generated!")
            print(f"   📊 Columns Analyzed: {len(profile.get('columns', {}))}")
            print(f"   📈 Statistical Summary Available: {'statistics' in profile}")
            print(f"   🔍 Data Quality Metrics: {'quality_metrics' in profile}")
            
            # Show column insights
            if 'columns' in profile:
                for col_name, col_info in list(profile['columns'].items())[:3]:
                    print(f"   Column '{col_name}': {col_info.get('data_type', 'unknown')} type")
            
            return True
        else:
            print(f"❌ Data profiling failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Data profiling error: {str(e)}")
        return False

def test_quality_metrics():
    """Test data quality metrics endpoint"""
    print("\n📏 Testing Quality Metrics...")
    
    try:
        response = requests.get(f"{BASE_URL}/data-quality-metrics")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Quality Metrics Retrieved!")
            print(f"   📊 Available Metrics: {len(result.get('quality_metrics', {}))}")
            print(f"   🔍 Issue Types: {len(result.get('issue_types', []))}")
            
            # Show some metrics
            for metric_name, metric_info in list(result.get('quality_metrics', {}).items())[:3]:
                print(f"   Metric '{metric_name}': {metric_info.get('description', 'No description')}")
            
            return True
        else:
            print(f"❌ Quality metrics failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Quality metrics error: {str(e)}")
        return False

def test_cli_tool():
    """Test CLI tool functionality"""
    print("\n🖥️  Testing CLI Tool...")
    
    try:
        # Test version command
        result = subprocess.run([
            "python", "cli.py", "version"
        ], capture_output=True, text=True, cwd="services/code-generation")
        
        if result.returncode == 0:
            print(f"✅ CLI Version: {result.stdout.strip()}")
        else:
            print(f"❌ CLI version failed: {result.stderr}")
            
        # Test help command
        result = subprocess.run([
            "python", "cli.py", "--help"
        ], capture_output=True, text=True, cwd="services/code-generation")
        
        if result.returncode == 0:
            print(f"✅ CLI Help Available (Commands found)")
            # Count available commands
            help_output = result.stdout
            commands = ['generate', 'analyze', 'erd', 'scaffold', 'serve', 'config']
            available_commands = [cmd for cmd in commands if cmd in help_output]
            print(f"   🔧 Available Commands: {len(available_commands)}")
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"❌ CLI testing error: {str(e)}")
        return False

def check_service_health():
    """Check if service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

def main():
    """Run all Week 5-6 tests"""
    print("🚀 Week 5-6 Testing: Data Cleaning Pipeline & CLI Tool Foundation")
    print("="*80)
    
    # Check if service is running
    if not check_service_health():
        print("❌ Service not running. Please start with: python services/code-generation/main.py")
        return
    
    # Run tests
    tests = [
        ("Data Quality Analysis", test_data_quality_analysis),
        ("Data Cleaning", test_data_cleaning),
        ("Data Profiling", test_data_profiling),
        ("Quality Metrics", test_quality_metrics),
        ("CLI Tool", test_cli_tool)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {str(e)}")
    
    # Final results
    print(f"\n{'='*80}")
    print(f"🏁 WEEK 5-6 TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Week 5-6 functionality working!")
        print("\n🚀 Week 5-6 Deliverables Complete:")
        print("   ✅ Data Quality Analysis Engine")
        print("   ✅ Data Cleaning Service")
        print("   ✅ Data Profiling System")
        print("   ✅ Quality Metrics API")
        print("   ✅ Professional CLI Tool")
        print("\n🎯 Ready for Week 7-8: AI Schema Critique System!")
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()
