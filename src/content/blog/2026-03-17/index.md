---
title: "FFmpeg 视频处理基础"
author: "叶家炜"
date: "Mar 17, 2026"
description: "FFmpeg 视频处理基础：转码、裁剪、滤镜实战指南"
latex: true
pdf: true
---


FFmpeg 是一个功能强大的开源多媒体框架，它能够处理视频、音频以及其他多媒体文件，支持编码、解码、转码、复用、解复用、流媒体协议等多种操作。作为一个跨平台的命令行工具，FFmpeg 被广泛应用于视频处理、直播推流和多媒体开发领域。它支持几乎所有常见的媒体格式，包括 MP4、AVI、MKV 等容器，以及 H.264、H.265 等主流编码器，这使得它成为开发者处理多媒体任务的首选工具。

选择 FFmpeg 的主要原因是其免费开源性质、强大的功能集以及优秀的跨平台兼容性。不论是 Windows、macOS 还是 Linux 系统，都能轻松运行 FFmpeg，而且社区活跃，提供海量扩展和插件。本文面向初学者和中级开发者，目标是帮助读者掌握 FFmpeg 的基本命令行用法，并通过常见场景演示来实现实际视频处理任务。阅读完本文后，你将能够独立完成格式转换、视频裁剪、尺寸调整以及水印添加等操作。

在使用 FFmpeg 前，需要准备好环境。首先从官方网站下载对应操作系统的二进制文件，对于 Windows 用户可以选择静态构建版本，直接解压后添加到系统 PATH；macOS 用户可通过 Homebrew 安装，即执行 `brew install ffmpeg`；Linux 用户则使用包管理器如 `apt install ffmpeg`。安装完成后，在终端运行 `ffmpeg -version` 来验证是否成功，该命令会输出 FFmpeg 的版本信息和编译配置，确认无误后即可开始实践。

## FFmpeg 核心概念

理解 FFmpeg 的核心概念有助于快速上手。媒体容器（Container）就像一个包装盒，内部封装了视频流和音频流，例如 MP4 文件就是一个典型的容器。编码器和解码器（Codec）负责数据的压缩和解压，H.264 是最常用的视频编码器，而 AAC 常用于音频。媒体流（Stream）是容器内的独立轨道，一个视频文件通常包含一个视频流和一个音频流。复用器（Muxer）和解复用器（Demuxer）分别用于将多个流打包成容器或从容器中拆分离流。

FFmpeg 的命令行结构非常直观，通常遵循 `ffmpeg [global options] -i input [output options] output` 的格式。其中，全局选项如 `-loglevel` 影响整个进程；`-i input` 指定输入文件，这是必选项；输出选项如 `-c:v` 用于配置视频编码器，作用于特定输出流；最后是输出文件名。该结构允许灵活组合选项，实现复杂处理任务。

## 安装与基本使用

安装过程因平台而异，但核心验证命令统一为 `ffmpeg -version`，它会显示版本号如 6.0 及支持的库列表，确保工具就绪。基本使用从查看文件信息开始，执行 `ffmpeg -i input.mp4`，这个命令会详细输出输入文件的元数据，包括容器格式、视频流的分辨率、帧率、比特率、音频流的采样率等信息，非常适合诊断文件问题，而无需额外工具。

简单转码是最基础的操作，例如 `ffmpeg -i input.mp4 output.avi`，这里 FFmpeg 会自动检测输入格式并选择合适的解码器和编码器，将 MP4 转换为 AVI 容器，整个过程无需指定额外参数。如果需要实时预览文件，可以运行 `ffplay input.mp4`，这是一个 FFmpeg 自带的播放器，支持硬件加速和滤镜预览，界面简洁，适合快速检查视频内容。

## 核心视频处理功能

### 格式转换与转码

格式转换是 FFmpeg 的核心功能之一。以 MP4 转 AVI 为例，命令 `ffmpeg -i input.mp4 output.avi` 会读取 input.mp4 文件，使用默认解码器提取视频和音频流，然后选择 AVI 容器的默认编码器重新编码并输出。整个过程涉及解复用、转码和复用，如果输入和输出格式兼容，甚至可以实现无损拷贝以提升速度。

为了精确控制编码器，使用 `ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4`。这里 `-c:v libx264` 指定视频使用开源 H.264 编码器 libx264，它以高质量压缩著称；`-c:a aac` 指定音频使用 AAC 编码器，确保兼容性。`-c` 是 codec 的缩写，可简写为 `-c:v libx264 -c:a copy` 来仅转码视频而音频直通拷贝，避免不必要重编码。常见容器包括 MP4（网络优化）、AVI（兼容性强）、MKV（支持字幕）、MOV（Apple 生态）和 WebM（Web 视频）。常用视频编码器有 libx264（平衡）、libx265（高压缩）和 libvpx（VP9 开源）。

