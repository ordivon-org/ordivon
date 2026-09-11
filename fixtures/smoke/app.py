import subprocess


def echo(value: str) -> str:
    return subprocess.check_output(["printf", "%s", value], text=True)
