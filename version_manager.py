import sys
import semver
import os
import importlib.util


def get_version_file():
    return os.path.join(os.path.dirname(__file__), "version.py")


def read_version():
    path = get_version_file()
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location("version", path)
        if spec is not None and spec.loader is not None:
            version_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version_mod)
            return getattr(version_mod, "__version__", "0.0.0")
    return "0.0.0"


def write_version(version):
    path = get_version_file()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"__version__ = '{version}'\n")


def bump_version(version, bump_type):
    v = semver.VersionInfo.parse(version)
    if bump_type == "major":
        return str(v.bump_major())
    elif bump_type == "minor":
        return str(v.bump_minor())
    elif bump_type == "prerelease":
        return str(v.bump_prerelease())
    else:
        return str(v.bump_patch())


def main():
    if len(sys.argv) < 2:
        print(f"Current version: {read_version()}")
        print(
            "Usage: python version_manager.py [patch|minor|major|prerelease|set <version>|get]"
        )
        return
    cmd = sys.argv[1].lower()
    if cmd in ("major", "minor", "patch", "prerelease"):
        old_version = read_version()
        if "-" in old_version and cmd == "patch":
            new_version = old_version.split("-")[0]
        else:
            new_version = bump_version(old_version, cmd)
        write_version(new_version)
        print(f"Version bumped: {old_version} -> {new_version}")
    elif cmd == "set" and len(sys.argv) == 3:
        new_version = sys.argv[2]
        try:
            semver.VersionInfo.parse(new_version)
        except Exception:
            print(f"Invalid semver: {new_version}")
            return
        write_version(new_version)
        print(f"Version set to: {new_version}")
    elif cmd == "get":
        print(read_version())
    else:
        print(
            "Invalid command. Usage: python version_manager.py [patch|minor|major|prerelease|set <version>|get]"
        )


if __name__ == "__main__":
    main()
