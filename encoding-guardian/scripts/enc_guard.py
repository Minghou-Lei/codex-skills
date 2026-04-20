#!/usr/bin/env python3
"""
enc_guard.py — Encoding Guardian v2.0
Detects, snapshots, restores, and batch-fixes file encodings.

Supported encodings: GBK/ANSI, UTF-8-BOM, UTF-8, UTF-16 LE/BE, UTF-32, Big5, Shift-JIS, EUC-JP/KR

Requirements: Python 3.8+; optional: pip install chardet

Usage:
  python enc_guard.py detect        <file>                           # print encoding info
  python enc_guard.py snapshot      <file> [--force]                 # save encoding metadata
  python enc_guard.py restore       <file> [--no-verify]             # restore from metadata
  python enc_guard.py verify        <file>                           # check vs snapshot
  python enc_guard.py fix           <file> --enc GBK [--from-enc latin-1]  # force re-encode
  python enc_guard.py scan          <dir>  [--ext .cpp .h ...] [--filter GBK] [--json] [--min-confidence 0.8]
  python enc_guard.py batch-snapshot <dir> [--ext ...] [--dry-run] [--force]
  python enc_guard.py batch         <dir>  [--dry-run] [--no-verify]
  python enc_guard.py status        <dir>                            # show all snapshot states
  python enc_guard.py clean         <dir>  [--dry-run]              # remove .enc_meta files
"""

import sys
import os
import json
import hashlib
import argparse
import tempfile
import shutil
from pathlib import Path

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

META_SUFFIX = ".enc_meta"
VERSION = "2.0"
FILE_SIZE_WARN_MB = 10

DEFAULT_EXTENSIONS = {
    ".cpp", ".h", ".c", ".cc", ".cxx",
    ".cs", ".hlsl", ".glsl", ".usf", ".ush",
    ".lua", ".py",
    ".txt", ".ini", ".cfg", ".xml", ".json",
}

