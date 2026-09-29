"""Read the hyper-parameters stored in a remote PyTorch Lightning checkpoint without downloading it.

Usage:  ..\\.venv\\Scripts\\python.exe inspect_ckpt_hparams.py <url>

A .ckpt is a zip; this fetches the zip directory and the small `data.pkl` entry with HTTP range
requests and lists its strings. It never unpickles (no code execution), it only scans the bytes.
"""
import re
import struct
import sys
import urllib.request
import zlib


def fetch(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def main():
    url = sys.argv[1]
    head = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"))
    size = int(head.headers["Content-Length"])
    tail = fetch(url, max(0, size - 65536), size - 1)
    eocd = tail.rfind(b"PK\x05\x06")
    zip64 = tail.rfind(b"PK\x06\x06")
    if zip64 != -1:  # ZIP64 end of central directory
        cd_size, cd_off = struct.unpack("<QQ", tail[zip64 + 40:zip64 + 56])
    else:
        cd_size, cd_off = struct.unpack("<II", tail[eocd + 12:eocd + 20])
    cd = fetch(url, cd_off, cd_off + cd_size - 1)
    i = 0
    while i < len(cd) and cd[i:i + 4] == b"PK\x01\x02":
        method, = struct.unpack("<H", cd[i + 10:i + 12])
        csize, usize = struct.unpack("<II", cd[i + 20:i + 28])
        nlen, xlen, clen = struct.unpack("<HHH", cd[i + 28:i + 34])
        loff, = struct.unpack("<I", cd[i + 42:i + 46])
        name = cd[i + 46:i + 46 + nlen].decode()
        extra = cd[i + 46 + nlen:i + 46 + nlen + xlen]
        if 0xFFFFFFFF in (csize, usize, loff):  # ZIP64 extra field
            vals = list(struct.unpack("<" + "Q" * ((len(extra) - 4) // 8), extra[4:4 + (len(extra) - 4) // 8 * 8]))
            if usize == 0xFFFFFFFF: usize = vals.pop(0)
            if csize == 0xFFFFFFFF: csize = vals.pop(0)
            if loff == 0xFFFFFFFF: loff = vals.pop(0)
        if name.endswith("data.pkl"):
            lh = fetch(url, loff, loff + 29)
            lnlen, lxlen = struct.unpack("<HH", lh[26:30])
            data = fetch(url, loff + 30 + lnlen + lxlen, loff + 30 + lnlen + lxlen + csize - 1)
            if method == 8:
                data = zlib.decompress(data, -15)
            print(f"{name}: {len(data)} bytes (checkpoint {size / 2**20:.1f} MB)")
            strings = [s.decode("utf-8", "replace") for s in re.findall(rb"[\x20-\x7e]{3,}", data)]
            print("strings:", " | ".join(dict.fromkeys(strings)))
            return
        i += 46 + nlen + xlen + clen
    print("data.pkl not found")


if __name__ == "__main__":
    main()
