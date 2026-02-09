#!/usr/bin/env python3
"""
Anti-Pattern Detector - Example Usage

This script demonstrates how to use the Anti-Pattern Detector
to scan code for quality issues and anti-patterns.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.core.anti_pattern_detector import (
    AntiPatternDetector,
    Severity
)


def example_basic_scan():
    """Example 1: Basic directory scan"""
    print("=" * 70)
    print("Example 1: Basic Scan")
    print("=" * 70)
    
    detector = AntiPatternDetector()
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    
    print(f"\nScanned core directory")
    print(f"Found {len(violations)} violations")
    
    stats = detector.get_statistics(violations)
    print(f"\nSeverity breakdown:")
    for severity, count in stats['by_severity'].items():
        print(f"  {severity.upper()}: {count}")


def example_critical_issues():
    """Example 2: Find critical security issues"""
    print("\n" + "=" * 70)
    print("Example 2: Critical Security Issues")
    print("=" * 70)
    
    detector = AntiPatternDetector()
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    
    critical = detector.filter_by_severity(violations, Severity.CRITICAL)
    
    if critical:
        print(f"\nFound {len(critical)} CRITICAL issues:")
        for v in critical[:5]:
            print(f"\n  File: {v.file_path}:{v.line_number}")
            print(f"  Pattern: {v.pattern_name}")
            print(f"  Suggestion: {v.suggestion}")
            print(f"  Code: {v.line_content[:60]}...")
    else:
        print("\nNo critical issues found!")


def example_pattern_filtering():
    """Example 3: Filter by specific patterns"""
    print("\n" + "=" * 70)
    print("Example 3: Filter by Pattern")
    print("=" * 70)
    
    detector = AntiPatternDetector()
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    
    # Find only TODO and FIXME comments
    todos_fixmes = detector.filter_by_pattern(violations, ['todo', 'fixme'])
    
    print(f"\nFound {len(todos_fixmes)} TODO/FIXME comments")
    
    # Group by pattern
    by_pattern = {}
    for v in todos_fixmes:
        if v.pattern_name not in by_pattern:
            by_pattern[v.pattern_name] = []
        by_pattern[v.pattern_name].append(v)
    
    print(f"\nTODOs: {len(by_pattern.get('todo', []))}")
    print(f"FIXMEs: {len(by_pattern.get('fixme', []))}")


def example_file_analysis():
    """Example 4: Analyze specific files"""
    print("\n" + "=" * 70)
    print("Example 4: File Analysis")
    print("=" * 70)
    
    detector = AntiPatternDetector()
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    
    stats = detector.get_statistics(violations)
    
    print("\nTop 5 files with most violations:")
    for file_path, count in list(stats['top_files'].items())[:5]:
        print(f"\n  {file_path}")
        print(f"  Violations: {count}")
        
        # Show violations for this file
        file_violations = detector.filter_by_file(violations, file_path)
        by_severity = {}
        for v in file_violations:
            sev = v.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        print(f"  Breakdown: {by_severity}")


def example_custom_patterns():
    """Example 5: Custom patterns"""
    print("\n" + "=" * 70)
    print("Example 5: Custom Patterns")
    print("=" * 70)
    
    # Define custom patterns
    custom_patterns = {
        'example_function': {
            'regex': r'def\s+example_\w+\(',
            'severity': Severity.INFO,
            'suggestion': 'Consider giving this function a more descriptive name'
        },
        'temp_variable': {
            'regex': r'\b(temp|tmp)\s*=',
            'severity': Severity.LOW,
            'suggestion': 'Use more descriptive variable names'
        }
    }
    
    detector = AntiPatternDetector(custom_patterns=custom_patterns)
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    
    # Find violations from custom patterns
    custom_violations = [
        v for v in violations 
        if v.pattern_name in custom_patterns.keys()
    ]
    
    print(f"\nFound {len(custom_violations)} custom pattern violations")
    for v in custom_violations[:5]:
        print(f"\n  {v.pattern_name}: {v.file_path}:{v.line_number}")
        print(f"  Suggestion: {v.suggestion}")


def example_quality_gate():
    """Example 6: Quality gate check"""
    print("\n" + "=" * 70)
    print("Example 6: Quality Gate")
    print("=" * 70)
    
    detector = AntiPatternDetector()
    violations = detector.scan(Path("blackbox5/engine/core"), file_patterns=['*.py'])
    stats = detector.get_statistics(violations)
    
    # Define thresholds
    MAX_CRITICAL = 1
    MAX_HIGH = 10
    
    critical_count = stats['by_severity'].get('critical', 0)
    high_count = stats['by_severity'].get('high', 0)
    
    print(f"\nQuality Gate Results:")
    print(f"  Critical: {critical_count} (max: {MAX_CRITICAL})")
    print(f"  High: {high_count} (max: {MAX_HIGH})")
    
    if critical_count > MAX_CRITICAL:
        print(f"\n  FAILED: Too many critical issues!")
        return False
    
    if high_count > MAX_HIGH:
        print(f"\n  FAILED: Too many high issues!")
        return False
    
    print("\n  PASSED: Quality gate check passed!")
    return True


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("ANTI-PATTERN DETECTOR - EXAMPLES")
    print("=" * 70)
    
    try:
        example_basic_scan()
        example_critical_issues()
        example_pattern_filtering()
        example_file_analysis()
        example_custom_patterns()
        example_quality_gate()
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
