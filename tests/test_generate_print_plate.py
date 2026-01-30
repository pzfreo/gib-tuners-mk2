import subprocess
import sys
import tempfile
from pathlib import Path

def test_generate_print_plate_script():
    """Test that the generate_print_plate.py script runs and produces output."""
    script_path = Path(__file__).parent.parent / "scripts" / "generate_print_plate.py"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_plate.3mf"
        
        # Run the script with minimal arguments
        cmd = [
            sys.executable,
            str(script_path),
            "--num-housings", "1",
            "--output", str(output_file)
        ]
        
        # Run process
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check return code
        assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"
        
        # Check if output file exists and has size
        assert output_file.exists(), "Output 3MF file was not created"
        assert output_file.stat().st_size > 0, "Output 3MF file is empty"

def test_generate_print_plate_viz_arg():
    """Test that the script accepts the --viz argument (dry run)."""
    # We can't easily test visual output in CI/test env, but we can check it doesn't crash 
    # immediately on argument parsing. However, invoking --viz might try to open a window.
    # We'll skip running it fully if we can't mock the visualization.
    # For now, just ensuring the help text works is a basic check of arg parsing.
    script_path = Path(__file__).parent.parent / "scripts" / "generate_print_plate.py"
    cmd = [sys.executable, str(script_path), "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "--viz" in result.stdout
