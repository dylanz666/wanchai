import subprocess
import sys
import re
import os
import semver
import importlib.util


def bump_version(version, bump_type="patch"):
    v = semver.VersionInfo.parse(version)
    bump_methods = {
        "major": v.bump_major,
        "minor": v.bump_minor,
        "prerelease": v.bump_prerelease,
        "patch": v.bump_patch,
    }
    return str(bump_methods.get(bump_type, v.bump_patch)())


def get_version():
    path = os.path.join(os.path.dirname(__file__), "version.py")
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location("version", path)
        if spec is not None and spec.loader is not None:
            version_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version_mod)
            return getattr(version_mod, "__version__", "0.0.0")
    return "0.0.0"


def main():
    print("Starting build process...")
    bump_type = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("major", "minor", "patch", "prerelease"):
            bump_type = arg
    # 读取当前版本
    version = get_version()
    if bump_type:
        # 调用 version_manager.py 递增版本
        result = subprocess.run(
            [sys.executable, "version_manager.py", bump_type],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        version = get_version()
    exe_name = f"wanchai-editor_v{version}"
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        "--icon=editor.ico",
        "wanchai-editor.py",
    ]
    print(" ".join(cmd))
    try:
        result = subprocess.run(cmd, check=True)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
