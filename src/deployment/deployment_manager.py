"""
Simplified deployment manager
This replaces the complex deploy_endpoints.py with a cleaner interface
"""

import argparse
import sys
from typing import Optional

from ..audio_processing.deployment import ModalDeployer, EndpointManager
from ..audio_processing.utils.config import AudioProcessingConfig
from ..audio_processing.utils.errors import DeploymentError


class DeploymentManager:
    """Simplified deployment manager for audio processing services"""
    
    def __init__(self):
        self.config = AudioProcessingConfig()
        self.modal_deployer = ModalDeployer(self.config)
        self.endpoint_manager = EndpointManager()
    
    def deploy(self) -> bool:
        """Deploy transcription service"""
        try:
            print("🚀 Starting deployment process...")
            endpoint_url = self.modal_deployer.deploy_transcription_service()
            
            if endpoint_url:
                print(f"✅ Deployment successful!")
                print(f"🌐 Endpoint URL: {endpoint_url}")
                return True
            else:
                print("❌ Deployment failed: Could not get endpoint URL")
                return False
                
        except DeploymentError as e:
            print(f"❌ Deployment failed: {e.message}")
            if e.details:
                print(f"📋 Details: {e.details}")
            return False
        except Exception as e:
            print(f"❌ Unexpected deployment error: {str(e)}")
            return False
    
    def status(self) -> bool:
        """Check deployment status"""
        print("🔍 Checking deployment status...")
        
        endpoints = self.endpoint_manager.list_endpoints()
        if not endpoints:
            print("❌ No endpoints configured")
            return False
        
        print(f"📋 Configured endpoints:")
        for name, url in endpoints.items():
            print(f"  • {name}: {url}")
        
        # Check health
        return self.modal_deployer.check_deployment_status()
    
    def undeploy(self):
        """Remove deployment configuration"""
        print("🗑️ Removing deployment configuration...")
        self.modal_deployer.undeploy_transcription_service()
    
    def list_endpoints(self):
        """List all configured endpoints"""
        endpoints = self.endpoint_manager.list_endpoints()
        
        if not endpoints:
            print("📋 No endpoints configured")
            return
        
        print("📋 Configured endpoints:")
        for name, url in endpoints.items():
            health_status = "✅ Healthy" if self.endpoint_manager.check_endpoint_health(name) else "❌ Unhealthy"
            print(f"  • {name}: {url} ({health_status})")
    
    def set_endpoint(self, name: str, url: str):
        """Manually set an endpoint"""
        self.endpoint_manager.set_endpoint(name, url)
    
    def remove_endpoint(self, name: str):
        """Remove an endpoint"""
        self.endpoint_manager.remove_endpoint(name)


def main():
    """Command line interface for deployment manager"""
    parser = argparse.ArgumentParser(description="Audio Processing Deployment Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Deploy command
    subparsers.add_parser("deploy", help="Deploy transcription service to Modal")
    
    # Status command
    subparsers.add_parser("status", help="Check deployment status")
    
    # Undeploy command
    subparsers.add_parser("undeploy", help="Remove deployment configuration")
    
    # List endpoints command
    subparsers.add_parser("list", help="List all configured endpoints")
    
    # Set endpoint command
    set_parser = subparsers.add_parser("set", help="Set endpoint URL manually")
    set_parser.add_argument("name", help="Endpoint name")
    set_parser.add_argument("url", help="Endpoint URL")
    
    # Remove endpoint command
    remove_parser = subparsers.add_parser("remove", help="Remove endpoint")
    remove_parser.add_argument("name", help="Endpoint name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DeploymentManager()
    
    try:
        if args.command == "deploy":
            success = manager.deploy()
            sys.exit(0 if success else 1)
        
        elif args.command == "status":
            success = manager.status()
            sys.exit(0 if success else 1)
        
        elif args.command == "undeploy":
            manager.undeploy()
        
        elif args.command == "list":
            manager.list_endpoints()
        
        elif args.command == "set":
            manager.set_endpoint(args.name, args.url)
        
        elif args.command == "remove":
            manager.remove_endpoint(args.name)
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 