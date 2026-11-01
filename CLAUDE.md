# SUN 摄影作品集

个人摄影作品集网站，纯静态，部署在 GitHub Pages（`main` 分支根目录）。网站的目的只有一个：好好展示照片。

- 线上地址：https://zppqako.github.io/personal_website/（用户准备改 GitHub 用户名并把仓库改名为 `<新用户名>.github.io`，地址会变成 `https://<新用户名>.github.io/`，见下方「改地址时要改的地方」）
- 照片来源：Mac「照片」App 里的相簿 **「网站」**。**相簿是唯一来源**：相簿里有什么，网站就显示什么；**相簿倒序显示**（相簿最后一张在网站第一位，也就是新加的在最前面）。
- 署名：网站上统一用 **SUN**（全大写、宽字距的衬线字标；logo、页脚、标签页标题 `SUN — Photography`），不写全名。

## 目录结构

```
index.html              页面骨架：导航、短标题区、图库容器（空）、Contact、Lightbox；<head> 里有分享预览标签
favicon.svg             网站图标：一个实心圆（太阳），深色模式下自动变浅
css/style.css           全部样式
js/main.js              全部交互；读取 data/photos.json 渲染图库
data/photos.json        照片数据（全部由脚本生成，不手改）
photos/                 网页用图片 + cover.jpg（全部由脚本生成，提交到 git）
scripts/process_photos.py  同步脚本：照片 App 相簿 → photos/ + photos.json
scripts/hdr_gainmap.swift  HDR 辅助程序（macOS 自带 Core Image），首次使用时编译到 .venv/bin/hdr_gainmap
scripts/requirements.txt   Python 依赖（osxphotos、Pillow）
update.sh               一键：同步相簿 → 生成图片 → 本地预览
.venv/                  Python 虚拟环境（gitignore，update.sh 首次运行自动创建）
.nojekyll               让 GitHub Pages 原样发布，不走 Jekyll
originals/              （本地遗留，gitignore）2026-11 之前网站用的原图，网站和脚本都不再使用，可以删
```

About 区块已于 2026-11 删除。

## 加新照片的标准流程

1. 在照片 App 里把照片加入相簿「网站」。新照片加在相簿末尾，网站上就显示在最前面；拖动可以调整顺序（网站顺序 = 相簿倒序）。
2. 想给照片起标题，就在照片 App 里填这张照片的「标题」，比如"上海外滩"。标题会显示在大图下方，也用作图片的替代文字。不填就不显示。
3. 运行 `./update.sh`：同步相簿、生成图片、更新 `data/photos.json`，然后在 http://localhost:8000 开预览。
4. 预览没问题后提交并推送：`git add -A && git commit -m "update photos" && git push`。GitHub Pages 1–2 分钟后更新。

- 下架照片：从相簿移除，再跑一遍 `./update.sh`。这张照片的条目和 `photos/` 里的文件会**被删除**。加回相簿时重新生成，约 1 秒。
- 在照片 App 里编辑过的照片，下次同步会自动重新导出编辑后的版本。
- 只想看会发生什么：`./update.sh --dry-run`。要全部重新生成：`./update.sh --force`。
- 第一次在新电脑上运行，需要给终端或 VS Code 开「完全磁盘访问权限」（系统设置 → 隐私与安全性），否则读不到照片图库。
- 只存在 iCloud 上的照片，脚本会让照片 App 下载并导出。第一次运行时 macOS 可能会弹窗询问是否允许控制「照片」，要点允许。

## 数据格式：data/photos.json

```json
{
  "version": 1,
  "photos": [
    {
      "id": "DSCF5010",
      "source": { "type": "photos", "uuid": "…", "fingerprint": "original" },
      "title": "上海外滩",
      "width": 5053, "height": 7581,
      "sizes": [400, 800, 1600, 2400],
      "hdr": true,
      "takenAt": "2026-04-11T20:23:09",
      "exif": { "camera": "FUJIFILM X-T5", "lens": "XF35mmF1.4 R", "focalLength": 35,
                "aperture": 1.8, "shutter": "1/100", "iso": 500 }
    }
  ],
  "cover": "DSCF6122"
}
```

