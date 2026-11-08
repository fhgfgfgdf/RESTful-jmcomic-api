# 接入腕上漫画（VELA 设备）

本项目已符合《自定义漫画源配置指南》(`bandcomic/docs/CUSTOM_SOURCE.md`)。
手环（VELA / NuttX）本身跑不了 Python，服务必须部署在能被手环访问到的 HTTPS 地址上；
手环通过 AstroBox 的「腕上漫画同步器」拿到源配置后，自己去请求接口。

## 1. 部署（Vercel，最简）

1. 打开 <https://vercel.com/new>，Import Git Repository，选择 `fhgfgfgdf/RESTful-jmcomic-api`。
2. Framework Preset 选 **Other**，Root Directory 保持仓库根目录。
3. 环境变量先不填也能跑（不填 `CACHE_DB` 时用进程内存缓存，适合 Serverless）。
4. Deploy。拿到形如 `https://xxxx.vercel.app` 的域名。

仓库已有 `vercel.json`：全部路径 rewrite 到 `index.py`，`maxDuration` 60s，所以 `/config`、`/album/...`、`/photo/...` 都能直接访问。

可选环境变量（Settings → Environment Variables）：

| 变量 | 用途 |
|---|---|
| `PUBLIC_URL` | 自定义域名/反代前缀时手动指定，不填则按请求 Host 推导 |
| `JM_DOMAINS` | 上游域名，最多三个，逗号分隔 |
| `JM_USERNAME` / `JM_PASSWORD` | 服务账号（不推荐写进云端环境变量） |
| `IMAGE_CONCURRENCY` / `IMAGE_GLOBAL_CONCURRENCY` | Serverless 下建议保持 1 / 2 |

## 2. 部署自检（先于手环）

```bash
curl -s https://你的域名/config
curl -s https://你的域名/album/114514
curl -s https://你的域名/photo/114514/chapter/1
curl -sI "https://你的域名/photo/114514/1?width=480&quality=50"
```

`/config` 应返回 `{"JMComic":{"name":...,"apiUrl":...,"detailPath":"/album/<id>","photoPath":"/photo/<id>/chapter/<chapter>","searchPath":"/search/<text>/<page>"}}`。
图片请求要看到 `Content-Type: image/jpeg` 和明确的 `Content-Length`（手环按整文件下载，不能分段流式）。

## 3. 同步到设备

1. AstroBox 插件市场安装「腕上漫画同步器」。
2. 输入漫画源地址（只填域名，**不带结尾 `/`**，例：`https://xxxx.vercel.app`），回车后插件会拉 `{域名}/config`。
3. 卡片会显示名称、key、API 地址；单源默认选中。
4. 需要登录态时，在对应 key 的卡片点「更新 Cookie」粘贴浏览器里的 `Cookie`（可选）。
5. 点「同步所选源到设备」，状态显示「命令已发送，待设备核实」。
6. 在手环上打开腕上漫画，按数字 ID 直达或关键词搜索。

## 4. 本项目的接口对应关系

| 指南 | 本项目路由 | 返回 |
|---|---|---|
| `/config` | `GET /config` | 源配置对象，key 为 `JMComic` |
| `detailPath` | `GET /album/<id>` | `item_id/name/page_count/cover/tags/total_chapters` |
| `searchPath` | `GET /search/<text>/<page>` | `page/has_more/results[{comic_id,title,cover_url,pages}]` |
| `photoPath` | `GET /photo/<id>/chapter/<chapter>` | `title/chapter/total_chapters/images[{url}]` |
| 图片本体 | `GET /photo/<photo_id>/<page>` | JPEG / PNG / LVGL，支持 `width|w`、`quality|q`、`ifPNG`、`ifLVGL` |
| 封面 | `GET /album/<id>/cover` | 支持 `width=80`（手环封面固定 80） |

图片 URL 由快应用追加参数，因此 `images[].url` 不要预先拼 `width/quality`，否则会重复。

## 5. 已知差异

- 不存在的漫画 ID 会回 `502`（上游抛错被全局兜底），指南建议 `404`；手环两种都会展示错误提示。要精确 404 需按 `jmcomic` 具体异常类型分支，未验证前不写死。
- 项目无鉴权，任何人拿到域名都能消耗上游配额；需限制时在 Vercel 前置一层口令或改用带 key 的 `/config`。
