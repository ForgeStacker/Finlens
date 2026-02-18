"""
FinLens Main Entry Point
Simple single-command execution - no CLI arguments needed
Following CMMI Level 5 standards for quality and process management
"""

import sys
from pathlib import Path

from backend.config_loader import load_config
from backend.runner import run_scan
from backend.utils.logger import get_logger, log_operation

logger = get_logger(__name__)

# Version information
VERSION = "1.0.0"
PRODUCT_NAME = "FinLens"


def _display_banner():
    """Display FinLens banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗███╗   ██╗██╗     ███████╗███╗   ██╗███████╗   ║
║   ██╔════╝██║████╗  ██║██║     ██╔════╝████╗  ██║██╔════╝   ║
║   █████╗  ██║██╔██╗ ██║██║     █████╗  ██╔██╗ ██║███████╗   ║
║   ██╔══╝  ██║██║╚██╗██║██║     ██╔══╝  ██║╚██╗██║╚════██║   ║
║   ██║     ██║██║ ╚████║███████╗███████╗██║ ╚████║███████║   ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝   ║
║                                                              ║
║   Cloud Infrastructure Scanner                  v{VERSION}      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """
    Main entry point - automatically scans all configured profiles
    No command-line arguments required
    
    Usage: python finlens.py
    """
    try:
        # Display banner
        _display_banner()
        
        log_operation("FINLENS_SCAN", "START", f"Version: {VERSION}")
        
        # Load configuration from default location
        print("\n📋 Loading configuration...")
        config_dir = Path(__file__).parent.parent / 'config'
        cfg = load_config(str(config_dir))
        
        print(f"✅ Configuration loaded successfully")
        
        # Display what will be scanned
        print(f"\n📊 Scan Plan:")
        print(f"   Profiles: {len(cfg.profiles)}")
        for p in cfg.profiles:
            print(f"      • {p.name} - {p.description}")
        
        print(f"   Regions (include): {len(cfg.regions.include)}")
        for r in cfg.regions.include:
            print(f"      • {r}")
        
        if cfg.regions.exclude:
            print(f"   Regions (exclude): {len(cfg.regions.exclude)}")
            for r in cfg.regions.exclude:
                print(f"      • {r}")
        
        # Get enabled services based on mode
        enabled_services = []
        if cfg.services.mode == 'include':
            enabled_services = cfg.services.list
            print(f"   Services (include): {len(enabled_services)}")
        else:
            # For exclude mode, you'd need all available services
            enabled_services = cfg.services.list  # This is what to exclude
            print(f"   Services (exclude): {len(enabled_services)}")
        
        for s in enabled_services:
            print(f"      • {s}")
        
        # Validate AWS credentials
        print(f"\n🔐 Validating AWS credentials...")
        from backend.utils.aws_client import validate_aws_credentials
        
        for profile in cfg.profiles:
            print(f"   Checking profile: {profile.name}...", end=" ")
            try:
                if validate_aws_credentials(profile.name):
                    print("✅")
                else:
                    print("❌ Failed")
                    print(f"\n❌ Error: Could not validate credentials for profile '{profile.name}'")
                    print(f"   Please check that AWS credentials are configured correctly.")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                sys.exit(1)
        
        # Set output directory to default ./data
        output_dir = Path(__file__).parent.parent / 'data'
        
        # Execute scan
        print(f"\n🚀 Starting scan...")
        print(f"   Output directory: {output_dir}")
        print("")
        
        results = run_scan(cfg, output_dir)
        
        # Display results
        _display_results(results)
        
        # Determine exit code
        if results['failed']:
            print("\n⚠️  Scan completed with errors")
            log_operation("FINLENS_SCAN", "COMPLETED_WITH_ERRORS", 
                         f"Failed: {len(results['failed'])}")
            sys.exit(1)
        else:
            print("\n✅ Scan completed successfully")
            log_operation("FINLENS_SCAN", "SUCCESS", 
                         f"Successful: {len(results['successful'])}")
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        log_operation("FINLENS_SCAN", "INTERRUPTED", "User cancelled")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during scan")
        print(f"\n❌ Error: {str(e)}")
        log_operation("FINLENS_SCAN", "FAILED", str(e))
        sys.exit(1)


def _display_results(results):
    """Display scan results summary"""
    successful = len(results['successful'])
    failed = len(results['failed'])
    skipped = len(results['skipped'])
    total = successful + failed + skipped
    
    print("\n" + "=" * 60)
    print("📊 SCAN RESULTS")
    print("=" * 60)
    print(f"Total collectors executed: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print("=" * 60)
    
    if results['successful']:
        print("\n✅ Successful collectors:")
        for item in results['successful']:
            print(f"   • {item['profile']}/{item['region']}/{item['service']}")
    
    if results['failed']:
        print("\n❌ Failed collectors:")
        for item in results['failed']:
            error = item.get('error', 'Unknown error')
            print(f"   • {item['profile']}/{item['region']}/{item['service']}")
            print(f"     Error: {error}")
    
    if results['skipped']:
        print("\n⏭️  Skipped collectors:")
        for item in results['skipped']:
            reason = item.get('reason', 'Unknown reason')
            print(f"   • {item['profile']}/{item['region']}/{item['service']}")
            print(f"     Reason: {reason}")


if __name__ == '__main__':
    main()