- **整个文件由脚本生成，不手改。** 要改内容，就去照片 App 里改（加减照片、排序、标题）。
- **数组顺序就是显示顺序** = 相簿倒序。数组里只有相簿里的照片。
- `id`：原文件名去掉扩展名（空格换成 `_`），同时决定图片文件名，也是单张照片链接里的 `#编号`。重名时追加 uuid 前 6 位。
- `source.uuid`：照片 App 里的 ID。`source.fingerprint` 记录是否编辑过、何时编辑，用来判断要不要重新导出。
- `title`：照片 App 里的标题，没有就不写这个字段。
- `width`/`height`：已按 EXIF 方向转正后的原图尺寸，页面用它预留比例和计算瀑布流。
- `sizes`：实际生成的长边尺寸。原图比 2400 小时只生成到原图尺寸。
- `hdr`：只有 HDR 照片才有（原图带增益图）。页面据此改用 `-hdr.jpg`。
- `exif`：大图下方的参数说明用它生成。没有的字段直接省略。
- `cover`：分享预览图 `photos/cover.jpg` 用的是哪张照片。

## 图片规则（photos/）

- `{id}-{长边}.webp`：长边 400/800/1600/2400，质量 82，用作网格 srcset 和 lightbox（取最大那档）。
- `{id}.jpg`：长边 1600，质量 85，渐进式，作为不支持 WebP 时的兜底。
- `{id}-{长边}-hdr.jpg`：只有 HDR 照片才生成。主图是普通版本，外加 ISO 21496-1 标准增益图。HDR 屏幕和支持的浏览器显示 HDR，其余显示普通版本。WebP 装不下 HDR，所以 HDR 照片在页面上用这组 JPEG 代替 WebP。
- `cover.jpg`：1200×630 的分享预览图，取页面上**第一张横幅照片**居中裁切，转成 sRGB（社交软件大多不做色彩管理）。每次同步都会重新生成。
- 先按 EXIF 方向把像素转正；**保留原 ICC 色彩配置**（大部分是 Display P3，去掉会发灰；cover 除外）；**去掉所有其他元数据，包括 GPS**。
- HDR 检测：原图里有增益图标记（Apple、ISO 21496-1、Ultra HDR 任一）就算 HDR。生成由 `scripts/hdr_gainmap.swift` 完成：用 Core Image 读出 HDR，缩放后写 JPEG，同样去掉 EXIF/GPS、保留色彩配置。没有 Swift 编译器时会自动退回只生成普通版本。
- 同步结束时，`photos/` 里不属于任何照片的文件会被删除。不要手动往里放文件。

## 设计原则

- 极简、留白、照片优先，界面不和照片抢注意力。参照美术馆：墙是中性的，作品不被改动，说明文字小而安静。
- **作品先出场**：首屏只有一个短标题（Moments in Light / Photography Portfolio），第一排照片在不滚动的情况下就能看到。不要再加全屏 Hero 或图库上方的大标题。
- **不改动作品**：悬停时照片不压暗、不放大、不加遮罩，只把鼠标变成放大镜（`cursor: zoom-in`）。照片保持直角，不加圆角、阴影或边框。
- 配色：背景 `#f5f5f5`（完全中性的浅灰，不带冷暖色偏，像美术馆墙面，不影响对照片颜色的判断），文字 `#1a1a1a`，辅助灰 `#6b6b6b` / `#a0a0a0`，全部定义在 `css/style.css` 的 `:root`。背景不要再加色调；用户问过纯白、18% 灰、深色，结论是保持这个浅灰（浏览时明亮，点开大图时深色沉浸）。
- 字体：标题用 Cormorant Garamond（衬线，细），正文和导航用 DM Sans（无衬线，细，大写加字距），从 Google Fonts 加载。
- 图库：瀑布流，**从左到右阅读**（第一行是第 1、2、3 张）。>1024px 3 列，481–1024px 2 列，≤480px 1 列。最大宽度 1600px。
- 动效：照片进入视野时淡入并轻微上移，曲线 `--transition`。同一批进入视野的照片按阅读顺序依次错开 0.08s，每批重新计时，所以页面再长，照片出现也不会越来越慢。
- HDR：网格里用 `dynamic-range-limit: constrained` 压住 HDR 高光，不和周围照片抢；点开大图用 `no-limit` 完全放开。不支持这个属性的浏览器会忽略它。
- 大图（lightbox）：
  - 深色背景，左上角计数 `12 / 52`。
  - 照片下方是标题（衬线，有才显示）和一行小字参数（相机 · 镜头 · 焦距 · 光圈 · 快门 · ISO），像美术馆的展签。
  - 左右箭头是 1px 细线 SVG（和页面上的细分隔线一致），悬停变白并向外滑动 6px。箭头放在左右两侧预留的通道里（`--lightbox-gutter`），照片最大宽度会扣掉两侧通道，所以再宽的照片也不会挡住箭头；整条通道都可以点击。
  - 手机上隐藏箭头，通道缩到 16px，改为左右滑动翻页。
  - 下一张还没下载完时，当前照片变半透明；新照片到了，文字和照片一起换。
