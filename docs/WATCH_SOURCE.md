# 接入腕上漫画（VELA 设备）

## 0. 线上地址（已部署、已验证）

```text
https://jmcomic-api.vercel.app
```

- Vercel 项目：`qaza1/jmcomic-api`，绑定 GitHub `fhgfgfgdf/RESTful-jmcomic-api` 的 `main`，push 即自动重建。
- 实测结果（2026-11-08）：

| 请求 | 结果 |
|---|---|
| `GET /config` | 200，返回 `JMComic` 源配置 |
| `GET /album/999999` | 200，`Grand Blue`，`total_chapters=127` |
| `GET /photo/999999/chapter/1` | 200，`images` 列表齐全 |
| `GET /photo/999925/1?width=480&quality=50` | 200，`image/jpeg`，`Content-Length=53372` |
| `GET /album/999999/cover?width=80` | 200，`image/jpeg`，2909 B |

## 0.1 同步器里怎么填

只填域名，**不带结尾 `/`**：`https://jmcomic-api.vercel.app` → 点「读取 / 刷新配置」→ 选中 `JMComic` → 「同步所选源到设备」。

## 1. 两个部署坑（已在仓库里改好）

- `vercel.json` 原来把 `/(.*)` rewrite 到 `/index.py`。Vercel 新版会把**改写后的路径**交给函数，Flask 收到的永远是 `/index.py`，所有接口 404。已删掉 rewrite，改由 Vercel 的 Flask 入口直接路由。
- 取封面原先不带 UA，上游对 `python-requests` 默认 UA 回 403。已给封面与 `/image/proxy` 补上 `Mozilla/5.0`。

## 2. 从零部署（换账号/重建时）

1. <https://vercel.com/new> → Import Git Repository → 选本仓库。
2. Application Preset 自动识别为 **Flask**，Root Directory `./`。
3. 环境变量先不填也能跑（不填 `CACHE_DB` 时用进程内存缓存，适合 Serverless）。
4. Deploy，拿到 `https://<项目名>.vercel.app`。

可选环境变量：`PUBLIC_URL`（自定义域名时手动指定）、`JM_DOMAINS`（上游域名，最多三个）、`IMAGE_CONCURRENCY`/`IMAGE_GLOBAL_CONCURRENCY`（Serverless 建议 1/2）。

## 3. 本地跑（不经 Vercel）

```bash
pip install -r requirements.txt
python index.py          # 默认 0.0.0.0:3002
```

## 4. 接口对应

| 指南 | 本项目路由 | 返回 |
|---|---|---|
| `/config` | `GET /config` | 源配置对象，key 为 `JMComic` |
| `detailPath` | `GET /album/<id>` | `item_id/name/page_count/cover/tags/total_chapters` |
| `searchPath` | `GET /search/<text>/<page>` | `page/has_more/results[{comic_id,title,cover_url,pages}]` |
| `photoPath` | `GET /photo/<id>/chapter/<chapter>` | `title/chapter/total_chapters/images[{url}]` |
| 图片本体 | `GET /photo/<photo_id>/<page>` | JPEG / PNG / LVGL，支持 `width|w`、`quality|q`、`ifPNG`、`ifLVGL` |
| 封面 | `GET /album/<id>/cover` | 支持 `width=80`（手环封面固定 80） |

`images[].url` 不预拼 `width/quality`——快应用自己会追加，预拼会重复。

## 5. 已知差异与限制

- 不存在的漫画 ID 会回 `502`（上游抛错被全局兜底），指南建议 `404`；要精确 404 需按 `jmcomic` 具体异常类型分支，未验证前不写死。
- 项目无鉴权，拿到域名即可消耗上游配额。
- Serverless 冷启动 + 单图解码约 2–6 秒，首次请求慢属正常（命中 CDN 后走缓存）。
