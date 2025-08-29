#!/usr/bin/env python3
"""
LUXORANOVA BRAIN - Anaconda Environment Intelligence System
"""

import os
import json
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LuxoranovaBrain')

@dataclass
class EnvironmentInfo:
    """Data class to store environment information"""
    name: str
    path: Path
    python_version: str
    packages: Dict[str, str]  # package_name: version
    size: int
    last_used: str
    is_active: bool

@dataclass
class PackageInfo:
    """Data class to store package information"""
    name: str
    version: str
    dependencies: Set[str]
    size: int
    is_core: bool

class AnacondaScanner:
    """Scanner for Anaconda environments and packages"""
    
    def __init__(self, anaconda_path: str = "D:/ANACONDA"):
        self.anaconda_path = Path(anaconda_path)
        self.environments: Dict[str, EnvironmentInfo] = {}
        self.packages: Dict[str, PackageInfo] = {}
        
    def scan_environments(self) -> Dict[str, EnvironmentInfo]:
        """Scan all Anaconda environments"""
        logger.info("Scanning Anaconda environments...")
        
        try:
            # Get list of environments using conda command
            result = subprocess.run(
                ['conda', 'env', 'list', '--json'],
                capture_output=True,
                text=True
            )
            env_data = json.loads(result.stdout)
            
            for env_path in env_data.get('envs', []):
                env_path = Path(env_path)
                env_name = env_path.name
                
                # Get environment details
                env_info = self._get_environment_info(env_path)
                self.environments[env_name] = env_info
                
                logger.info(f"Found environment: {env_name}")
                
        except Exception as e:
            logger.error(f"Error scanning environments: {str(e)}")
            
        return self.environments
    
    def _get_environment_info(self, env_path: Path) -> EnvironmentInfo:
        """Get detailed information about an environment"""
        try:
            # Get package list
            result = subprocess.run(
                ['conda', 'list', '--json', '--prefix', str(env_path)],
                capture_output=True,
                text=True
            )
            packages = {
                pkg['name']: pkg['version']
                for pkg in json.loads(result.stdout)
            }
            
            # Get Python version
            python_version = packages.get('python', 'unknown')
            
            # Get environment size
            size = sum(
                f.stat().st_size
                for f in env_path.rglob('*')
                if f.is_file()
            )
            
            # Check if environment is active
            is_active = os.environ.get('CONDA_DEFAULT_ENV') == env_path.name
            
            # Get last used time (based on most recent file modification)
            last_used = max(
                (f.stat().st_mtime
                 for f in env_path.rglob('*')
                 if f.is_file()),
                default=0
            )
            
            return EnvironmentInfo(
                name=env_path.name,
                path=env_path,
                python_version=python_version,
                packages=packages,
                size=size,
                last_used=str(last_used),
                is_active=is_active
            )
            
        except Exception as e:
            logger.error(f"Error getting environment info: {str(e)}")
            return None

class DependencyAnalyzer:
    """Analyzes package dependencies and relationships"""
    
    def __init__(self, scanner: AnacondaScanner):
        self.scanner = scanner
        self.dependency_graph: Dict[str, Set[str]] = {}
        
    def build_dependency_graph(self):
        """Build a graph of package dependencies"""
        logger.info("Building dependency graph...")
        
        for env_name, env_info in self.scanner.environments.items():
            try:
                # Get detailed package info including dependencies
                result = subprocess.run(
                    ['conda', 'list', '--json', '--prefix', str(env_info.path)],
                    capture_output=True,
                    text=True
                )
                packages = json.loads(result.stdout)
                
                for pkg in packages:
                    name = pkg['name']
                    if name not in self.dependency_graph:
                        self.dependency_graph[name] = set()
                    
                    # Add dependencies
                    if 'depends' in pkg:
                        for dep in pkg['depends']:
                            # Extract package name from dependency specification
                            dep_name = dep.split()[0]
                            self.dependency_graph[name].add(dep_name)
                            
            except Exception as e:
                logger.error(f"Error building dependency graph: {str(e)}")

class LuxoranovaBrain:
    """Main brain class coordinating all analysis and optimization"""
    
    def __init__(self, anaconda_path: str = "D:/ANACONDA"):
        self.scanner = AnacondaScanner(anaconda_path)
        self.analyzer = DependencyAnalyzer(self.scanner)
        
    def initialize(self):
        """Initialize the brain by scanning and analyzing"""
        logger.info("Initializing LUXORANOVA BRAIN...")
        
        # Scan environments
        self.scanner.scan_environments()
        
        # Build dependency graph
        self.analyzer.build_dependency_graph()
        
    def generate_report(self) -> dict:
        """Generate a comprehensive report of the Anaconda system"""
        report = {
            "environments": {},
            "total_environments": len(self.scanner.environments),
            "total_packages": sum(
                len(env.packages)
                for env in self.scanner.environments.values()
            ),
            "active_environment": None,
            "system_stats": {
                "total_size": sum(
                    env.size
                    for env in self.scanner.environments.values()
                )
            }
        }
        
        # Add environment details
        for env_name, env_info in self.scanner.environments.items():
            report["environments"][env_name] = {
                "python_version": env_info.python_version,
                "package_count": len(env_info.packages),
                "size_bytes": env_info.size,
                "is_active": env_info.is_active
            }
            
            if env_info.is_active:
                report["active_environment"] = env_name
                
        return report
    
    def optimize_environments(self) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Check for duplicate environments
        package_sets = {}
        for env_name, env_info in self.scanner.environments.items():
            package_set = frozenset(env_info.packages.items())
            if package_set in package_sets:
                suggestions.append(
                    f"Environments {env_name} and {package_sets[package_set]} "
                    "have identical packages"
                )
            package_sets[package_set] = env_name
            
        # Check for outdated packages
        for env_name, env_info in self.scanner.environments.items():
            for pkg_name, version in env_info.packages.items():
                if version.endswith('.0'):
                    suggestions.append(
                        f"Package {pkg_name} in environment {env_name} "
                        "might have an update available"
                    )
                    
        return suggestions

def main():
    """Main function to run the LUXORANOVA BRAIN"""
    try:
        # Initialize brain
        brain = LuxoranovaBrain()
        brain.initialize()
        
        # Generate and print report
        report = brain.generate_report()
        print("\n=== LUXORANOVA BRAIN REPORT ===")
        print(json.dumps(report, indent=2))
        
        # Get optimization suggestions
        suggestions = brain.optimize_environments()
        if suggestions:
            print("\n=== OPTIMIZATION SUGGESTIONS ===")
            for suggestion in suggestions:
                print(f"- {suggestion}")
                
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
