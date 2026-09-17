# 上传到 GitHub（B站外链版，无视频文件）

本文件夹已经生成完毕，直接上传即可，不必运行脚本。

## 上传步骤

1. 解压本包，不要把ZIP本身上传为展示内容。
2. 将本文件夹中的README.md、index.html、assets目录及其他配套文件上传到仓库根目录，保持结构。
3. 仓库首页自动显示README。点击4个视频封面将跳转至对应B站视频。
4. assets/montages包含12张组合图，每张包含6帧双联图；assets/posters包含4张封面。
5. index.html也是外链版本，不依赖本地MP4。可本地打开，或用GitHub Pages部署。

如果以前已经上传旧版本：覆盖README.md和index.html；原仓库的assets/videos目录可以删除，本版不再引用它。单纯上传新文件不会自动删除远端旧视频。

## 视频对应关系

按提供的4个链接顺序对应：
- 0706成像：https://www.bilibili.com/video/BV13Ceu6eE2b/
- 0718成像：https://www.bilibili.com/video/BV1Gkeu6NEkB/
- VSLAM 11/22/33：https://www.bilibili.com/video/BV1Xkeu6NE8e/
- VSLAM 44/55/66：https://www.bilibili.com/video/BV1akeu6NEtk/

## 可选：重新抽帧和生成组合图

只有需要重新制作图片时，才运行build.bat并提供原始四个视频所在的本地目录。
也可执行：python generate_showcase.py --source-dir "原视频目录" --output . --skip-video
需要Python、opencv-python、numpy、Pillow（requirements.txt）。该版本不会复制或转码视频。
中间抽帧保存在.work内，.gitignore已排除。视频标题、图片说明和时间点保留在README中。
selection_manifest.csv记录原始视频名称、帧号、时间和裁剪坐标，视频名称只是溯源记录，不表示包中包含视频文件。
