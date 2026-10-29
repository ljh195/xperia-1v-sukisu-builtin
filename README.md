# SukiSU builtin kernel — Sony Xperia 1 V (pdx234)

把 **SukiSU Ultra 直接编进内核**（`CONFIG_KSU=y`），产出 `Image` 和可直接 `fastboot flash boot` 的 `boot-new.img`。

## 为什么不用 LKM

官方预编译的 `android14-5.15_kernelsu.ko`（vermagic `5.15.202-dirty`）在本机
（内核 `5.15.211-gdb39b3851f98`，LineageOS 24.0）上**会导致无限重启**，
并且因为 `init_boot` 里的 `init` 被替换后加载失败，连 recovery / fastbootd 都起不来。

所以改成把 KSU 编进内核，只替换 `boot`（内核），**不碰 `init_boot`**，风险低得多。

## 目标环境

| 项目 | 值 |
|---|---|
| 机型 | Sony Xperia 1 V（XQ-DQ72 / pdx234） |
| 系统 | LineageOS 24.0 NIGHTLY `24.0-20261025-NIGHTLY-pdx234` |
| 内核 | 5.15.211-gdb39b3851f98（GKI 5.15） |
| 源码 | `LineageOS/android_kernel_sony_sm8550` @ `db39b3851f98` |
| 配置 | 设备 `/proc/config.gz`（提取自官方 `boot.img` 的 `IKCFG_ST` 段） |
| 工具链 | LLVM 22（对齐设备 clang 22.0.2） |

## 关键点

- `LOCALVERSION="-gdb39b3851f98"` + `LOCALVERSION_AUTO=n`，保证 vermagic 与设备**逐字一致**，
  否则 364 个 vendor `.ko`（WLAN / 相机 / 音频…）全部加载失败
- 使用设备原始配置，不改动任何其他选项，保证导出符号 CRC（`MODVERSIONS`）一致
- 用 clang 22 而非 18/19，避免 CFI 类型哈希不一致
- 重打包时丢弃 AVB footer（bootloader 已解锁，不校验）

## 产物

- `Image` — 裸内核
- `boot-new.img` — 已重打包，可直接刷入

## 刷入

```bash
adb reboot bootloader
fastboot flash boot boot-new.img
fastboot reboot
```

刷回原厂内核：

```bash
# 用官方 boot.img（LineageOS 镜像站可直接下）
curl -LO https://mirrorbits.lineageos.org/full/pdx234/20261025/boot.img
fastboot flash boot boot.img
```

> ⚠️ 只写 `boot`，**不要动 `init_boot`**。`init_boot` 被写坏会导致正常启动、
> recovery、fastbootd 全部失效（本次事故即由此产生），只能靠切到另一个 slot 抢救。