### 视频裁剪与截取

视频裁剪常用时间参数实现，例如 `ffmpeg -i input.mp4 -ss 00:00:10 -t 00:00:20 -c copy output.mp4`。`-ss 00:00:10` 表示从第 10 秒开始（格式为 HH:MM:SS 或秒数），`-t 00:00:20` 指定持续 20 秒，`-c copy` 启用流拷贝模式，避免重新编码以保持原质量和极速处理。如果放在 `-i` 前，`-ss` 会快速定位文件偏移，提升效率。

按帧数截取则依赖视频滤镜，命令 `ffmpeg -i input.mp4 -vf "select=between(n\,100\,200)" output.mp4` 使用 `-vf` 指定滤镜链。「select」滤镜筛选帧，`n` 表示当前帧序号，`between(n\,100\,200)` 选择第 100 到 200 帧（注意转义逗号以防 shell 解析），输出仅包含这些帧，非常适合精确帧级编辑。

### 尺寸调整与缩放

尺寸调整通过 scale 滤镜完成，例如 `ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4`，`-vf scale=1280:720` 将视频缩放到 1280x720 分辨率，默认使用双线性插值算法。如果要保持宽高比，使用 `ffmpeg -i input.mp4 -vf scale=1280:-1 output.mp4`，其中 `-1` 让高度自适应，避免拉伸变形。常用预设如 `scale=1920:1080`（全高清）或 `scale=1280:720`（高清），可链式组合如 `scale=1920:1080:flags=lanczos` 以 Lanczos 算法提升质量。

### 视频合并与拼接

水平拼接两个视频使用 `ffmpeg -i left.mp4 -i right.mp4 -filter_complex hstack output.mp4`。「-filter_complex」处理复杂滤镜图，`hstack` 将两个输入并排拼接，要求两视频高度相同，否则需预处理。垂直拼接类似，`ffmpeg -i top.mp4 -i bottom.mp4 -filter_complex vstack output.mp4`，上下叠加适用于短视频制作。

对于相同参数的多视频合并，创建文本列表 `echo "file '1.mp4'" > list.txt` 和 `echo "file '2.mp4'" >> list.txt`，然后 `ffmpeg -f concat -i list.txt -c copy output.mp4`。「-f concat」指定 concat 解复用器，从列表读取文件路径，`-c copy` 无损连接，仅适用于分辨率、帧率一致的视频。

## 高级视频处理技巧

### 滤镜系统

FFmpeg 的滤镜系统是其强大之处，支持链式组合。例如 `ffmpeg -i input.mp4 -vf "scale=1280:720,crop=1280:720:0:0" output.mp4`，先 scale 缩放到 1280x720，然后 crop 从左上角裁剪相同尺寸，逗号分隔多个滤镜，按顺序执行。常用组合 ` -vf "scale=1920:1080:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"`：scale 使用 Lanczos 算法 upscale，pad 居中填充黑边，`ow/ih` 为输出宽高，`iw/iw` 为输入宽高，实现完美适配。

滤镜类型丰富，scale 用于尺寸调整，crop=w:h:x:y 指定裁剪宽高及偏移，pad 填充背景，overlay 叠加图层如水印。

### 音频处理

提取音频使用 `ffmpeg -i input.mp4 -vn -acodec copy audio.aac`，`-vn` 禁用视频流，`-acodec copy` 直通音频编码（如 AAC），快速分离轨道。替换音频则需多输入：`ffmpeg -i video.mp4 -i new_audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4`。「-map 0:v:0」选择第一个输入（索引 0）的第一个视频流，`-map 1:a:0` 取第二个输入的第一个音频流，`-c:v copy` 保留原视频，`-c:a aac` 转码新音频，确保同步。

### 水印与字幕

添加图片水印：`ffmpeg -i input.mp4 -i logo.png -filter_complex "overlay=W-w-10:H-h-10" output.mp4`。`-filter_complex` 处理双输入，overlay 将 logo.png 叠加到主视频右下角，`W-w-10` 表示主机宽减 logo 宽再减 10 像素的 x 坐标，`H-h-10` 为 y 坐标，实现动态定位。