- 中英双语：元素上用 `data-zh` 或 `data-zh-html` 写中文，英文直接写在 HTML 里，右上角切换，选择存在 localStorage。新增文字时两种语言都要写。

## 代码要点

- `js/main.js` 是一个 IIFE。图库在 `fetch('data/photos.json')` 之后渲染，渲染完才调用 `initReveal()`（滚动渐显）；跟图库相关的逻辑都要放在渲染之后。`index.html` 里用 `<link rel="preload">` 提前请求 photos.json（带 `crossorigin`，否则会重复下载）。
- 前 3 张（桌面第一排）用 `fetchpriority="high"` 立即加载，其余 `loading="lazy"`。
- 瀑布流由 `layoutGallery()` 用 JS 分列：前面的照片依次放进最短的列，最后 8 张会穷举所有放法，选底部最平的一种。不要换回 CSS `columns`，那种写法是竖着先填满第一列，最新的照片会全挤在左边。**注意：页面结构里的顺序是按列的，不是照片顺序**；照片顺序以 `galleryItems` 数组为准（测试时也要按它找照片）。
- 列数只在 CSS 里定义：`.gallery` 的 `--gallery-columns` 变量（媒体查询里修改），JS 读取它；窗口跨断点时会重新分列。`sizes` 属性（`GALLERY_SIZES`）和列数断点是对应的，改列数时 CSS 和 `GALLERY_SIZES` 要一起改。
- 大图和浏览器历史：打开大图 `pushState` 到 `#照片id`（state 里 `pushed: true`），翻页用 `replaceState`，关闭时如果是自己 push 的就 `history.back()`，否则（从分享链接直接进来）`replaceState` 去掉 `#`。`popstate` 根据网址开关大图。这样手机返回键只关大图，不会离开网站；单张照片链接 `…/#DSCF5010` 可以直接分享。
- 键盘：照片 `tabindex=0`、`role=button`，回车或空格打开；大图打开后焦点在关闭按钮上，Tab 只在大图按钮间循环，Esc 关闭后焦点回到原来那张照片。大图的 `visibility` 打开时立即生效（关闭时等淡出结束才隐藏），否则打开瞬间无法聚焦。
- 大图打开时预加载前后各一张（`preload()`）。
- 大图说明文字由 `captionFor(exif)` 生成：镜头名里已包含机型时省略镜头（如 iPhone 的 "back triple camera"）；每项内部用不换行空格，只在分隔点处换行。
- 照片导出（`export_from_photos`）：本地有可读的文件（编辑过的照片用编辑版，没编辑过用原片）就直接读取；否则用 AppleScript 让照片 App 导出当前版本（会自动下载 iCloud 原片，HEIC/DNG 会转成 JPEG）。osxphotos 只用来读图库数据库，不用它导出，因为它的 iCloud 下载在这里拿不到任何文件，也不报错。
- 单张照片导出失败时会跳过它（已有的旧版本保留），其余照片照常处理，结尾列出失败的照片。再跑一次即可，已成功的不会重复处理。
- 本地预览必须走 HTTP 服务器（`./update.sh` 或 `python3 -m http.server`）。**直接双击打开 index.html 图库会是空的**，因为 file:// 下 fetch 读不了 JSON。

## 改地址时要改的地方

网站地址变了（改用户名、改仓库名、绑定自己的域名）时：

1. `index.html` 里的 `og:url` 和 `og:image` 是**绝对地址**，要改成新地址，否则分享预览图会失效。
2. 本文件顶部的「线上地址」。
3. 本地 git 远程地址：`git remote set-url personal_website <新仓库地址>`（GitHub 会对旧地址做重定向，但最好改掉）。

## 不要做的事

- 不引入框架、打包工具或构建步骤。保持纯静态，push 到 main 就能直接部署。
- 不要把原图（几 MB 到几十 MB 的相机文件）提交到 git，网站只用 `photos/` 里的生成图。仓库是公开的，提交进去的东西任何人都能下载。2026-11 已经清理过一次 git 历史里的原图，不要再引入。
- 不要在 `index.html` 里手写照片，也不要手改 `photos.json`。加照片、排序、改标题只走「照片 App 相簿 → 脚本」这一条路。
- 不要去掉生成图里的 ICC 配置，也不要保留 GPS 等元数据。
- 不要直接在 `main` 上做结构性改动。先开分支，确认后再合并。
- 没有用户明确要求时，不要 push，不要改写 git 历史。

## 已知问题和待办

- 网址改名：等用户改完 GitHub 用户名、仓库改名为 `<新用户名>.github.io` 后，按上面「改地址时要改的地方」更新。
