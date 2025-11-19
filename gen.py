"""
Generator script for ResponseSpec ANTLR parser.
Run this script to generate the Python parser from the .g4 grammar file.
"""

import os
import subprocess
import sys


def generate_parser():
    """Generate ANTLR parser from ResponseSpec.g4"""
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    g4_file = os.path.join(script_dir, "spec_lang", "ResponseSpec.g4")
    antlr_jar = os.path.join(script_dir, "..", "AgentSpec-master", "src", "spec_lang", "antlr-4.13.2-complete.jar")
    output_dir = os.path.join(script_dir, "spec_lang")
    
    # Check if ANTLR jar exists
    if not os.path.exists(antlr_jar):
        print(f"Error: ANTLR jar not found at {antlr_jar}")
        print("Please download ANTLR 4.13.2 from https://www.antlr.org/download/")
        return False
    
    # Check if g4 file exists
    if not os.path.exists(g4_file):
        print(f"Error: Grammar file not found at {g4_file}")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate parser
    print(f"Generating parser from {g4_file}...")
    cmd = [
        "java",
        "-jar",
        antlr_jar,
        "-Dlanguage=Python3",
        "-o",
        output_dir,
        g4_file
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Parser generated successfully!")
        print(result.stdout)
        
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(output_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# ResponseSpec parser module\n")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating parser: {e}")
        print(e.stderr)
        return False


if __name__ == "__main__":
    success = generate_parser()
    sys.exit(0 if success else 1)
