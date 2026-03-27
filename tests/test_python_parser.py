from pathlib import Path

from sweepr.parsers.python_parser import analyze_python


def test_detects_unused_import_and_variable() -> None:
    content = """import os\nimport sys\n\n\ndef run():\n    temp = 123\n    return os.getcwd()\n"""
    analysis = analyze_python(Path("demo.py"), content)
    kinds = {finding.kind for finding in analysis.findings}
    assert "unused_import" in kinds
    assert "unused_variable" in kinds
    assert analysis.updated_content is not None
