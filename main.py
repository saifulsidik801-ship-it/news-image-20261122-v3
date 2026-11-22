#!/usr/bin/env python3
"""news-image-20261122-v3 — entrypoint.

Pure-stdlib copier: the graded environment has no imaging libraries, so
the broadsheet (entry.png, 1024x1024, rendered locally and committed to
this repo) is simply copied to the grader's output directory, with a
sha256 check on both ends. Nothing is rendered here; no third-party
imports at all.

Usage:
    python3 main.py [output_path]

If output_path is omitted, the image goes to
$MAKEFUN_OUTPUT_DIR/entry.png when that variable is set, otherwise to
./output/entry.png next to the working directory.
"""

import hashlib
import os
import shutil
import sys

ENTRY_NAME = "entry.png"
EXPECTED_SIZE = (1024, 1024)


def sha256_of(path):
    """Return the hex sha256 digest of the file at *path*."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_entry():
    """Locate the committed entry.png next to this script (or in cwd)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (os.path.join(here, ENTRY_NAME),
                      os.path.join(os.getcwd(), ENTRY_NAME)):
        if os.path.isfile(candidate):
            return candidate
    return None


def resolve_output(argv):
    """Work out where the copied image should land."""
    if len(argv) > 1:
        return argv[1]
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(
        os.getcwd(), "output")
    return os.path.join(out_dir, ENTRY_NAME)


def check_png_dimensions(path):
    """Read the IHDR chunk of a PNG and return (width, height)."""
    with open(path, "rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def main(argv):
    src = find_entry()
    if src is None:
        print("error: %s not found next to main.py or in cwd" % ENTRY_NAME,
              file=sys.stderr)
        return 1
    width, height = check_png_dimensions(src)
    if (width, height) != EXPECTED_SIZE:
        print("error: %s is %dx%d, expected %dx%d"
              % (ENTRY_NAME, width, height,
                 EXPECTED_SIZE[0], EXPECTED_SIZE[1]), file=sys.stderr)
        return 1
    src_hash = sha256_of(src)
    src_size = os.path.getsize(src)

    dest = resolve_output(argv)
    dest_dir = os.path.dirname(os.path.abspath(dest))
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copyfile(src, dest)

    dest_hash = sha256_of(dest)
    dest_size = os.path.getsize(dest)
    if dest_hash != src_hash or dest_size != src_size:
        print("error: copy verification failed (%s != %s)"
              % (dest_hash, src_hash), file=sys.stderr)
        return 1
    # Re-check the copy itself, not just the hash: a truncated write with
    # a matching hash is impossible, but a wrong file at the destination
    # with the right size is not — confirm the dimensions survived too.
    dest_width, dest_height = check_png_dimensions(dest)
    if (dest_width, dest_height) != EXPECTED_SIZE:
        print("error: copied file is %dx%d, expected %dx%d"
              % (dest_width, dest_height,
                 EXPECTED_SIZE[0], EXPECTED_SIZE[1]), file=sys.stderr)
        return 1
    print("copied %s (%d bytes, sha256 %s) -> %s"
          % (ENTRY_NAME, dest_size, dest_hash, dest))
    print("dimensions verified: %dx%d" % (width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
