#!/usr/bin/env python3
"""Generate web images and data/photos.json for the portfolio.

Usage:
  python scripts/process_photos.py                 # sync the "网站" album from Photos.app
  python scripts/process_photos.py --album NAME    # sync a different album
  add --force to regenerate everything, --dry-run to only print what would happen

Rules (see CLAUDE.md):
  - The album is the only source: data/photos.json holds exactly the album's photos.
  - Display order is the album order reversed: the last photo in the album is shown first.
  - A photo removed from the album is deleted from photos.json and photos/ (re-adding it
    regenerates it). Files in photos/ that belong to no photo are deleted too.
  - Titles come from the photo's title in Photos.app.
  - photos/cover.jpg (share preview) is made from the first landscape photo on the page.
  - A photo that fails to export is skipped and reported; the rest of the sync still runs.
"""

import argparse
import io
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "photos.json"
OUT_DIR = ROOT / "photos"

DEFAULT_ALBUM = "网站"
SIZES = [400, 800, 1600, 2400]  # long edge in px
FALLBACK_SIZE = 1600            # long edge of the JPEG fallback
WEBP_QUALITY = 82
JPEG_QUALITY = 85
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
COVER_FILE = OUT_DIR / "cover.jpg"
COVER_SIZE = (1200, 630)        # standard share-preview (Open Graph) size

# HDR photos carry a gain map; these byte strings identify the formats we know.
GAIN_MAP_MARKERS = (b"urn:iso:std:iso:ts:21496", b"hdrgainmap", b"HDRGainMap", b"hdrgm")
HDR_HELPER_SRC = ROOT / "scripts" / "hdr_gainmap.swift"
HDR_HELPER_BIN = ROOT / ".venv" / "bin" / "hdr_gainmap"


# ---------- data file ----------

def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"version": 1, "photos": []}


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def new_entry(photo_id, uuid):
    return {"id": photo_id, "source": {"type": "photos", "uuid": uuid}}


# ---------- image processing ----------

def target_sizes(long_edge):
    sizes = [s for s in SIZES if s < long_edge]
    top = min(long_edge, SIZES[-1])
    if top not in sizes:
        sizes.append(top)
    return sizes


def output_paths(photo_id, sizes, hdr=False):
    paths = [OUT_DIR / f"{photo_id}-{s}.webp" for s in sizes]
    paths.append(OUT_DIR / f"{photo_id}.jpg")
    if hdr:
        paths += [OUT_DIR / f"{photo_id}-{s}-hdr.jpg" for s in sizes]
    return paths


def outputs_exist(entry):
    sizes = entry.get("sizes")
    return bool(sizes) and all(p.exists() for p in output_paths(entry["id"], sizes, entry.get("hdr")))


def remove_outputs(photo_id):
    # Exact pattern, so removing "DSCF3638" leaves "DSCF3638-3" alone.
    own = re.compile(rf"{re.escape(photo_id)}(-\d+\.webp|-\d+-hdr\.jpg|\.jpg)")
    for p in OUT_DIR.iterdir():
        if own.fullmatch(p.name):
            p.unlink()


def sweep_outputs(photos, dry_run):
    """Delete files in photos/ that belong to no photo (removed photos, old leftovers)."""
    expected = {COVER_FILE}
    for e in photos:
        expected.update(output_paths(e["id"], e.get("sizes", []), e.get("hdr")))
    stray = sorted(p for p in OUT_DIR.iterdir() if p.is_file() and p not in expected)
    for p in stray:
        if not dry_run:
            p.unlink()
    return len(stray)


def make_cover(photos, dry_run):
    """photos/cover.jpg: 1200x630 crop of the first landscape photo, in sRGB for social apps."""
    if not photos:
        return None
    chosen = next((e for e in photos if e["width"] > e["height"]), photos[0])
    if dry_run:
        return chosen["id"]
    with Image.open(OUT_DIR / f"{chosen['id']}-{chosen['sizes'][-1]}.webp") as im:
        icc = im.info.get("icc_profile")
        im = im.convert("RGB")
        if icc:
            im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                                           ImageCms.createProfile("sRGB"), outputMode="RGB")
        ImageOps.fit(im, COVER_SIZE, Image.LANCZOS).save(COVER_FILE, "JPEG", quality=JPEG_QUALITY,
                                                         optimize=True, progressive=True)
    return chosen["id"]


# ---------- HDR ----------

def has_gain_map(path):
    data = Path(path).read_bytes()
    return any(m in data for m in GAIN_MAP_MARKERS)