文字水印使用 `ffmpeg -i input.mp4 -vf "drawtext=text='水印文字':fontsize=24:fontcolor=white:x=10:y=H-th-10" output.mp4`。「drawtext」滤镜渲染文本，`text` 为内容，`fontsize=24` 字号，`fontcolor=white` 颜色，`x=10` 左边距 10 像素，`y=H-th-10` 从底部向上 10 像素（H 为视频高，th 为文本高）。硬字幕烧录：`ffmpeg -i input.mp4 -vf subtitles=subtitles.srt output.mp4`，将 SRT 文件永久嵌入视频帧。

## 批量处理与自动化

批量处理依赖脚本循环。在 Windows CMD 中，`for %f in (*.mp4) do ffmpeg -i "%f" -vf scale=1280:720 "resized_%f"` 遍历当前目录所有 MP4 文件，对每个输入执行缩放并输出 resized_ 前缀文件，双引号防止空格问题。在 Linux/Shell，`for file in *.mp4; do ffmpeg -i "$``$file'' -vf scale=1280:720 ``resized_$$\verb|ffmpeg -i "$file" -vf scale=1280:720 "resized_${file%.*}.mp4"; done|$$

\text{\verb|${file%.*}| 移除扩展名，确保输出为 resized\_ 原名 .mp4。这些脚本适合大规模处理。}{file%.*}` 移除扩展名，确保输出为 resized_ 原名 .mp4。这些脚本适合大规模处理，提升效率。

## 性能优化与最佳实践

性能优化从预设参数入手，使用 `-preset ultrafast` 加速编码（牺牲些质量），`-preset medium` 平衡速度与质量，`-preset slow` 追求极致压缩。CRF（恒定码率因子）控制质量，`-crf 18-28` 范围推荐，数值越小质量越高如 `-crf 23` 为标准高清；`-threads 0` 自动并行所有 CPU 核心。

硬件加速显著提速，NVIDIA 用户执行 `ffmpeg -i input.mp4 -c:v h264_nvenc -preset p4 output.mp4`，`h264_nvenc` 使用 GPU NVENC 编码器，`-preset p4` 中等质量。Intel QuickSync 用 `ffmpeg -i input.mp4 -c:v h264_qsv output.mp4`，依赖 QSV 硬件解码。

常见问题如无音频可用 `-c:a copy` 或指定 `-c:a aac`；视频变形加 `-vf setsar=1` 修正像素宽高比；编码慢则 `-preset faster` 或硬件加速。

## 实际应用案例

短视频平台优化常需竖屏适配，从横屏视频裁剪为 9:16，例如结合 crop 和 pad 滤镜处理直播录制。直播转码如将 HLS 流保存为 MP4。批量图片转视频用 `ffmpeg -framerate 1/5 -pattern_type glob -i "*.png" -c:v libx264 output.mp4`，`-framerate 1/5` 每 5 秒一帧。GIF 优化 `ffmpeg -i input.gif -vf "scale=iw:ih:flags=lanczos,fps=30,palettegen" palette.png` 生成调色板，再 `ffmpeg -i input.gif -i palette.png -lavfi "fps=30[x];[x][1:v]paletteuse" output.mp4`，大幅减小体积。

## FFmpeg 与编程语言集成

在 Node.js 中，fluent-ffmpeg 库封装命令，如 `const ffmpeg = require('fluent-ffmpeg'); ffmpeg('input.mp4').output('output.mp4').videoFilters('scale=1280:720').run();`，链式 API 简化调用。Python 的 ffmpeg-python 类似，`import ffmpeg; ffmpeg.input('input.mp4').filter('scale', 1280, 720).output('output.mp4').run()`，支持异步和进度回调。

## 进阶学习资源

官方文档 ffmpeg.org 是最佳起点，详尽列出所有选项。推荐《FFmpeg 基础与应用》书籍及 YouTube 教程。编译自定义版本用 `./configure --enable-gpl --enable-libx264`，启用特定功能。社区如 Stack Overflow 和 Reddit r/ffmpeg 解答疑难。

## 结论

FFmpeg 以其全面功能和高效性主导视频处理领域，从基础转码到高级滤镜自动化，均游刃有余。实践是掌握关键，多尝试命令以积累经验。以下附录提供快速参考，推动你的项目落地。

## 附录：快速参考命令表

转换格式：`ffmpeg -i input.mp4 output.webm`，自动处理编码兼容。  
截取片段：`ffmpeg -ss 00:01:30 -t 00:00:30 -i input.mp4 output.mp4`，快速定位并拷贝。  
压缩视频：`ffmpeg -i input.mp4 -vcodec libx264 -crf 23 output.mp4`，CRF 23 平衡体积质量。  
添加水印：`ffmpeg -i input.mp4 -i logo.png -filter_complex overlay output.mp4`，默认右下角叠加。
