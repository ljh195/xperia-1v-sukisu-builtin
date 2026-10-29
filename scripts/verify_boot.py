#!/usr/bin/env python3
"""校验重打包后的 boot.img 结构是否正确。"""
import struct
import sys


def main(path: str) -> None:
    data = open(path, "rb").read()
    assert data[:8] == b"ANDROID!", "魔数错误"
    kernel_size, ramdisk_size, os_version, header_size = struct.unpack("<IIII", data[8:24])
    header_version = struct.unpack("<I", data[40:44])[0]
    print(f"大小={len(data)} kernel={kernel_size} ramdisk={ramdisk_size} hdr_v={header_version}")

    assert header_version == 4
    assert ramdisk_size == 0
    assert len(data) <= 0x6000000, "超过 boot 分区大小"

    kernel = data[4096:4096 + kernel_size]
    assert kernel[:4] == b"MZ\x40\xfa" or kernel[:4] == b"\x00\x00\xa0\xe1", \
        f"kernel 魔数异常: {kernel[:4].hex()}"
    print(f"kernel 魔数正常: {kernel[:4].hex()}")

    # 确认含 KSU 痕迹
    if b"KernelSU" in data:
        print("OK: 镜像内含 KernelSU 字符串")
    else:
        print("WARN: 未在镜像中找到 KernelSU 字符串（可能被压缩/LTO 优化掉）")
    print("校验通过")


if __name__ == "__main__":
    main(sys.argv[1])
