# Sun 摄影作品集

个人摄影作品集网站，纯静态，部署在 GitHub Pages（`main` 分支根目录）。网站的目的只有一个：好好展示照片。

- 线上地址：https://zppqako.github.io/personal_website/
- 照片来源：Mac「照片」App 里的相簿 **「网站」**。相簿里有什么，网站就显示什么；**相簿倒序显示**（相簿最后一张在网站第一位，也就是新加的在最前面）。
- 署名：网站上统一用 **SUN**（全大写、宽字距的衬线字标；logo、页脚、标签页标题 `SUN — Photography`），不写全名。

## 目录结构

```
index.html              页面骨架：导航、短标题区、图库容器（空）、Contact、Lightbox（About 已于 2026-11 删除，旧文案在 git 历史里）
favicon.svg             网站图标：一个实心圆（太阳），深色模式下自动变浅
css/style.css           全部样式
js/main.js              全部交互；读取 data/photos.json 渲染图库
data/photos.json        照片数据（脚本生成，alt 可手改）
photos/                 网页用图片（脚本生成，提交到 git）
scripts/process_photos.py  照片处理/同步脚本
scripts/requirements.txt   Python 依赖（osxphotos、Pillow）
update.sh               一键：同步相簿 → 生成图片 → 本地预览
originals/              旧的原图备份（gitignore，不进仓库，网站不使用）
.venv/                  Python 虚拟环境（gitignore，update.sh 首次运行自动创建）
.nojekyll               让 GitHub Pages 原样发布，不走 Jekyll
```

## 加新照片的标准流程

1. 在照片 App 里把照片加入相簿「网站」。新照片加在相簿末尾，网站上就显示在最前面；拖动可以调整顺序（网站顺序 = 相簿倒序）。
2. 运行 `./update.sh`：同步相簿、生成图片、更新 `data/photos.json`，然后在 http://localhost:8000 开预览。
3. 预览没问题后提交并推送：`git add -A && git commit -m "update photos" && git push`。GitHub Pages 1–2 分钟后更新。

- 下架照片：从相簿移除，再跑一遍 `./update.sh`。条目会标成 `"hidden": true`，图片文件保留；加回相簿就会重新显示。
- 网站只显示相簿里的照片。不在相簿里的条目（包括早期从文件夹导入的旧照片）一律隐藏。
- 在照片 App 里编辑过的照片，下次同步会自动重新导出编辑后的版本。
- 只想看会发生什么：`./update.sh --dry-run`。要全部重新生成：`./update.sh --force`。
- 从文件夹导入（不经过照片 App）：`.venv/bin/python scripts/process_photos.py --folder 路径`。
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
      "alt": { "en": "", "zh": "" },
      "hidden": false,
      "width": 5053, "height": 7581,
      "sizes": [400, 800, 1600, 2400],
      "takenAt": "2026-04-11T20:23:09",
      "exif": { "camera": "FUJIFILM X-T5", "lens": "XF35mmF1.4 R", "focalLength": 35,
                "aperture": 1.8, "shutter": "1/100", "iso": 500 }
    }
  ]
}
```

- **数组顺序就是显示顺序。** 同步后，相簿里的照片按**相簿倒序**排在最前面，其余条目全部隐藏，排在后面。
- `id`：原文件名去掉扩展名（空格换成 `_`），同时决定图片文件名。重名时追加 uuid 前 6 位。
- `source.type`：
  - `photos`：来自照片 App。`uuid` 是照片 App 里的 ID；`fingerprint` 记录是否编辑过、何时编辑，用来判断要不要重新导出。
  - `folder`：从文件夹导入，用 `sha256` 判断文件是否变化。
  - 2026-11 迁移进来的 43 张旧照片原本都是 `folder` 类型。如果相簿里有同 `id` 的照片，同步时会自动接管这条记录，变成 `photos` 类型；没有对应照片的就隐藏。
- `alt`：**唯一可以手改的字段**，脚本永远不会覆盖。为空时页面用 `"Photo"`。
- `hidden`：由同步脚本维护。在相簿里为 `false`，不在相簿里为 `true`。
- `width`/`height`：已按 EXIF 方向转正后的原图尺寸，页面用它预留比例。
- `sizes`：实际生成的长边尺寸。原图比 2400 小时只生成到原图尺寸。
- `exif`：页面目前不显示，留作以后用。没有的字段直接省略。

## 图片规则（photos/）

- `{id}-{长边}.webp`：长边 400/800/1600/2400，质量 82，用作网格 srcset 和 lightbox（取最大那档）。
- `{id}.jpg`：长边 1600，质量 85，渐进式，作为不支持 WebP 时的兜底。
- 先按 EXIF 方向把像素转正；**保留原 ICC 色彩配置**（大部分是 Display P3，去掉会发灰）；**去掉所有其他元数据，包括 GPS**。
- 不要手动往 `photos/` 里放文件或改文件名。一律通过脚本生成。

## 设计原则

- 极简、留白、照片优先，界面不和照片抢注意力。参照美术馆：墙是中性的，作品不被改动，说明文字小而安静。
- **作品先出场**：首屏只有一个短标题（Moments in Light / Photography Portfolio），第一排照片在不滚动的情况下就能看到。不要再加全屏 Hero 或图库上方的大标题。
- **不改动作品**：悬停时照片不压暗、不放大、不加遮罩，只把鼠标变成放大镜（`cursor: zoom-in`）。照片保持直角，不加圆角、阴影或边框。
- 配色：背景 `#f5f5f5`（完全中性的浅灰，不带冷暖色偏，像美术馆墙面，不影响对照片颜色的判断），文字 `#1a1a1a`，辅助灰 `#6b6b6b` / `#a0a0a0`，全部定义在 `css/style.css` 的 `:root`。背景不要再加色调。
- 字体：标题用 Cormorant Garamond（衬线，细），正文和导航用 DM Sans（无衬线，细，大写加字距），从 Google Fonts 加载。
- 图库：瀑布流，**从左到右阅读**（第一行是第 1、2、3 张）。>1024px 3 列，481–1024px 2 列，≤480px 1 列。最大宽度 1600px。
- 动效：照片进入视野时淡入并轻微上移，曲线 `--transition`。同一批进入视野的照片按阅读顺序依次错开 0.08s，每批重新计时，所以页面再长，照片出现也不会越来越慢。
- 大图（lightbox）：深色背景；左上角计数 `12 / 52`；照片下方一行小字参数（相机 · 镜头 · 焦距 · 光圈 · 快门 · ISO），像美术馆的展签。左右箭头是 1px 细线 SVG（和页面上的细分隔线一致），悬停变白并向外滑动 6px。箭头放在左右两侧预留的通道里（`--lightbox-gutter`），照片最大宽度会扣掉两侧通道，所以再宽的照片也不会挡住箭头；整条通道都可以点击。手机上隐藏箭头，通道缩到 16px，改为左右滑动翻页。
- 中英双语：元素上用 `data-zh` 或 `data-zh-html` 写中文，英文直接写在 HTML 里，右上角切换，选择存在 localStorage。新增文字时两种语言都要写。

