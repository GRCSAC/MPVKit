#!/usr/bin/env python3
"""Keep Package.swift in step with the GRCSAC (OmniPlay) build of MPVKit.

  omniplay-package.py strip-gpl
      Remove the GPL product and targets. This fork ships the LGPL build only.

  omniplay-package.py pin <version> <release-dir>
      Point the targets this fork builds (FFmpeg + libmpv) at the GRCSAC release
      <version>, with the checksums written by the build into <release-dir>.
      Everything else (libass, MoltenVK, libplacebo, ...) stays on mpvkit's
      own dependency releases, which this fork does not rebuild.
"""
import pathlib
import re
import sys

PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "Package.swift"
BUILT = ["Libmpv", "Libavcodec", "Libavdevice", "Libavformat", "Libavfilter",
         "Libavutil", "Libswresample", "Libswscale"]


def strip_gpl(text: str) -> str:
    text = re.sub(r'\n        \.library\(\n            name: "MPVKit-GPL",.*?\n        \),', "", text, flags=re.S)
    text = re.sub(r'\n        \.target\(\n            name: "_MPVKit-GPL",.*?(?=\n\n        \.binaryTarget\()', "", text, flags=re.S)
    text = re.sub(r'\n\n?        \.binaryTarget\(\n            name: "[^"]+-GPL",.*?\n        \),', "", text, flags=re.S)
    text = re.sub(r'\n\n?        \.binaryTarget\(\n            name: "Libsmbclient",.*?\n        \),', "", text, flags=re.S)
    if "GPL" in text.replace("LGPL", ""):
        sys.exit("strip-gpl: GPL references remain in Package.swift")
    return text


def pin(text: str, version: str, release: pathlib.Path) -> str:
    for name in BUILT:
        checksum = (release / f"{name}.xcframework.checksum.txt").read_text().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            sys.exit(f"pin: bad checksum for {name}: {checksum!r}")
        url = f"https://github.com/GRCSAC/MPVKit/releases/download/{version}/{name}.xcframework.zip"
        pattern = re.compile(r'(\.binaryTarget\(\n\s+name: "' + re.escape(name) + r'",\n\s+url: ")[^"]*(",\n\s+checksum: ")[^"]*(")')
        text, count = pattern.subn(lambda m: m.group(1) + url + m.group(2) + checksum + m.group(3), text)
        if count != 1:
            sys.exit(f"pin: expected one binaryTarget named {name}, found {count}")
    return text


def main() -> None:
    text = PACKAGE.read_text()
    if sys.argv[1:2] == ["strip-gpl"]:
        text = strip_gpl(text)
    elif sys.argv[1:2] == ["pin"] and len(sys.argv) == 4:
        text = pin(text, sys.argv[2], pathlib.Path(sys.argv[3]))
    else:
        sys.exit(__doc__)
    PACKAGE.write_text(text)


if __name__ == "__main__":
    main()
