from pathlib import Path

# AF4 falsifier: if Blender reports process success despite this exception, Studio must
# reject semantic completion unless declared artifact/state postconditions are observed.
raise RuntimeError("AF4_INTENTIONAL_BLENDER_TRACEBACK")
