---
title: "USB 协议详解"
author: "王思成"
date: "Apr 26, 2026"
description: "USB 协议从基础拓扑到高级传输全面解析"
latex: true
pdf: true
---


在日常生活中，USB 接口无处不在，它是我们手机充电的必需品、键盘鼠标的连接桥梁、外接硬盘的数据通道，几乎所有电子设备都依赖它来实现即插即用的便利性。想象一下，没有 USB，我们将如何高效地传输数据或供电？正因如此，深入了解 USB 协议变得尤为重要，它不仅是硬件工程师设计外围设备的基石，更是嵌入式开发者编写驱动的指南针，还能帮助驱动程序员调试复杂系统问题。本文将带领读者从零基础起步，逐步掌握 USB 协议的核心机制，直至高级应用，帮助你构建完整的知识体系。

USB 的发展历程堪称传奇。从 1996 年的 USB 1.0 开始，它以 1.5 Mbps 和 12 Mbps 的速度解决了早期 PC 端口杂乱的问题；2000 年的 USB 2.0 提升至 480 Mbps，成为高性能标配；2008 年和 2013 年的 USB 3.0/3.1 分别达到 5 Gbps 和 10 Gbps，引入 SuperSpeed 概念；2019 年的 USB4 更是飙升至 40 Gbps，并兼容 Thunderbolt 3，支持 DisplayPort 和 Power Delivery 等功能。这一时间线见证了 USB 从简单总线向多功能生态的演变。

阅读本文前，读者需具备基本的数字电路知识，如比特传输和时序概念。这些将帮助你理解物理层信号。如果你对这些不熟，不妨先复习一下。接下来，我们将按协议层级和历史脉络展开讨论，从基础拓扑到高级特性，全方位解析 USB 的奥秘。

## USB 协议基础

USB，全称 Universal Serial Bus，即通用串行总线，是一种支持即插即用、热插拔和多设备级联的串行总线标准。它彻底改变了 PC 外围设备的连接方式，让用户无需开关机即可添加设备。USB 的核心在于树状拓扑结构，以主机（Host）为中心，通过集线器（Hub）扩展到多个设备（Device），采用严格的主从架构：主机掌控一切调度，设备被动响应。这种设计确保了总线的有序性和可扩展性。

物理层接口经历了多次演进，早期的 Type-A 和 Type-B 设计为固定角色，后来 Micro-USB 缩小体积适应移动设备，而如今的 Type-C 以其对称形状和多功能性主导市场。这些接口内部包含 VBUS 电源线、GND 地线，以及数据线 D+ 和 D-，USB 3.x 进一步增加 TX+、TX-、RX+、RX- 等差分对以支持更高速度。

不同 USB 版本在性能和特性上存在显著差异。USB 1.x 于 1996 年发布，最大速度为 1.5 Mbps（低速）和 12 Mbps（全速），适用于键盘鼠标等低带宽设备。2000 年的 USB 2.0 引入高速模式达 480 Mbps，成为十年标杆。2008 年的 USB 3.0 实现 5 Gbps 的 SuperSpeed，2013 年的 USB 3.1 升级至 10 Gbps SuperSpeed+。最新 USB4 于 2019 年推出，支持 40 Gbps，并集成 Thunderbolt 3 协议、DisplayPort 输出和 PD 充电。这些版本的线缆差异主要体现在差分对数量上：USB 2.0 仅需一对数据线，而 USB 3.x 需要四对独立对以实现全双工传输。

USB 的拓扑结构严格限定为树状：一台主机通过根集线器连接多个设备或子集线器，每层 Hub 最多扩展多个端口，但总层级不得超过 7 层，总设备数上限为 127 个（减去 Hub 占用）。这种设计平衡了扩展性和管理复杂度，避免了总线冲突。主机通常集成在 PC 芯片组中，负责时钟同步和流量控制，而 Hub 提供电源管理和信号中继，设备则通过唯一地址响应主机命令。

## USB 物理层（PHY）详解

USB 物理层负责比特级的信号传输，主要依赖差分信号机制。数据通过 D+ 和 D- 两线差分传输，实现全双工或半双工通信；VBUS 提供 5V 电源，GND 为参考地。在 USB 2.0 中，D+/D- 承担所有数据和控制信号，采用半双工模式；USB 3.x 则引入独立的 TX（发送）和 RX（接收）差分对，支持全双工以提升吞吐量。

编码方式采用 NRZI（非归零反转编码）结合比特填充。NRZI 规则简单：比特 0 表示信号电平不翻转，1 表示翻转，以避免直流分量积累。为防止时钟恢复问题，协议插入比特填充：连续 6 个 0 时插入 1，连续 6 个 1 后也调整。这种机制确保接收端能可靠同步。信号以 J（D+ 高、D- 低）和 K（D+ 低、D- 高）状态表示空闲或 SE0（两者低）表示结束。

