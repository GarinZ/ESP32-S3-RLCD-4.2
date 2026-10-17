# AGENTS.md

## 项目目标

基于 **微雪 Waveshare ESP32-S3-RLCD-4.2** 全反射屏 AIoT 开发板进行软硬件开发。我们已采购该设备（V2 版本，自 2026-10-10 起出货），本仓库用于承载该硬件的固件、示例、外壳/结构设计及相关工程。

主要开发方向（按需推进）：

- 固件开发（Arduino 或 ESP-IDF）
- 屏幕（RLCD 4.2" 300×400）显示应用 / LVGL UI
- 音频（ES7210 双麦克风 + ES8311 编解码）与 AI 语音（小智 AI）
- 传感器应用（SHTC3 温湿度、PCF85063 RTC）
- 结构/外壳设计（注意 V1/V2 尺寸差异）

## 硬件关键信息

- SoC：ESP32-S3-WROOM-1-N16R8（双核 240 MHz，16MB Flash + 8MB PSRAM，Wi-Fi + BLE 5）
- 屏幕：4.2" RLCD 全反射屏，300×400，无背光（环境光反射成像）
- 外设：ES7210（双麦克风阵列/回声消除）、ES8311（音频编解码）、SHTC3（温湿度）、PCF85063（RTC）、Micro SD 卡槽、18650 电池座 + RTC 备用电池座、扬声器接口（MX1.25 2PIN）、2×8 排母（2.54mm）
- 按键：PWR（单击开机/长按关机）、BOOT（按住重新上电进入下载模式）、KEY（自定义）
- 版本：V2 隔板加厚（液晶与亚克力间距 3.75→4.35 mm，总厚度 13.50→14.1 mm），其余与 V1 一致，以 QC 标签区分

> ⚠️ 屏幕为精密易碎部件，装配/搬运严禁以屏幕为受力点，避免跌落碰撞。

## 文档索引

文档原文已导出到 `doc/` 目录，图片资源在 `doc/assets/`。导出脚本：`doc/_export.py`（可重跑以同步上游更新）。

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| [doc/01-overview.md](doc/01-overview.md) | 产品概览、版本兼容性、产品特性、资源/接口介绍、V1/V2 产品尺寸、开发方式 | https://docs.waveshare.net/ESP32-S3-RLCD-4.2 |
| [doc/02-resources-and-documents.md](doc/02-resources-and-documents.md) | 示例程序、硬件资料（原理图/V1/V2 结构与尺寸）、技术手册、社区示例 | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/Resources-And-Documents |
| [doc/03-arduino.md](doc/03-arduino.md) | Arduino IDE 环境搭建、库安装（LVGL/SensorLib/U8g2）、工程参数、示例程序清单 | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/Arduino |
| [doc/04-esp-idf.md](doc/04-esp-idf.md) | ESP-IDF 环境搭建（VS Code）、示例程序 | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/ESP-IDF |
| [doc/05-xiaozhi-ai.md](doc/05-xiaozhi-ai.md) | 小智 AI 应用教程（无/有开发环境烧录固件） | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/XiaoZhi_AI |
| [doc/06-faq.md](doc/06-faq.md) | 产品 FAQ（电池、功耗、RTC 电池、烧录失败、环境搭建等） | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/FAQ |
| [doc/07-technical-support.md](doc/07-technical-support.md) | 技术支持 / 售后联系方式 | https://docs.waveshare.net/ESP32-S3-RLCD-4.2/Technical-Support |

## 关键外部资源

- 示例程序（含 Arduino/ESP-IDF 示例与库）：
  - Gitee：https://gitee.com/waveshare/ESP32-S3-RLCD-4.2
  - GitHub：https://github.com/waveshareteam/ESP32-S3-RLCD-4.2
  - 下载包：https://files.waveshare.net/wiki/ESP32-S3-RLCD-4.2/ESP32-S3-RLCD-4.2-Demo.zip
- 原理图：https://www.waveshare.net/w/upload/e/e6/ESP32-S3-RLCD-4.2-schematic.pdf
- V2 结构与尺寸：https://www.waveshare.net/w/upload/9/91/ESP32-S3-RLCD-4.2_20261010.zip

## 开发约定

- 环境版本：Arduino-ESP32 v3.3.x（仓库验证 3.3.12）；ESP-IDF v5.5.x（仓库验证 5.5.5）
- 关键库版本：LVGL v9.3.0、SensorLib v0.3.1、U8g2 v2.36.18（版本强相关，勿混用 LVGL v8/v9 驱动）
- 尺寸/结构相关：以实收产品实测为准，V1/V2 外壳不通用。
