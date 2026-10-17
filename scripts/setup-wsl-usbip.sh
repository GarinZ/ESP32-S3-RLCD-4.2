#!/usr/bin/env bash
# WSL2 USB/IP 客户端侧配置（需以 root 运行：sudo bash scripts/setup-wsl-usbip.sh）
# 用途：让 Windows 侧的 usbipd-win 能把 ESP32-S3（USB-Serial-JTAG，VID 303A）透传进 WSL。
set -euo pipefail

echo "==> [1/4] 安装 usbip 用户态工具 + USB 设备名数据库"
apt-get update
apt-get install -y linux-tools-generic hwdata

echo "==> [2/4] 加载 vhci-hcd 内核模块（USB/IP 客户端）"
modprobe vhci-hcd

echo "==> [3/4] 开机自动加载 vhci-hcd（WSL 每次重启内核模块会复位）"
echo "vhci-hcd" > /etc/modules-load.d/vhci-hcd.conf

echo "==> [4/4] udev 规则：Espressif(303A) 设备对 plugdev/dialout 组放开权限"
cat > /etc/udev/rules.d/99-esp32-usb.rules <<'EOF'
# Espressif USB-Serial-JTAG / USB-OTG / DFU
SUBSYSTEM=="usb", ATTR{idVendor}=="303a", GROUP="plugdev", MODE="0660"
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", GROUP="dialout", MODE="0660", SYMLINK+="ttyESP32"
EOF
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

echo
echo "==> 校验结果"
if [ -d /sys/devices/platform/vhci_hcd.0 ]; then
  echo "  [OK] vhci-hcd 已加载"
else
  echo "  [!!] vhci-hcd 未就绪，请检查 modprobe 输出"
fi
command -v usbip >/dev/null && { echo "  [OK] usbip: $(usbip version 2>&1 | head -1)"; }
echo
echo "完成。接下来在 Windows PowerShell 里执行 usbipd-win 的 bind/attach（见项目文档或对话）。"
