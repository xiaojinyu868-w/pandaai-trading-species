---
name: vmc
description: 用素材中台 CLI（vmc）生成图片或视频。当用户要求出图、批量出图、生成视频、查看生成任务进度或下载生成结果时使用。所有下单命令先不带 --yes 拿到计划（模型、数量、配额、费用），把计划展示给用户并获得明确确认后，再加 --yes 提交。
---

# vmc：素材中台生图 / 生视频命令行

> 由 vmc 0.1.4 生成；升级 vmc 后运行 `vmc init --force` 更新本文件。

vmc 是确定性工具，没有内置模型；你（Agent）负责理解需求、拼命令、解读 JSON 输出。
所有命令在非 TTY 下自动输出 JSON 信封 `{ok, data|error, meta}`；显式加 `--json` 亦可。

## 铁律：先计划，再确认，才提交

1. 先运行**不带 --yes** 的生成命令。CLI 只会输出计划并以退出码 5 结束（`error.code = CONFIRMATION_REQUIRED`，`plan` 字段含模型、数量、今日配额前后、费用预估）。
2. 把计划里的模型 / 数量 / 配额 / 费用原样转述给用户，等用户明确同意。
3. 用户同意后，**同一条命令加 `--yes`** 重新运行。永远不要在用户未确认时自行加 --yes。
4. 想只看计划不提交：`--dry-run`。

## 常用命令

```bash
vmc whoami                       # 当前用户 / 令牌
vmc quota                        # 今日配额（图片 张 / 视频 条）与在途任务
vmc models image                 # 图片模型、版本、尺寸
vmc models video                 # 视频模型、时长、分辨率、比例、是否支持有声

# 生图（单任务 1-4 张）
vmc image gen --prompt "产品海报，白底，柔光" --model gpt --size 1024x1536 --count 2 --yes --out ./vmc-output
vmc image gen --prompt "{color} 配色的运动鞋主图" --var 红色 --var 蓝色 --var 黑色 --yes --out ./vmc-output
vmc image gen --prompt "换成雪地背景" --ref ./product.png --model nanobanana --size 9:16 --yes --out ./vmc-output

# 批量生图：每行一个 JSON（至少含 prompt）或一条纯文本提示词
cat > prompts.jsonl <<'EOF'
{"prompt": "夏日饮品海报，清爽蓝色", "size": "1024x1536"}
{"prompt": "夏日饮品海报，热情橙色", "size": "1024x1536", "count": 2}
EOF
vmc image batch --file prompts.jsonl --model gpt --yes --out ./vmc-output

# 生视频
vmc video gen --model kling-v3 --prompt "镜头缓慢推进，产品旋转展示" --duration 5 --ratio 9:16 --yes --out ./vmc-output
vmc video gen --model seedance-2.0 --ref ./frame.png --prompt "轻微呼吸感动效" --yes --out ./vmc-output
vmc video gen --model seedance-2.5 --prompt "海浪拍打礁石，带环境音" --audio --yes --out ./vmc-output

# 任务
vmc task list --type image --limit 5
vmc task get img_123
vmc task wait img_123 vid_45 --out ./vmc-output   # 轮询到完成并下载
vmc task cancel vid_45
vmc upload ./a.png ./b.png        # 预先上传参考图，拿 key 复用
```

## 输出与退出码

- 成功：`{ "ok": true, "data": {...}, "meta": {"version": "..."} }`。生成结果在 `data.urls`（CDN 地址）与 `data.files`（--out 下载后的本地路径）。
- 失败：`{ "ok": false, "error": {"code", "message", "hint"}, ... }`；需确认时还带 `plan`。
- 退出码：0 成功；2 参数错误；3 未登录 / 令牌无效 / 缺少作用域；4 配额不足或在途任务超限；5 需要确认；6 任务失败；7 网络或服务端错误。

## 注意

- 单任务最多 4 张；更多请用 `image batch`，或 `--var` 一个变量出多张变体。
- 图片模型：gpt（像素尺寸）、nanobanana（比例如 9:16，--image-size 1K/2K/4K）、seedream（像素尺寸，见 `vmc models image` 的合法尺寸）。
- 参考图 --ref 可以是本地文件（自动上传）或已上传的 key。
- 有声视频加 `--audio`。哪些模型支持以 `vmc models video` 为准（表格「有声」列，JSON 为 `supports_sound`），每次现查，不要凭记忆或旧结论判断；不支持的模型加 --audio 会报 `AUDIO_UNSUPPORTED`。
- 配额是每人每天的硬闸口，超限（退出码 4）不要重试，告知用户联系管理员。
- 带 `--yes` 的提交因超时 / 网络错误（退出码 7）失败时，可原样重跑同一条命令：服务端 10 分钟内按参数去重，不会重复下单，输出里 `replayed: true` 表示复用了已创建的任务。
- 未登录（退出码 3）时提示用户在终端运行 `vmc login`（会打开浏览器走飞书授权），你不要替用户登录。
- 输出目录默认建议 ./vmc-output/<任务ID>/。
