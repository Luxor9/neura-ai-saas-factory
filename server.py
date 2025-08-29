#!/usr/bin/env python3
"""
Entry point for the NEURA AI SaaS Factory API server
"""

import uvicorn
import sys
import os

def main():
    """Main entry point for the API server"""
    # Add the root directory to the path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, root_dir)
    
    # Run the server
    uvicorn.run(
        "packages.api.core.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[root_dir],
        log_level="info"
    )

if __name__ == "__main__":
    main()