ANSI_ENCODINGS = {"gbk", "gb2312", "gb18030", "cp936", "windows-1252", "ansi"}

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_WARNING = 2


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _atomic_write(filepath: str, data: bytes) -> None:
    path = Path(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".enc_guard_tmp_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        shutil.move(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _write_with_encoding(filepath: str, text: str, enc_label: str, has_bom: bool) -> None:
    enc_upper = enc_label.upper()

    if any(k in enc_upper for k in ("GBK", "GB2312", "GB18030", "ANSI", "CP936")):
        data = text.encode("gbk", errors="replace")
    elif "BIG5" in enc_upper:
        data = text.encode("big5", errors="replace")
    elif "SHIFT_JIS" in enc_upper:
        data = text.encode("shift_jis", errors="replace")
    elif "EUC-JP" in enc_upper:
        data = text.encode("euc_jp", errors="replace")
    elif "EUC-KR" in enc_upper:
        data = text.encode("euc_kr", errors="replace")
    elif "UTF-8-BOM" in enc_upper or (enc_upper == "UTF-8" and has_bom):
        data = b"\xef\xbb\xbf" + text.encode("utf-8", errors="replace")
    elif "UTF-16-LE" in enc_upper:
        data = b"\xff\xfe" + text.encode("utf-16-le", errors="replace")
    elif "UTF-16-BE" in enc_upper:
        data = b"\xfe\xff" + text.encode("utf-16-be", errors="replace")
    elif "UTF-32-LE" in enc_upper:
        data = b"\xff\xfe\x00\x00" + text.encode("utf-32-le", errors="replace")
    elif "UTF-32-BE" in enc_upper:
        data = b"\x00\x00\xfe\xff" + text.encode("utf-32-be", errors="replace")
    else:
        data = text.encode("utf-8", errors="replace")

    _atomic_write(filepath, data)


def _round_trip_verify(filepath: str, enc_label: str, has_bom: bool) -> bool:
    enc_upper = enc_label.upper()
    raw = Path(filepath).read_bytes()

    if has_bom or "BOM" in enc_upper:
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        elif raw.startswith(b"\xff\xfe\x00\x00"):
            raw = raw[4:]
        elif raw.startswith(b"\x00\x00\xfe\xff"):
            raw = raw[4:]
        elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            raw = raw[2:]

    decode_map = {
        "GBK": "gbk", "GB2312": "gbk", "GB18030": "gbk", "ANSI": "gbk",
        "BIG5": "big5",
        "SHIFT_JIS": "shift_jis",
        "EUC-JP": "euc_jp",
        "EUC-KR": "euc_kr",
        "UTF-16-LE": "utf-16-le",
        "UTF-16-BE": "utf-16-be",
        "UTF-32-LE": "utf-32-le",
        "UTF-32-BE": "utf-32-be",
    }
    codec = next((v for k, v in decode_map.items() if k in enc_upper), "utf-8")

    try:
        raw.decode(codec)
        return True
    except (UnicodeDecodeError, LookupError):
        return False


def detect_encoding(filepath: str) -> dict:
    path = Path(filepath)

    try:
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > FILE_SIZE_WARN_MB:
            print(
                f"[detect] WARNING: {filepath} is {size_mb:.1f} MB - detection may be slow",
                file=sys.stderr,
            )
    except OSError:
        pass

    try:
        raw = path.read_bytes()
    except OSError as e:
        print(f"[detect] ERROR: cannot read {filepath}: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if not raw:
        return {"encoding": "UTF-8", "bom": False, "confidence": 1.0, "note": "empty file"}

    if raw.startswith(b"\xef\xbb\xbf"):
        return {"encoding": "UTF-8-BOM", "bom": True, "confidence": 1.0}
    if raw.startswith(b"\xff\xfe\x00\x00"):
        return {"encoding": "UTF-32-LE", "bom": True, "confidence": 1.0}
    if raw.startswith(b"\x00\x00\xfe\xff"):
        return {"encoding": "UTF-32-BE", "bom": True, "confidence": 1.0}
    if raw.startswith(b"\xff\xfe"):
        return {"encoding": "UTF-16-LE", "bom": True, "confidence": 1.0}
    if raw.startswith(b"\xfe\xff"):
        return {"encoding": "UTF-16-BE", "bom": True, "confidence": 1.0}

    try:
        raw.decode("utf-8")
        return {"encoding": "UTF-8", "bom": False, "confidence": 0.99}
    except UnicodeDecodeError:
        pass

    high_bytes = sum(1 for b in raw if b > 0x7F)
    high_ratio = high_bytes / len(raw)

    try:
        raw.decode("gbk")
        if high_bytes >= 2:
            conf = round(min(0.95, 0.70 + high_ratio * 1.5), 2)
            return {"encoding": "GBK", "bom": False, "confidence": conf}
    except (UnicodeDecodeError, ValueError):
        pass

    try:
        raw.decode("big5")
        if high_bytes >= 2:
            conf = round(min(0.88, 0.65 + high_ratio * 1.2), 2)
            return {"encoding": "BIG5", "bom": False, "confidence": conf}
    except (UnicodeDecodeError, ValueError):
        pass

    try:
        raw.decode("shift_jis")
        if high_bytes >= 2:
            conf = round(min(0.85, 0.60 + high_ratio * 1.2), 2)
            return {"encoding": "SHIFT_JIS", "bom": False, "confidence": conf}
    except (UnicodeDecodeError, ValueError):
        pass

    for codec, label in [("euc_jp", "EUC-JP"), ("euc_kr", "EUC-KR")]:
        try:
            raw.decode(codec)
            if high_bytes >= 2:
                return {"encoding": label, "bom": False, "confidence": 0.75}
        except (UnicodeDecodeError, ValueError):
            pass

    if HAS_CHARDET:
        result = chardet.detect(raw)
        enc = (result.get("encoding") or "").lower()
        conf = result.get("confidence", 0.0)

        if conf < 0.6 and high_bytes >= 2:
            try:
                raw.decode("gbk")
                return {"encoding": "GBK", "bom": False, "confidence": 0.65}
            except (UnicodeDecodeError, ValueError):
                pass

        if enc in ANSI_ENCODINGS or enc.startswith("gb"):
            return {"encoding": "GBK", "bom": False, "confidence": round(conf, 2)}
        if enc:
            return {"encoding": enc.upper(), "bom": False, "confidence": round(conf, 2)}

    return {"encoding": "BINARY_OR_UNKNOWN", "bom": False, "confidence": 0.0}


def snapshot(filepath: str, force: bool = False) -> None:
    path = Path(filepath)

    if not path.exists():
        print(f"[snapshot] ERROR: file not found: {filepath}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    info = detect_encoding(filepath)

    if info["encoding"] == "BINARY_OR_UNKNOWN":
        print(f"[snapshot] SKIP {filepath} - binary or undetectable")
        return

    meta_path = filepath + META_SUFFIX

    if os.path.exists(meta_path) and not force:
        print(f"[snapshot] SKIP {filepath} - snapshot exists (use --force to overwrite)")
        return

    raw = path.read_bytes()
    sha256 = _sha256(raw)

    meta = {
        "version": VERSION,
        "file": str(path.resolve()),
        "sha256": sha256,
        **info,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(
        f"[snapshot] {filepath} -> {info['encoding']} "
        f"(confidence={info['confidence']}, sha256={sha256[:8]}...)"
    )


def restore(filepath: str, no_verify: bool = False) -> None:
    meta_path = filepath + META_SUFFIX

    if not os.path.exists(meta_path):
        print(f"[restore] ERROR: no snapshot found at {meta_path}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[restore] ERROR: cannot read snapshot {meta_path}: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    target_enc = meta["encoding"]
    has_bom = meta.get("bom", False)

    if target_enc == "UTF-8" and not has_bom:
        print(f"[restore] SKIP {filepath} - original was UTF-8 no-BOM, no action needed")
        return

    current_raw = Path(filepath).read_bytes()

    try:
        text = current_raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        print(
            f"[restore] WARNING: {filepath} is not valid UTF-8, falling back to latin-1 lossless decode",
            file=sys.stderr,
        )
        text = current_raw.decode("latin-1")

    _write_with_encoding(filepath, text, target_enc, has_bom)

    if not no_verify:
        ok = _round_trip_verify(filepath, target_enc, has_bom)
        status = "OK" if ok else "WARNING: round-trip decode failed - check file"
        print(f"[restore] {filepath} -> {target_enc} (bom={has_bom}) | {status}")
        if not ok:
            sys.exit(EXIT_WARNING)
    else:
        print(f"[restore] {filepath} -> {target_enc} (bom={has_bom})")


def verify(filepath: str) -> bool:
    meta_path = filepath + META_SUFFIX

    if not os.path.exists(meta_path):
        print(f"[verify] No snapshot for {filepath}")
        return False

    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[verify] ERROR: cannot read snapshot: {e}", file=sys.stderr)
        return False

    current = detect_encoding(filepath)
    enc_match = current["encoding"] == meta["encoding"]

    raw = Path(filepath).read_bytes()
    current_sha = _sha256(raw)
    orig_sha = meta.get("sha256", "")
    sha_match = current_sha == orig_sha

    enc_icon = "OK" if enc_match else "MISMATCH"
    sha_note = "unchanged since snapshot" if sha_match else "modified since snapshot"

    print(f"[verify] {filepath}")
    print(f"  encoding : {enc_icon}  current={current['encoding']}  snapshot={meta['encoding']}")
    print(f"  content  : {sha_note}")

    return enc_match


def fix(filepath: str, target: str, source_enc: str = None) -> None:
    raw = Path(filepath).read_bytes()
    target_upper = target.upper()

    if source_enc:
        decode_order = [source_enc, "latin-1"]
    elif any(k in target_upper for k in ("GBK", "BIG5", "SHIFT_JIS", "EUC")):
        decode_order = ["latin-1", "utf-8-sig", "utf-8"]
    else:
        decode_order = ["utf-8-sig", "gbk", "utf-8", "latin-1"]

    text = None
    used_enc = None
    for try_enc in decode_order:
        try:
            text = raw.decode(try_enc)
            used_enc = try_enc
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text is None:
        print(f"[fix] ERROR: cannot decode {filepath} with any attempted encoding", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    has_bom = "BOM" in target_upper
    _write_with_encoding(filepath, text, target_upper, has_bom)

    ok = _round_trip_verify(filepath, target_upper, has_bom)
    status = "OK" if ok else "WARNING: round-trip failed"
    print(f"[fix] {filepath}: decoded as {used_enc!r} -> re-encoded as {target_upper} | {status}")
    if not ok:
        sys.exit(EXIT_WARNING)


def scan(directory: str, extensions: list, filter_enc: str = None, output_json: bool = False, min_confidence: float = 0.0) -> list:
    exts = set(extensions) if extensions else DEFAULT_EXTENSIONS
    results = []

    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in exts:
            continue
        if path.name.endswith(META_SUFFIX):
            continue

        try:
            info = detect_encoding(str(path))
        except SystemExit:
            continue
        except Exception as e:
            print(f"[scan] ERROR reading {path}: {e}", file=sys.stderr)
            continue

        enc = info["encoding"]
        conf = info["confidence"]

        if filter_enc and enc.upper() != filter_enc.upper():
            continue
        if conf < min_confidence:
            continue

        entry = {"file": str(path), **info}
        results.append(entry)

        if not output_json:
            flag = "WARN" if conf < 0.8 else "OK"
            print(f"{flag:4s} {enc:16s} conf={conf:.2f}  {path}")

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    return results


def batch_snapshot(directory: str, extensions: list, dry_run: bool = False, force: bool = False) -> None:
    exts = set(extensions) if extensions else DEFAULT_EXTENSIONS
    count = skipped = errors = 0

    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in exts:
            continue
        if path.name.endswith(META_SUFFIX):
            continue

        try:
            info = detect_encoding(str(path))
        except SystemExit:
            errors += 1
            continue
        except Exception as e:
            print(f"[batch-snapshot] ERROR reading {path}: {e}", file=sys.stderr)
            errors += 1
            continue

        enc = info["encoding"]
        if enc in ("UTF-8", "BINARY_OR_UNKNOWN"):
            continue

        meta_path = str(path) + META_SUFFIX
        if os.path.exists(meta_path) and not force:
            skipped += 1
            continue

        if dry_run:
            print(f"[dry-run] would snapshot {path} ({enc}, conf={info['confidence']:.2f})")
        else:
            try:
                snapshot(str(path), force=force)
                count += 1
            except SystemExit:
                errors += 1

    print(f"[batch-snapshot] Done. snapshotted={count} skipped={skipped} errors={errors}")


def batch_restore(directory: str, dry_run: bool = False, no_verify: bool = False) -> None:
    count = errors = 0

    for meta_file in sorted(Path(directory).rglob(f"*{META_SUFFIX}")):
        original = str(meta_file)[:-len(META_SUFFIX)]
        if not os.path.exists(original):
            print(f"[batch] SKIP - source file not found: {original}")
            continue

        if dry_run:
            try:
                with open(meta_file, encoding="utf-8") as f:
                    meta = json.load(f)
                print(f"[dry-run] would restore {original} -> {meta['encoding']}")
            except Exception as e:
                print(f"[dry-run] ERROR reading {meta_file}: {e}", file=sys.stderr)
            continue

        try:
            restore(original, no_verify=no_verify)
            count += 1
        except SystemExit:
            errors += 1

    print(f"[batch] Done. restored={count} errors={errors}")


def status(directory: str) -> None:
    found = 0
    for meta_file in sorted(Path(directory).rglob(f"*{META_SUFFIX}")):
        original = str(meta_file)[:-len(META_SUFFIX)]
        found += 1
        if not os.path.exists(original):
            print(f"  MISSING  {original}")
            continue
        verify(original)
        print()

    if found == 0:
        print(f"[status] No snapshots found in {directory}")


def clean(directory: str, dry_run: bool = False) -> None:
    count = 0
    for meta_file in sorted(Path(directory).rglob(f"*{META_SUFFIX}")):
        if dry_run:
            print(f"[dry-run] would remove {meta_file}")
        else:
            meta_file.unlink()
            print(f"[clean] removed {meta_file}")
        count += 1

    action = "would remove" if dry_run else "removed"
    print(f"[clean] Done. {action} {count} snapshot file(s)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Encoding Guardian v{VERSION} - protect legacy source file encodings"
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("detect", help="Print encoding info for a file")
    p.add_argument("file")

    p = sub.add_parser("snapshot", help="Save encoding metadata to .enc_meta")
    p.add_argument("file")
    p.add_argument("--force", action="store_true", help="Overwrite existing snapshot")

    p = sub.add_parser("restore", help="Restore encoding from .enc_meta")
    p.add_argument("file")
    p.add_argument("--no-verify", action="store_true", help="Skip round-trip verification")

    p = sub.add_parser("verify", help="Check current encoding + SHA-256 against snapshot")
    p.add_argument("file")

    p = sub.add_parser("fix", help="Force re-encode a possibly corrupted file")
    p.add_argument("file")
    p.add_argument("--enc", default="UTF-8", help="Target encoding")
    p.add_argument("--from-enc", default=None, help="Source decode encoding override")

    p = sub.add_parser("scan", help="Audit encodings in a directory")
    p.add_argument("dir")
    p.add_argument("--ext", nargs="*", help="File extensions e.g. .cpp .h .hlsl")
    p.add_argument("--filter", dest="filter_enc", default=None, help="Only show matching encoding")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("--min-confidence", type=float, default=0.0, help="Exclude low confidence results")

    p = sub.add_parser("batch-snapshot", help="Snapshot all non-UTF-8 files in a directory")
    p.add_argument("dir")
    p.add_argument("--ext", nargs="*")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="Overwrite existing snapshots")

    p = sub.add_parser("batch", help="Batch restore all snapshots in a directory")
    p.add_argument("dir")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-verify", action="store_true")

    p = sub.add_parser("status", help="Show state of all snapshots")
    p.add_argument("dir")

    p = sub.add_parser("clean", help="Remove all .enc_meta files after a verified session")
    p.add_argument("dir")
    p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "detect":
        info = detect_encoding(args.file)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    elif args.cmd == "snapshot":
        snapshot(args.file, force=args.force)
    elif args.cmd == "restore":
        restore(args.file, no_verify=args.no_verify)
    elif args.cmd == "verify":
        ok = verify(args.file)
        sys.exit(EXIT_OK if ok else EXIT_WARNING)
    elif args.cmd == "fix":
        fix(args.file, args.enc, source_enc=args.from_enc)
    elif args.cmd == "scan":
        scan(
            args.dir,
            args.ext,
            filter_enc=args.filter_enc,
            output_json=args.json,
            min_confidence=args.min_confidence,
        )
    elif args.cmd == "batch-snapshot":
        batch_snapshot(args.dir, args.ext, dry_run=args.dry_run, force=args.force)
    elif args.cmd == "batch":
        batch_restore(args.dir, dry_run=args.dry_run, no_verify=args.no_verify)
    elif args.cmd == "status":
        status(args.dir)
    elif args.cmd == "clean":
        clean(args.dir, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
