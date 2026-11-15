# 鹈鹕六千年的车 · Pure-Code Edition

零外部位图（0 PNG/JPG）、零外置字体包（0 WOFF2/TTF），画面全部由矢量代码实时绘制；音频为一条预渲染 **Ogg Opus** 混音轨。由 **Hydrogen** 独立交付的一整部 **2 分 55 秒（174.64s）** 中文交互式视听长卷：涵盖铁匠铺矢量篆刻开场、穿越 20 个艺术史时代、Live Canvas/SVG 动态笔触渲染，以及预渲染中文歌声/多轨器乐。

- **在线直开（GitHub Pages）**：https://wwh5441.github.io/pelican-6000-pure-code/
- **单文件离线包下载**：前往 [Releases 最新版](https://github.com/wwh5441/pelican-6000-pure-code/releases/latest) 下载 `pelican-6000-pure-code-single.zip`

## 本版资产体积

- `data/audio.opus`：约 `408 KiB`（Ogg Opus，48 kHz 立体声）
- `鹈鹕骑行_纯代码全片_单文件版.html`：`1.62 MiB`（单文件内嵌 Gzip-9 虚拟文件系统与 Opus 音轨，浏览器可直接打开）

## 音频

音轨为 `data/audio.opus`，由原始多轨频谱参数解码混音后预渲染。浏览器启动时预取，首次点击后通过 Web Audio `decodeAudioData` 解码为 `AudioBuffer`，再由 `AudioBufferSourceNode` 播放；旧的 LZMA / 频谱解码器与参数 payload 已移除。

## 播放交互控制

极简零按钮播放器设计，点击画面即可开始播放：

- **点击画面 / `Space`**：播放 / 暂停（首次交互解锁 Web Audio 播放）
- **双击画面 / `F`**：进入 / 退出全屏
- **`M`**：静音切换
- **`R`**：从头重播
- **`←` / `→`**：快退 / 快进 `5` 秒

## 本地运行与重新构建

双击 [启动纯代码全片.command](./启动纯代码全片.command) 后在浏览器打开 `http://127.0.0.1:8922/`；如需重新打包单文件离线版，可运行：

```bash
python3 ./tools/build_single_html.py
```

## 致敬与鸣谢

- 原创测试命题源头：Simon Willison — *"A pelican riding a bicycle"*
- 20 幕艺术史命题先行开源项目：[orbitoo/pelican-test](https://github.com/orbitoo/pelican-test)（及同源项目 [RoyceBella-commits/The-Pelican-Test](https://github.com/RoyceBella-commits/The-Pelican-Test)）
- 开源社区认可与友链：[LINUX DO](https://linux.do/)（真诚、友善、团结、专业，本项目已在 LINUX DO 开源交流发布）
