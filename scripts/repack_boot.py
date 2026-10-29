#!/usr/bin/env python3
"""用官方 boot.img 作模板，替换其中的 kernel，生成新的 boot.img。

pdx234 的 boot.img 是 Android boot image header v4：
  offset 0     : 1584 字节 header
  offset 4096  : kernel（页面对齐）
  ramdisk_size = 0（GKI：通用 ramdisk 在 init_boot 里）

原始 boot.img 末尾带 AVB footer（"AVBf" 魔数 + 64 字节），
解锁 bootloader 后不需要 AVB，重打包时直接丢弃。
"""
import struct
import sys


def main(src: str, image: str, out: str) -> None:
    data = open(src, "rb").read()
    print(f"模板: {src} 大小={len(data)}")

    avb = data.find(b"AVBf")
    if avb > 0:
        print(f"丢弃 AVB footer @ {avb}")
        data = data[:avb]

    if data[:8] != b"ANDROID!":
        raise SystemExit(f"不是 Android boot image: {data[:8]!r}")

    kernel_size, ramdisk_size, os_version, header_size = struct.unpack("<IIII", data[8:24])
    header_version = struct.unpack("<I", data[40:44])[0]
    print(
        f"kernel_size={kernel_size} ramdisk_size={ramdisk_size} "
        f"header_version={header_version} header_size={header_size}"
    )
    if header_version != 4:
        raise SystemExit(f"只支持 header v4，实际 {header_version}")
    if ramdisk_size != 0:
        raise SystemExit(f"预期 ramdisk_size=0，实际 {ramdisk_size}")

    new_kernel = open(image, "rb").read()
    print(f"新 kernel: {image} 大小={len(new_kernel)}")

    header = bytearray(data[:4096])
    struct.pack_into("<I", header, 8, len(new_kernel))   # kernel_size
    struct.pack_into("<I", header, 12, 0)                # ramdisk_size 保持 0

    blob = bytearray(header)
    blob += new_kernel
    blob += b"\x00" * ((-len(blob)) % 4096)

    with open(out, "wb") as fh:
        fh.write(blob)
    print(f"写出: {out} 大小={len(blob)} (分区 0x6000000=100663296)")
    if len(blob) > 0x6000000:
        raise SystemExit("镜像超过 boot 分区大小！")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("用法: repack_boot.py <stock-boot.img> <Image> <out-boot.img>")
    main(*sys.argv[1:])