## 代码要点

- `js/main.js` 是一个 IIFE。图库在 `fetch('data/photos.json')` 之后渲染，渲染完才调用 `initReveal()`（滚动渐显）；跟图库相关的逻辑都要放在渲染之后。
- 照片导出（`export_from_photos`）：本地有可读的文件（编辑过的照片用编辑版，没编辑过用原片）就直接读取；否则用 AppleScript 让照片 App 导出当前版本（会自动下载 iCloud 原片，HEIC/DNG 会转成 JPEG）。osxphotos 只用来读图库数据库，不用它导出，因为它的 iCloud 下载在这里拿不到任何文件，也不报错。
- 单张照片导出失败时会跳过它，其余照片照常处理，结尾列出失败的照片。再跑一次即可，已成功的不会重复处理。
- 大图说明文字由 `captionFor(exif)` 生成：镜头名里已包含机型时省略镜头（如 iPhone 的 "back triple camera"）；每项内部用不换行空格，只在分隔点处换行。
- 点击图库用事件委托（挂在 `#galleryGrid` 上），lightbox 读取每项的 `data-full`。
- 瀑布流由 `layoutGallery()` 用 JS 分列：前面的照片依次放进最短的列，最后 8 张会穷举所有放法，选底部最平的一种。不要换回 CSS `columns`，那种写法是竖着先填满第一列，最新的照片会全挤在左边。
- 列数只在 CSS 里定义：`.gallery` 的 `--gallery-columns` 变量（媒体查询里修改），JS 读取它；窗口跨断点时会重新分列。
- `sizes` 属性（`GALLERY_SIZES`）和列数断点是对应的。改列数时 CSS 和 `GALLERY_SIZES` 要一起改。
- 本地预览必须走 HTTP 服务器（`./update.sh` 或 `python3 -m http.server`）。**直接双击打开 index.html 图库会是空的**，因为 file:// 下 fetch 读不了 JSON。

## 不要做的事

- 不引入框架、打包工具或构建步骤。保持纯静态，push 到 main 就能直接部署。
- 不要把原图（几 MB 到几十 MB 的相机文件）提交到 git，网站只用 `photos/` 里的生成图。
- 不要在 `index.html` 里手写照片。加照片只走「相簿 → 脚本」这一条路。
- 不要手改 `photos.json` 里脚本管理的字段（除 `alt` 外都是）。要改顺序就去照片 App 里拖。
- 不要去掉生成图里的 ICC 配置，也不要保留 GPS 等元数据。
- 不要直接在 `main` 上做结构性改动。先开分支，确认后再合并。
- 没有用户明确要求时，不要 push、不要改写 git 历史（历史里已有约 380 MB 旧原图，清理需要 force push，必须用户决定）。

## 已知问题和待办

- 暂无。
