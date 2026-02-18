#!/usr/bin/env python3

"""
Simple API server to serve data from the FinLens data directory
This reads the actual JSON files from your data directory structure
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

class DataAPIHandler(BaseHTTPRequestHandler):
    @staticmethod
    def _add_service(discovery_result, account_name, category_name, service_name):
        """Add discovered service once per category"""
        if category_name not in discovery_result['services'][account_name]:
            discovery_result['services'][account_name][category_name] = []
        if service_name not in discovery_result['services'][account_name][category_name]:
            discovery_result['services'][account_name][category_name].append(service_name)

    @staticmethod
    def _add_region(discovery_result, account_name, region_name):
        """Add discovered region once per account"""
        if region_name and region_name not in discovery_result['regions'][account_name]:
            discovery_result['regions'][account_name].append(region_name)

    def do_GET(self):
        """Handle GET requests for service data and discovery"""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) >= 2 and path_parts[0] == 'api':
            if path_parts[1] == 'discovery':
                self.serve_discovery_data()
            elif path_parts[1] == 'data' and len(path_parts) >= 5:
                account_name = path_parts[2]
                region_code = path_parts[3]

                if len(path_parts) == 5:
                    service_name = path_parts[4]
                    category_name = None
                else:
                    category_name = path_parts[4]
                    service_name = path_parts[5] if len(path_parts) > 5 else None

                if service_name:
                    self.serve_service_data(account_name, region_code, service_name, category_name)
                else:
                    self.send_error(400, "Service name required")
            else:
                self.send_error(404, "API endpoint not found")
        else:
            self.send_error(404, "Not found")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def serve_discovery_data(self):
        """Discover and return the complete file system structure"""
        try:
            # Get the data directory path - check for Docker environment first
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Check if we're in Docker container (api_server.py is in /app/)
            if script_dir == '/app':
                data_root = '/app/data'
            else:
                # Local development mode (api_server.py is in frontend/)
                data_root = os.path.join(script_dir, '..', 'data')
            
            print(f"Looking for data directory at: {data_root}")  # Debug logging
            
            discovery_result = {
                'accounts': [],
                'regions': {},
                'services': {}
            }
            
            if not os.path.exists(data_root):
                self.send_json_response(discovery_result)
                return
            
            # Discover accounts
            for account_dir in os.listdir(data_root):
                account_path = os.path.join(data_root, account_dir)
                if os.path.isdir(account_path):
                    discovery_result['accounts'].append(account_dir)
                    discovery_result['regions'][account_dir] = []
                    discovery_result['services'][account_dir] = {}

                    # New layout:
                    # data/{account}/regions/{region}/services/{category}/{service}.json
                    regions_root = os.path.join(account_path, 'regions')
                    if os.path.exists(regions_root):
                        for region_dir in os.listdir(regions_root):
                            region_path = os.path.join(regions_root, region_dir)
                            if not os.path.isdir(region_path):
                                continue

                            self._add_region(discovery_result, account_dir, region_dir)

                            services_path = os.path.join(region_path, 'services')
                            if not os.path.exists(services_path):
                                continue

                            for category_dir in os.listdir(services_path):
                                category_path = os.path.join(services_path, category_dir)
                                if not os.path.isdir(category_path):
                                    continue

                                for service_file in os.listdir(category_path):
                                    if service_file.endswith('.json'):
                                        service_name = service_file[:-5]  # Remove .json extension
                                        self._add_service(discovery_result, account_dir, category_dir, service_name)

                    # Legacy layout fallback:
                    # data/{account}/services/{category}/{service}.json
                    legacy_services_path = os.path.join(account_path, 'services')
                    if os.path.exists(legacy_services_path):
                        for category_dir in os.listdir(legacy_services_path):
                            category_path = os.path.join(legacy_services_path, category_dir)
                            if not os.path.isdir(category_path):
                                continue

                            for service_file in os.listdir(category_path):
                                if service_file.endswith('.json'):
                                    service_name = service_file[:-5]  # Remove .json extension
                                    self._add_service(discovery_result, account_dir, category_dir, service_name)

                                    # Try to determine region from file content for legacy data
                                    try:
                                        service_file_path = os.path.join(category_path, service_file)
                                        with open(service_file_path, 'r', encoding='utf-8') as f:
                                            service_data = json.load(f)
                                            region = (
                                                service_data.get('region')
                                                or service_data.get('service', {}).get('region')
                                            )
                                            self._add_region(discovery_result, account_dir, region)
                                    except Exception as load_error:
                                        print(f"Discovery parsing error for {service_file_path}: {load_error}")
                    
                    # Default region if none found
                    if not discovery_result['regions'][account_dir]:
                        discovery_result['regions'][account_dir] = ['ap-south-1']
            
            print(f"Discovery result: {discovery_result}")
            self.send_json_response(discovery_result)
            
        except Exception as e:
            print(f"Error in discovery: {e}")
            self.send_error(500, f"Discovery failed: {str(e)}")

    def serve_service_data(self, account_name, region_code, service_name, category_name=None):
        """Serve data from the actual JSON files"""
        try:
            # Get the data directory path - check for Docker environment first
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Check if we're in Docker container (api_server.py is in /app/)
            if script_dir == '/app':
                account_root = f'/app/data/{account_name}'
            else:
                # Local development mode (api_server.py is in frontend/)
                account_root = os.path.join(script_dir, '..', 'data', account_name)
            
            print(f"Looking for service data in account root: {account_root}")  # Debug logging

            region_services_dir = os.path.join(account_root, 'regions', region_code, 'services')
            legacy_services_dir = os.path.join(account_root, 'services')
            
            # Determine which categories to search
            categories_to_check = []
            if category_name:
                categories_to_check = [category_name]
            else:
                if os.path.exists(region_services_dir):
                    categories_to_check.extend(
                        [c for c in os.listdir(region_services_dir) if os.path.isdir(os.path.join(region_services_dir, c))]
                    )
                if os.path.exists(legacy_services_dir):
                    categories_to_check.extend(
                        [c for c in os.listdir(legacy_services_dir) if os.path.isdir(os.path.join(legacy_services_dir, c))]
                    )

            # Find the service file across categories
            service_file = None
            for category_dir in categories_to_check:
                # First try new region-specific path
                category_path = os.path.join(region_services_dir, category_dir)
                potential_file = os.path.join(category_path, f'{service_name}.json')
                if os.path.exists(potential_file):
                    service_file = potential_file
                    break

                # Then try legacy path
                legacy_category_path = os.path.join(legacy_services_dir, category_dir)
                legacy_file = os.path.join(legacy_category_path, f'{service_name}.json')
                if os.path.exists(legacy_file):
                    service_file = legacy_file
                    break

            # Final fallback: search requested service in any region
            if service_file is None and os.path.exists(os.path.join(account_root, 'regions')):
                regions_root = os.path.join(account_root, 'regions')
                for discovered_region in os.listdir(regions_root):
                    region_path = os.path.join(regions_root, discovered_region, 'services')
                    if not os.path.isdir(region_path):
                        continue

                    search_categories = categories_to_check if category_name else [
                        c for c in os.listdir(region_path) if os.path.isdir(os.path.join(region_path, c))
                    ]

                    for category_dir in search_categories:
                        potential_file = os.path.join(region_path, category_dir, f'{service_name}.json')
                        if os.path.exists(potential_file):
                            service_file = potential_file
                            break
                    if service_file:
                        break
            
            if service_file and os.path.exists(service_file):
                with open(service_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
            else:
                # Return empty structure if file not found
                empty_data = {
                    "schema_version": "1.0.0",
                    "generated_at": "2026-02-09T00:00:00.000000",
                    "service": {
                        "service_name": service_name,
                        "region": region_code,
                        "profile": account_name
                    },
                    "summary": {
                        "resource_count": 0,
                        "scan_status": "success"
                    },
                    "resources": []
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(json.dumps(empty_data, indent=2).encode('utf-8'))
                
        except Exception as e:
            print(f"Error serving data for {account_name}/{service_name}: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def send_json_response(self, data):
        """Helper method to send JSON response with proper headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        print(f"[API] {format % args}")

def main():
    """Main function to start the API server"""
    port = 8083
    # Bind to 0.0.0.0 for Docker container access, localhost for local development
    host = '0.0.0.0'
    server = HTTPServer((host, port), DataAPIHandler)
    print(f"Starting FinLens Data API server on http://{host}:{port}")
    print("Endpoints:")
    print("  GET /api/data/{account}/{region}/{service}")
    print(f"  Example: http://localhost:{port}/api/data/your-account/ap-south-1/eks")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == '__main__':
    main()