def hdr_helper():
    """Path to the compiled Swift helper, building it if needed; None if Swift is unavailable."""
    if HDR_HELPER_BIN.exists() and HDR_HELPER_BIN.stat().st_mtime >= HDR_HELPER_SRC.stat().st_mtime:
        return HDR_HELPER_BIN
    print("  编译 HDR 辅助程序（只在第一次或脚本更新后进行）…", flush=True)
    try:
        subprocess.run(["swiftc", "-O", str(HDR_HELPER_SRC), "-o", str(HDR_HELPER_BIN)],
                       check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as err:
        print(f"    ✗ 无法编译（{getattr(err, 'stderr', '') or err}），HDR 照片将只生成普通版本")
        return None
    return HDR_HELPER_BIN


def render_hdr(src_path, photo_id, sizes):
    """Write {id}-{size}-hdr.jpg (normal image + ISO 21496-1 gain map). Returns True on success."""
    helper = hdr_helper()
    if not helper:
        return False
    result = subprocess.run([str(helper), str(src_path), str(OUT_DIR / photo_id), str(JPEG_QUALITY / 100),
                             *map(str, sizes)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ✗ HDR 版本生成失败：{result.stderr.strip()}，只保留普通版本")
        return False
    return True


def resized(im, long_edge):
    w, h = im.size
    scale = long_edge / max(w, h)
    if scale >= 1:
        return im
    return im.resize((round(w * scale), round(h * scale)), Image.LANCZOS, reducing_gap=3.0)


def render(src_path, photo_id):
    """Write all web versions of src_path. Returns (width, height, sizes, exif, hdr)."""
    with Image.open(src_path) as raw:
        exif = read_exif(raw)
        icc = raw.info.get("icc_profile")
        im = ImageOps.exif_transpose(raw)  # bake rotation into pixels
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.load()

    w, h = im.size
    sizes = target_sizes(max(w, h))
    OUT_DIR.mkdir(exist_ok=True)
    remove_outputs(photo_id)
    # Only the colour profile is kept; all other metadata (incl. GPS) is dropped.
    for s in sizes:
        resized(im, s).save(OUT_DIR / f"{photo_id}-{s}.webp", "WEBP",
                            quality=WEBP_QUALITY, method=5, icc_profile=icc)
    resized(im, FALLBACK_SIZE).save(OUT_DIR / f"{photo_id}.jpg", "JPEG",
                                    quality=JPEG_QUALITY, optimize=True, progressive=True,
                                    icc_profile=icc)
    hdr = has_gain_map(src_path) and render_hdr(src_path, photo_id, sizes)
    return w, h, sizes, exif, hdr


# ---------- EXIF ----------

def fmt_shutter(t):
    if not t:
        return None
    t = float(t)
    if t >= 1:
        return f"{t:g}s"
    return f"1/{round(1 / t)}"


def fmt_num(x):
    if x is None:
        return None
    x = round(float(x), 1)
    return int(x) if x.is_integer() else x


def camera_name(make, model):
    make, model = (make or "").strip(), (model or "").strip()
    if not model:
        return make or None
    if make and not model.lower().startswith(make.split()[0].lower()):
        return f"{make} {model}"
    return model


def read_exif(im):
    ex = im.getexif()
    sub = ex.get_ifd(0x8769)
    taken = sub.get(0x9003) or ex.get(0x0132)
    if taken:
        try:
            taken = datetime.strptime(taken.strip(), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            taken = None
    iso = sub.get(0x8827)
    if isinstance(iso, tuple):
        iso = iso[0]
    return {
        "takenAt": taken,
        "camera": camera_name(ex.get(0x010F), ex.get(0x0110)),
        "lens": (sub.get(0xA434) or "").strip() or None,
        "focalLength": fmt_num(sub.get(0x920A)),
        "aperture": fmt_num(sub.get(0x829D)),
        "shutter": fmt_shutter(sub.get(0x829A)),
        "iso": int(iso) if iso else None,
    }


def exif_from_photos(photo):
    """Fallback when the exported file has no EXIF."""
    e = photo.exif_info
    if not e:
        return {}
    return {
        "takenAt": photo.date.replace(tzinfo=None).isoformat(timespec="seconds") if photo.date else None,
        "camera": camera_name(e.camera_make, e.camera_model),
        "lens": e.lens_model,
        "focalLength": fmt_num(e.focal_length),
        "aperture": fmt_num(e.aperture),
        "shutter": fmt_shutter(e.shutter_speed),
        "iso": e.iso,
    }


def apply_render(entry, src_path, fallback_exif=None):
    w, h, sizes, exif, hdr = render(src_path, entry["id"])
    if fallback_exif:
        exif = {k: exif.get(k) or fallback_exif.get(k) for k in set(exif) | set(fallback_exif)}
    entry["width"], entry["height"], entry["sizes"] = w, h, sizes
    if hdr:
        entry["hdr"] = True
    else:
        entry.pop("hdr", None)
    entry["takenAt"] = exif.pop("takenAt", None)
    entry["exif"] = {k: v for k, v in exif.items() if v is not None}


# ---------- Photos.app album sync ----------

def photos_fingerprint(photo):
    if photo.hasadjustments:
        modified = photo.date_modified or photo.date
        return f"edited@{modified.isoformat()}"
    return "original"


# Photos.app exports the current version (edits applied) as JPEG and downloads
# iCloud-only originals on the way. osxphotos' own iCloud download path silently
# returned nothing here, so we call AppleScript directly.
PHOTOS_EXPORT_SCRIPT = """
on run argv
  set destFolder to POSIX file (item 2 of argv)
  tell application "Photos"
    with timeout of 600 seconds
      export {media item id ((item 1 of argv) & "/L0/001")} to destFolder
    end timeout
  end tell
end run
"""


def export_from_photos(photo, tmpdir):
    """Return a full-size image file of the photo's current version (edits applied)."""
    local = photo.path_edited if photo.hasadjustments else photo.path
    if local and Path(local).suffix.lower() in IMAGE_EXTS and Path(local).exists():
        return Path(local)  # already on disk in a format Pillow reads

    dest = Path(tmpdir) / photo.uuid
    dest.mkdir(exist_ok=True)
    result = subprocess.run(["osascript", "-", photo.uuid, str(dest)], input=PHOTOS_EXPORT_SCRIPT,
                            capture_output=True, text=True, timeout=700)
    files = [f for f in dest.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    if result.returncode != 0 or not files:
        raise RuntimeError(result.stderr.strip() or "照片 App 没有导出任何文件")
    return files[0]


def unique_id(base, uuid, by_id):
    entry = by_id.get(base)
    if entry is None or entry["source"].get("uuid") == uuid:
        return base
    return f"{base}-{uuid[:6]}"


def sync_album(data, album_name, force, dry_run):
    try:
        import osxphotos
    except ImportError:
        sys.exit("缺少 osxphotos，请先运行 ./update.sh（会自动安装依赖）")

    try:
        db = osxphotos.PhotosDB()
    except (FileNotFoundError, PermissionError):
        sys.exit("读不到照片图库。请在 系统设置 → 隐私与安全性 → 完全磁盘访问权限 中"
                 "打开你运行脚本的程序（终端 / VS Code），然后重启该程序。")

    albums = [a for a in db.album_info if a.title == album_name]
    if not albums:
        sys.exit(f"照片 App 里没有找到名为「{album_name}」的相簿。")
    album_photos = [p for p in albums[0].photos if not p.ismovie]

    by_uuid = {e["source"].get("uuid"): e for e in data["photos"] if e["source"].get("type") == "photos"}
    by_id = {e["id"]: e for e in data["photos"]}
    stats = {"new": 0, "updated": 0, "skipped": 0, "removed": 0, "failed": 0}
    ordered = []

    with tempfile.TemporaryDirectory() as tmp:
        for photo in album_photos:
            fingerprint = photos_fingerprint(photo)
            previous = by_uuid.get(photo.uuid)
            if previous is None:
                photo_id = unique_id(Path(photo.original_filename).stem.replace(" ", "_"), photo.uuid, by_id)
                entry = new_entry(photo_id, photo.uuid)
                by_id[photo_id] = entry
                status = "新增"
            else:
                entry = previous
                unchanged = entry["source"].get("fingerprint") == fingerprint and outputs_exist(entry)
                status = None if unchanged and not force else "更新"

            if status:
                print(f"  {status} {photo.original_filename}", flush=True)
                if not dry_run:
                    try:
                        exported = export_from_photos(photo, tmp)
                        apply_render(entry, exported, exif_from_photos(photo))
                    except Exception as err:  # keep going; report at the end
                        print(f"    ✗ 失败：{err}")
                        stats["failed"] += 1
                        if previous is None:
                            del by_id[entry["id"]]
                            continue
                        entry = previous  # keep the old version on the site
                        ordered.append(entry)
                        continue
                    entry["source"] = {"type": "photos", "uuid": photo.uuid, "fingerprint": fingerprint}
                stats["new" if status == "新增" else "updated"] += 1
            else:
                stats["skipped"] += 1
            title = (photo.title or "").strip()
            if title:
                entry["title"] = title
            else:
                entry.pop("title", None)
            ordered.append(entry)

    kept = {e["id"] for e in ordered}
    for e in data["photos"]:
        if e["id"] not in kept:
            print(f"  删除 {e['id']}（已不在相簿中）")
            stats["removed"] += 1
    if not dry_run:
        data["photos"] = ordered[::-1]  # newest addition (end of album) first
    return stats, len(ordered)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--album", default=DEFAULT_ALBUM, help=f"照片 App 相簿名（默认：{DEFAULT_ALBUM}）")
    ap.add_argument("--force", action="store_true", help="全部重新生成")
    ap.add_argument("--dry-run", action="store_true", help="只显示会做什么，不写任何文件")
    args = ap.parse_args()

    data = load_data()
    print(f"同步照片 App 相簿：{args.album}")
    stats, shown = sync_album(data, args.album, args.force, args.dry_run)

    if not args.dry_run:
        data["cover"] = make_cover(data["photos"], args.dry_run)
        save_data(data)
    stray = sweep_outputs(data["photos"], args.dry_run)
    labels = {"new": "新增", "updated": "更新", "skipped": "未变", "removed": "删除", "failed": "失败"}
    print("完成：" + "，".join(f"{labels[k]} {v}" for k, v in stats.items()))
    print(f"网站将显示 {shown} 张照片" + (f"；清理 photos/ 里不再使用的文件 {stray} 个" if stray else ""))
    if stats.get("failed"):
        print("有照片处理失败（见上面的 ✗），修好后再运行一次即可，已成功的不会重复处理。")


if __name__ == "__main__":
    main()
