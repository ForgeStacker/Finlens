"""
Configuration Loader
Loads and validates YAML configuration files (profiles, regions, services)
Following CMMI Level 5 configuration management standards
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceConfig:
    """Service configuration data class"""
    mode: str  # 'include' or 'exclude'
    list: List[str]  # List of services
    
    def should_scan_service(self, service_name: str) -> bool:
        """
        Determine if a service should be scanned
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service should be scanned
        """
        if self.mode == 'include':
            return service_name in self.list
        elif self.mode == 'exclude':
            return service_name not in self.list
        else:
            logger.warning(f"Unknown services mode: {self.mode}, defaulting to include")
            return service_name in self.list


@dataclass
class RegionConfig:
    """Region configuration data class"""
    include: List[str]  # Regions to include
    exclude: List[str]  # Regions to exclude
    
    def should_scan_region(self, region_name: str) -> bool:
        """
        Determine if a region should be scanned
        
        Args:
            region_name: Name of the region
            
        Returns:
            True if region should be scanned
        """
        # If region is in exclude list, skip it
        if region_name in self.exclude:
            return False
        
        # If include list is empty, scan all regions (except excluded)
        if not self.include:
            return True
        
        # Otherwise, only scan regions in include list
        return region_name in self.include
    
    def get_regions_to_scan(self) -> List[str]:
        """
        Get list of regions to scan
        
        Returns:
            List of region names
        """
        # If include list is specified, use it (minus any excluded)
        if self.include:
            return [r for r in self.include if r not in self.exclude]
        
        # If no include list, must specify explicitly
        logger.warning("No regions specified in include list")
        return []


@dataclass
class ProfileConfig:
    """Profile configuration data class"""
    name: str
    description: str = ""


@dataclass
class ScanConfig:
    """Scan configuration data class"""
    timeout: int = 300
    retry: int = 3
    parallel: bool = True


@dataclass
class FinLensConfig:
    """Main configuration data class"""
    services: ServiceConfig
    regions: RegionConfig
    profiles: List[ProfileConfig]
    scan: ScanConfig
    
    def get_profiles(self) -> List[ProfileConfig]:
        """Get list of profiles"""
        return self.profiles
    
    def get_profile(self, name: str) -> Optional[ProfileConfig]:
        """Get specific profile by name"""
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None
    
    def get_enabled_services(self) -> List[str]:
        """Get list of enabled services"""
        return self.services.list if self.services.mode == 'include' else []
    
    def get_regions_to_scan(self) -> List[str]:
        """Get list of regions to scan"""
        return self.regions.get_regions_to_scan()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Create FinLensConfig from dictionary
        
        Args:
            data: Configuration dictionary
            
        Returns:
            FinLensConfig instance
        """
        # Parse services
        services_data = data.get('services', {})
        services = ServiceConfig(
            mode=services_data.get('mode', 'include'),
            list=services_data.get('list', [])
        )
        
        # Parse regions
        regions_data = data.get('regions', {})
        regions = RegionConfig(
            include=regions_data.get('include', []),
            exclude=regions_data.get('exclude', [])
        )
        
        # Parse profiles
        profiles_data = data.get('profiles', [])
        profiles = [
            ProfileConfig(
                name=p.get('name', 'default'),
                description=p.get('description', '')
            )
            for p in profiles_data
        ]
        
        # Parse scan config
        scan_data = data.get('scan', {})
        scan = ScanConfig(
            timeout=scan_data.get('timeout', 300),
            retry=scan_data.get('retry', 3),
            parallel=scan_data.get('parallel', True)
        )
        
        return cls(
            services=services,
            regions=regions,
            profiles=profiles,
            scan=scan
        )


class ConfigLoader:
    """Configuration loader and validator"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Path to config directory (optional)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to config directory in project root
            project_root = Path(__file__).parent.parent
            self.config_dir = project_root / 'config'
        
        self.profiles_path = self.config_dir / 'profiles.yaml'
        self.regions_path = self.config_dir / 'regions.yaml'
        self.services_path = self.config_dir / 'services.yaml'
        self.config: Optional[FinLensConfig] = None
    
    def load(self) -> FinLensConfig:
        """
        Load and parse configuration files
        
        Returns:
            FinLensConfig instance
            
        Raises:
            FileNotFoundError: If config files do not exist
            yaml.YAMLError: If config files contain invalid YAML
            ValueError: If configuration validation fails
        """
        logger.info(f"Loading configuration from: {self.config_dir}")
        
        # Check all required files exist
        if not self.profiles_path.exists():
            error_msg = f"Profiles configuration not found: {self.profiles_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not self.regions_path.exists():
            error_msg = f"Regions configuration not found: {self.regions_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not self.services_path.exists():
            error_msg = f"Services configuration not found: {self.services_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Load profiles configuration
            with open(self.profiles_path, 'r') as f:
                profiles_data = yaml.safe_load(f)
            
            # Load regions configuration
            with open(self.regions_path, 'r') as f:
                regions_data = yaml.safe_load(f)
            
            # Load services configuration
            with open(self.services_path, 'r') as f:
                services_data = yaml.safe_load(f)
            
            # Merge configurations
            merged_data = {
                'profiles': profiles_data.get('profiles', []),
                'regions': regions_data,
                'services': services_data,
                'scan': {}  # Default scan config
            }
            
            self.config = FinLensConfig.from_dict(merged_data)
            
            # Validate configuration
            self._validate()
            
            logger.info("Configuration loaded successfully")
            return self.config
            
        except yaml.YAMLError as e:
            error_msg = f"Failed to parse YAML configuration: {str(e)}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg)
            raise
    
    def _validate(self):
        """
        Validate configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        # Validate services
        if not self.config.services.list:
            raise ValueError("No services configured")
        
        if self.config.services.mode not in ['include', 'exclude']:
            raise ValueError(f"Invalid services mode: {self.config.services.mode}")
        
        # Validate regions
        if not self.config.regions.include:
            logger.warning("No regions specified in include list")
        
        # Validate profiles
        if not self.config.profiles:
            raise ValueError("No profiles configured")
        
        # Check for duplicate profile names
        profile_names = [p.name for p in self.config.profiles]
        if len(profile_names) != len(set(profile_names)):
            raise ValueError("Duplicate profile names found")
        
        logger.info("Configuration validation passed")
    
    def get_config(self) -> Optional[FinLensConfig]:
        """
        Get loaded configuration
        
        Returns:
            FinLensConfig instance or None if not loaded
        """
        return self.config


def load_config(config_dir: Optional[str] = None) -> FinLensConfig:
    """
    Convenience function to load configuration
    
    Args:
        config_dir: Path to config directory (optional)
        
    Returns:
        FinLensConfig instance
    """
    loader = ConfigLoader(config_dir)
    return loader.load()