速度模式包括低速 1.5 Mbps、全速 12 Mbps 和高速 480 Mbps，设备连接时通过特定序列协商。复位后，主机发送 Chirp J（全速）或 Chirp K（高速检测），设备若支持高速则响应 Chirp K-J 序列，最终锁定模式。这种协商确保向下兼容，例如 USB 3.x 设备可回退至 USB 2.0 模式。

电气规范同样关键。VBUS 电压维持在 5V ±5%，USB 2.0 最大电流 900mA，结合 PD 可达 5A。差分阻抗精确匹配 90 Ω，线缆长度限 3-5 米以防衰减。眼图测试验证信号完整性，避免抖动和串扰。这些规范由 USB-IF 严格定义，确保全球互操作性。

在实际波形中，Chirp 信号表现为快速的 J/K 切换：例如，高速 Chirp K 持续 1-10 ms，示波器上可见 D+/D- 的对称翻转，伴随 SE0 结束分隔（EOP）。理解这些，能帮助调试连接失败问题。

## USB 协议栈架构

USB 协议栈采用分层模型，从物理层向上构建至应用层。最低物理层（PHY）处理比特传输，其上包层（Packet Layer）封装数据帧，再到事务层（Transaction Layer）管理 IN/OUT/SETUP 操作。USB 核心层提供设备框架，设备类层定义 HID 或 Mass Storage 等标准接口，顶层应用层由函数驱动实现具体逻辑。这种分层便于模块化开发和调试。

包是 USB 通信的基本单元，所有包前导 8 位 SYNC 字段（KJKJKJKJ）用于时钟同步。PID（Packet ID）8 位标识类型，并携带地址、端点和 CRC 校验。TOKEN 包用于 SETUP（配置）、IN（主机读）和 OUT（主机写），结构为 PID（8 位）+ 地址（7 位）+ 端点（4 位）+ CRC5（5 位），总长 24 位。DATA 包携带 0-1023 字节负载，加 CRC16 校验。HANDSHAKE 包仅 PID，如 ACK（成功）、NAK（忙）和 STALL（错误）。USB 3.x 扩展为 HEADER PACKET（协议头）和 DATA PACKET（分段数据），支持更大吞吐。

事务机制围绕 TOKEN 展开。以 OUT 事务为例：主机发 TOKEN-OUT 指定地址和端点，继而 DATA 包，设备响应 HANDSHAKE。IN 事务反之，SETUP 用于控制传输。错误处理包括超时（无响应 3 次重试）、位填充违规和 CRC 失败，触发重传或 Stall。时序上，一个 OUT 事务从 SYNC 开始，至 EOP 结束，总时延受速度制约。

考虑一个简化 OUT 事务的伪代码表示：

```
void usb_out_transaction(uint8_t addr, uint8_t ep, uint8_t* data, uint16_t len) {
    // 发送 SYNC (8 bits: KJKJKJKJ)，同步时钟
    send_sync();
    // 构造 TOKEN: PID=OUT(0xE1), addr(7b), ep(4b), CRC5
    uint8_t token[3] = {0xE1, (addr<<1)|0x01, crc5_calc()};
    send_packet(TOKEN, token, 3);
    // 发送 DATA0/1 PID + 数据 + CRC16，翻转 DATA PID 确保奇偶
    uint8_t data_pid = toggle_data_pid();  // 内部维护 PID 翻转
    send_packet(DATA, data_pid, data, len, crc16_calc(data, len));
    // 等待 HANDSHAKE，超时重试
    uint8_t handshake = receive_handshake();
    if (handshake == ACK) toggle_data_pid();  // 成功后翻转下次 PID
}
```

这段代码逐层解读：首先 send_sync() 输出固定 KJKJKJKJ 序列，帮助接收端 PLL 锁定比特率。TOKEN 构建中，PID 0xE1 表示 OUT（反码 0xE1 校验），地址左移加端点方向位，CRC5 覆盖前两字节。DATA 部分，toggle_data_pid() 维护 DATA0（0xD2）和 DATA1（0xD3）的交替，确保丢失检测。CRC16 使用 CCITT 多项式 $x^{16} + x^{15} + x^{2} + 1$ 计算。最后，receive_handshake() 解析 PID，若 ACK（0xD2）则确认翻转，避免重复传输。这体现了 USB 的可靠性和状态机设计。

## USB 设备枚举与配置

