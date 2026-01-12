#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison script for different MkDocs multi-project documentation methods.

This script tests and compares three different approaches:
1. Symlinks (Method 1)
2. MkDocs Monorepo Plugin (Method 2)
3. File Copying with Build Script (Method 3)

It provides a detailed comparison of pros/cons, compatibility, and recommendations.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure stdout for UTF-8 on Windows
if platform.system() == 'Windows':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * len(text)}{Colors.ENDC}")


def check_system_info() -> Dict[str, str]:
    """Gather system information."""
    print_section("System Information")

    info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'python_version': platform.python_version(),
        'is_admin': False,
        'has_symlink': False,
        'git_version': 'Not installed',
        'mkdocs_version': 'Not installed',
    }

    # Check if running as admin (Windows) or root (Unix)
    if info['platform'] == 'Windows':
        try:
            import ctypes
            info['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            pass
    else:
        info['is_admin'] = os.geteuid() == 0

    # Check symlink capability
    try:
        test_dir = Path('test_symlink_check')
        test_dir.mkdir(exist_ok=True)
        test_link = test_dir / 'link'
        test_target = test_dir / 'target'
        test_target.mkdir(exist_ok=True)
        test_link.symlink_to(test_target)
        info['has_symlink'] = True
        test_link.unlink()
        test_target.rmdir()
        test_dir.rmdir()
    except (OSError, NotImplementedError):
        info['has_symlink'] = False

    # Check git version
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            info['git_version'] = result.stdout.strip().split()[-1]
    except FileNotFoundError:
        pass

    # Check mkdocs version
    try:
        result = subprocess.run(['mkdocs', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            info['mkdocs_version'] = result.stdout.strip().split()[-1]
    except FileNotFoundError:
        pass

    # Print info
    print(f"  Platform:         {info['platform']} {info['platform_release']}")
    print(f"  Python:           {info['python_version']}")
    print(f"  Admin/Root:       {Colors.OKGREEN if info['is_admin'] else Colors.WARNING}{info['is_admin']}{Colors.ENDC}")
    print(f"  Symlink Support:  {Colors.OKGREEN if info['has_symlink'] else Colors.FAIL}{info['has_symlink']}{Colors.ENDC}")
    print(f"  Git:              {info['git_version']}")
    print(f"  MkDocs:           {info['mkdocs_version']}")

    return info


def test_method1_symlinks(info: Dict[str, str]) -> Dict[str, any]:
    """Test Method 1: Symlinks."""
    print_section("Method 1: Symlinks")

    result = {
        'name': 'Symlinks',
        'supported': False,
        'tested': False,
        'errors': [],
        'pros': [
            'Simple configuration',
            'No build step needed',
            'Files stay in source repositories',
            'Changes reflected immediately',
        ],
        'cons': [
            'Windows requires admin or developer mode',
            'May not work with all CI/CD systems',
            'Git symlink handling varies by platform',
        ],
    }

    if not info['has_symlink']:
        result['errors'].append(
            'Symlink creation not supported on this system'
        )
        if info['platform'] == 'Windows':
            result['errors'].append(
                'Windows: Enable Developer Mode or run as Administrator'
            )
        print(f"{Colors.FAIL}  ✗ Symlinks NOT supported{Colors.ENDC}")
        return result

    # Try creating a test symlink
    test_dir = Path('test_method1')
    test_dir.mkdir(exist_ok=True)

    try:
        src = Path('projects/soliplex/docs')
        if src.exists():
            link = test_dir / 'soliplex'
            link.symlink_to(src.resolve(), target_is_directory=True)
            result['supported'] = True
            result['tested'] = True
            print(f"{Colors.OKGREEN}  ✓ Symlinks fully supported{Colors.ENDC}")

            # Check if we can read files through symlink
            test_file = link / 'overview.md'
            if test_file.exists():
                print(f"{Colors.OKGREEN}  ✓ Can read files through symlink{Colors.ENDC}")
            else:
                result['errors'].append('Cannot read files through symlink')

            link.unlink()
        else:
            result['errors'].append('Test directory projects/soliplex/docs not found')

    except Exception as e:
        result['errors'].append(f'Symlink test failed: {e}')
        print(f"{Colors.FAIL}  ✗ Symlink test failed: {e}{Colors.ENDC}")
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

    return result


def test_method2_monorepo() -> Dict[str, any]:
    """Test Method 2: MkDocs Monorepo Plugin."""
    print_section("Method 2: MkDocs Monorepo Plugin")

    result = {
        'name': 'MkDocs Monorepo Plugin',
        'supported': False,
        'tested': False,
        'plugin_installed': False,
        'errors': [],
        'pros': [
            'Designed for multi-repo documentation',
            'Automatic navigation merging',
            'Supports git submodules',
            'No manual file copying',
            'Links rewritten automatically',
        ],
        'cons': [
            'Requires plugin installation',
            'More complex configuration',
            'May need adjustments for .mdx files',
            'Additional dependency to maintain',
        ],
    }

    # Check if plugin is installed
    try:
        result_proc = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True
        )
        if 'mkdocs-monorepo-plugin' in result_proc.stdout:
            result['plugin_installed'] = True
            result['supported'] = True
            print(f"{Colors.OKGREEN}  ✓ mkdocs-monorepo-plugin is installed{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}  ⚠ mkdocs-monorepo-plugin not installed{Colors.ENDC}")
            print(f"    Install with: pip install mkdocs-monorepo-plugin")
            result['errors'].append('Plugin not installed')

    except Exception as e:
        result['errors'].append(f'Failed to check plugin: {e}')
        print(f"{Colors.FAIL}  ✗ Failed to check plugin: {e}{Colors.ENDC}")

    return result


def test_method3_copy_files() -> Dict[str, any]:
    """Test Method 3: Copy Files with Build Script."""
    print_section("Method 3: Copy Files with Build Script")

    result = {
        'name': 'Copy Files with Build Script',
        'supported': True,  # Always supported
        'tested': False,
        'errors': [],
        'pros': [
            'Most reliable across all platforms',
            'Full control over file organization',
            'Works with any CI/CD system',
            'Can handle special cases (convert .mdx, rename, etc.)',
            'No runtime dependencies',
        ],
        'cons': [
            'Requires build step before preview/deploy',
            'Need to maintain build script',
            'Temporary file duplication',
            'More complex workflow',
        ],
    }

    # Check if build-docs.py exists
    build_script = Path('scripts/build-docs.py')
    if not build_script.exists():
        result['errors'].append('build-docs.py not found')
        print(f"{Colors.FAIL}  ✗ Build script not found at {build_script}{Colors.ENDC}")
        return result

    # Try running the build script in dry-run/validate mode
    try:
        result_proc = subprocess.run(
            [sys.executable, str(build_script), '--validate-only', '--no-update'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result_proc.returncode == 0:
            result['tested'] = True
            print(f"{Colors.OKGREEN}  ✓ Build script validated successfully{Colors.ENDC}")
        else:
            result['errors'].append(f'Build script validation failed:\n{result_proc.stderr}')
            print(f"{Colors.WARNING}  ⚠ Build script validation had issues{Colors.ENDC}")

    except subprocess.TimeoutExpired:
        result['errors'].append('Build script timed out')
        print(f"{Colors.FAIL}  ✗ Build script timed out{Colors.ENDC}")
    except Exception as e:
        result['errors'].append(f'Failed to run build script: {e}')
        print(f"{Colors.FAIL}  ✗ Failed to run build script: {e}{Colors.ENDC}")

    return result


def generate_comparison_table(results: List[Dict[str, any]], info: Dict[str, str]):
    """Generate a comparison table of all methods."""
    print_header("Comparison Summary")

    # Overall compatibility
    print(f"{Colors.BOLD}Overall Compatibility:{Colors.ENDC}\n")

    for result in results:
        status = f"{Colors.OKGREEN}✓" if result['supported'] else f"{Colors.FAIL}✗"
        tested = f"(Tested: {'Yes' if result['tested'] else 'No'})"
        print(f"  {status} {result['name']:30s} {Colors.ENDC}{tested}")

    # Detailed comparison
    print(f"\n{Colors.BOLD}Detailed Comparison:{Colors.ENDC}\n")

    criteria = [
        ('Platform Independence', ['Medium', 'High', 'Very High']),
        ('Setup Complexity', ['Low', 'Medium', 'Medium']),
        ('Runtime Performance', ['Fast', 'Medium', 'Fast']),
        ('Maintenance Burden', ['Low', 'Medium', 'Medium']),
        ('CI/CD Compatibility', ['Medium', 'High', 'Very High']),
        ('Special File Support', ['Limited', 'Good', 'Excellent']),
    ]

    print(f"  {'Criteria':30s} {'Method 1':15s} {'Method 2':15s} {'Method 3':15s}")
    print(f"  {'-' * 75}")

    for criterion, values in criteria:
        print(f"  {criterion:30s} {values[0]:15s} {values[1]:15s} {values[2]:15s}")

    # Recommendations
    print_section("Recommendations")

    print(f"{Colors.BOLD}For your use case:{Colors.ENDC}\n")

    recommendation = None
    reasons = []

    if info['platform'] == 'Windows' and not info['has_symlink']:
        print(f"  {Colors.WARNING}⚠ Symlinks not available on this Windows system{Colors.ENDC}")
        reasons.append("Symlinks unavailable on Windows without admin/dev mode")

    if not any(r['plugin_installed'] for r in results if r['name'] == 'MkDocs Monorepo Plugin'):
        print(f"  {Colors.WARNING}⚠ Monorepo plugin not installed{Colors.ENDC}")
        reasons.append("Monorepo plugin requires installation")

    # Determine recommendation
    if results[2]['supported'] and results[2]['tested']:
        recommendation = "Method 3: Copy Files with Build Script"
        reasons.append("✓ Most reliable across platforms")
        reasons.append("✓ Works with periodic git submodule updates")
        reasons.append("✓ No broken links - all files physically present")
        reasons.append("✓ Can handle special cases (.mdx conversion, README handling)")
    elif results[1]['plugin_installed']:
        recommendation = "Method 2: MkDocs Monorepo Plugin"
        reasons.append("✓ Good for monorepo setups")
        reasons.append("⚠ May need testing with .mdx files")
    elif results[0]['supported']:
        recommendation = "Method 1: Symlinks"
        reasons.append("✓ Simplest approach")
        reasons.append("⚠ Platform compatibility concerns")

    if recommendation:
        print(f"\n  {Colors.OKGREEN}{Colors.BOLD}Recommended: {recommendation}{Colors.ENDC}\n")
        for reason in reasons:
            print(f"    {reason}")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}\n")
    print(f"  1. Review the comparison above")
    print(f"  2. Choose a method based on your requirements")
    print(f"  3. Run the appropriate implementation:")
    print(f"     - Method 3: python scripts/build-docs.py")
    print(f"     - Method 2: pip install mkdocs-monorepo-plugin (then configure)")
    print(f"  4. Update mkdocs.yml navigation")
    print(f"  5. Update index.md to reference all projects")


def main():
    """Main entry point."""
    print_header("MkDocs Multi-Project Documentation Method Comparison")

    # Gather system info
    info = check_system_info()

    # Test each method
    results = [
        test_method1_symlinks(info),
        test_method2_monorepo(),
        test_method3_copy_files(),
    ]

    # Generate comparison
    generate_comparison_table(results, info)

    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

    # Return success if at least one method works
    if any(r['supported'] for r in results):
        return 0
    else:
        print(f"{Colors.FAIL}No supported methods found!{Colors.ENDC}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
