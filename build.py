"""
Rebuild everything from params.py:

    python build.py            sizing report, templates, STL files, 3D model
    python build.py --fast     skip the 3D parts (no CadQuery needed)
"""
import sys

from sizing import design_calc

d = design_calc.main()
from cad import export_templates          # noqa: E402

export_templates.main()
if "--fast" not in sys.argv:
    from cad import assembly, printed_parts   # noqa: E402
    printed_parts.main()
    assembly.main()
if d["warnings"]:
    print("\nWARNINGS:")
    for w in d["warnings"]:
        print("  -", w)
else:
    print("\nAll design checks pass.")