设备枚举是 USB 初始化核心过程，确保主机识别并配置新设备。第一步，主机发送总线复位，设备以默认地址 0 响应，并报告设备描述符中的 bMaxPacketSize0（通常 8、16 或 64 字节），确定控制端点 0 最大包长。第二步，SET_ADDRESS 命令分配唯一地址（1-127）。第三步，主机查询配置描述符（含 wTotalLength 和 bNumInterfaces）、接口描述符（bInterfaceClass 如 HID=3）和端点描述符（bmAttributes 指定 Bulk/Int 等，wMaxPacketSize 定义负载）。最后，SET_CONFIGURATION 激活选定配置，设备进入工作态。

描述符是二进制结构，提供设备元数据。设备描述符 18 字节，包括 bcdUSB（版本，如 0x0200）、idVendor 和 idProduct 用于驱动匹配。配置描述符 9 字节起，wTotalLength 覆盖整个配置块，bNumInterfaces 列出接口数。接口描述符 9 字节，bInterfaceClass 标识类码（如 Mass Storage=8）。端点描述符 7 字节，bEndpointAddress（方向位 8 为 IN），wMaxPacketSize 如 512 字节。这些字段标准化，确保即插即用。

设备类规范定义标准协议：HID（Human Interface Device）用于键盘鼠标，支持报告描述符；MSC（Mass Storage Class）模拟块设备，通过 SCSI 命令读写；CDC（Communication Device Class）实现虚拟串口。自定义类需 vendor ID 支持。

Wireshark 抓包中，枚举表现为连续 GET_DESCRIPTOR 请求：bDescriptorType=1（设备）、49（配置），响应十六进制流如 12 09 00 01 00 01 00 40 4B，解析为 bLength=18、bDescriptorType=1、bcdUSB=0x0100 等，直观展示过程。

## USB 传输类型与高级特性

USB 定义四种传输类型，各有优化。控制传输可靠双向，带 HANDSHAKE 状态，用于配置和命令，如枚举阶段。Bulk 传输可靠大块数据，无带宽保证，适用于 U 盘打印机，通过重传确保完整性。Interrupt 传输低延迟，主机轮询，适合键盘鼠标报告事件。Isochronous 传输实时，时延保证但无重传，专为音频视频设计，利用微帧（125 μ s）分配带宽。

USB 3.x 引入 SuperSpeed 特性，如 LFPS（Low Frequency Periodic Signaling）低功耗信号，U1/U2 休眠状态节省能耗。USB Power Delivery（PD）支持动态协商 5-20V 电压，最高 100W，通过 CC 引脚实现。Type-C 接口革命性翻转角色，Alt Mode 复用为 DisplayPort 或 HDMI。

性能优化依赖带宽分配：TT（Transaction Translator）在 Hub 调度 Split 事务，将高速拆分至全速设备。调试常见问题包括信号完整性（眼图闭合度）和功耗管理（选择性挂起）。

## 实际开发与工具

开发 USB 设备离不开专业工具。USB Analyzer 如 Ellisys 捕获物理信号，Wireshark USB 插件解析协议包，Keil 或 PlatformIO 提供固件环境。开源库 TinyUSB 和 libusb 加速实现，前者嵌入式友好，后者主机侧便捷。

以 STM32 实现 USB HID 为例，以下伪代码展示报告发送：

```
#include "usbd_hid.h"

uint8_t report[8] = {0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // HID 报告：按键 1

int main() {
    usbd_init();  // 初始化 USB 栈，配置描述符
    while(1) {
        if (key_pressed()) {  // 模拟按键检测
            report[2] = 0x01;  // 修改报告字节
            USBD_HID_SendReport(&husbd_device, report, 8);  // IN 端点发送
            HAL_Delay(10);  // 防抖
            report[2] = 0x00;  // 释放
            USBD_HID_SendReport(&husbd_device, report, 8);
        }
    }
}
```

解读：usbd_init() 注册设备描述符（HID 类，IN Interrupt 端点）和配置，栈处理枚举。USBD_HID_SendReport() 触发 Interrupt IN 事务：填充 DATA PID + 报告 + CRC，主机轮询时拉取。report 数组模拟键盘扫描码，字节 2 置位表示键码。这段代码简洁，实际需处理 PID 翻转和 NAK 响应，TinyUSB 库封装这些细节，便于快速原型。


本文从 USB 基础拓扑、物理层编码，到协议栈、枚举、传输类型和开发实践，全面解析了其机制。核心在于主从树状架构、可靠事务和分层设计，确保高互操作性。

展望未来，USB4 v2 目标 80 Gbps，无线 USB 趋势或融合 Wi-Fi 7。读者不妨实践：用 STM32 搭建 HID 设备，亲手验证枚举和传输。

## 附录

参考 USB-IF 官网规范和《USB Complete》（Jan Axelson）深入研究。术语如 PID（Packet Identifier）、EOP（End of Packet）、SOF（Start of Frame）遍布协议。FAQ：USB3 向下兼容 USB2，通过回退模式。进一步阅读 USB4 白皮书，探索 40 Gbps 细节。
