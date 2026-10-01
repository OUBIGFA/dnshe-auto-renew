<div align="center">
  <h1>DNSHE 免费域名自动续期</h1>
  <p>每周自动检查 DNSHE 域名，到期前自动免费续期</p>
  <p>简体中文 | <a href="README.en.md">English</a></p>
  <p>
    <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB">
    <img alt="Platform" src="https://img.shields.io/badge/platform-GitHub%20Actions-2088FF">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-111827">
    <img alt="Schedule" src="https://img.shields.io/badge/schedule-Weekly-22c55e">
  </p>
</div>

> 只需 3 分钟部署，之后每周自动检查并续期你的 DNSHE 免费域名。

## 3 分钟部署

### 第 0 步：获取 DNSHE API 凭证

打开：

- https://my.dnshe.com

准备好这两个值：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

### 第 1 步：用 GitHub Importer 转成私有仓库

1. 登录 GitHub，打开 <https://github.com/new/import>
2. 按以下信息填写：

| 字段 | 填什么 |
| --- | --- |
| `Your old repository's clone URL` | `https://github.com/OUBIGFA/dnshe-auto-renew` |
| `Owner` | 你的 GitHub 账号 |
| `Repository name` | 你的仓库名，例如 `my-dnshe-auto-renew` |
| `Privacy` | 选 `Private` |

3. 点击 `Begin import`，等待导入完成（通常几十秒到几分钟）
4. 导入完成后，GitHub 会生成一个属于你自己的私有仓库，后续的 Secrets、Variables 和 workflow 都在这个仓库里设置

### 第 2 步：添加 GitHub Secrets 和 Variable

进入：

- `Settings -> Secrets and variables -> Actions`

添加 Secrets：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

添加 Variable：

- `DNSHE_DOMAINS`

### 第 3 步：配置域名

`DNSHE_DOMAINS` 一行一个域名：

```text
abc88.cc.cd
12366.cc.cd
```

### 第 4 步：手动运行一次

打开 GitHub 的 `Actions`，手动运行 `DNSHE Auto Renew`。

第一次运行会检查域名，之后工作流每周自动运行一次。

## 域名管理

### 填写格式

一行一个域名，新增就加一行，删除就删一行：

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

### 新增域名

只需把新域名追加到 `DNSHE_DOMAINS`。下一次 workflow 运行时自动发现新域名，并读取接口返回的到期时间。不需要手动填注册时间或到期时间。

### 为什么不用手填到期时间

- 到期时间直接读接口返回的 `expires_at`
- 续期成功后接口会返回新的 `expires_at`，自动向下滚动
- 接口不返回到期时间时，回退到 `created_at + 365` 天

## 续期规则

默认规则：

- 官方续期窗口为到期前 `180` 天，本工具提前 `175` 天进入判断
- 每周检查一次
- 只有进入窗口后才会请求续期

## 重新生成 API 凭证

如果你在 DNSHE 后台重新生成了 API 凭据，同步更新 GitHub Secrets 即可：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

## 与上游同步

`.github/workflows/sync-upstream.yml` 每周一自动把本仓库对齐到上游模板：上游新增、修改的文件会同步过来，上游删掉的文件也会跟着删掉。

唯一的例外是 `PROTECTED_PATHS`，默认只含 `state/domains-state.json` —— 它是本仓库自己的到期时间记录，被覆盖会导致重复续期。

两点注意：

- 放在本仓库的其他文件会在下次同步时被删除。需要保留就加进 `sync-upstream.yml` 的 `PROTECTED_PATHS`（空格分隔）。
- Secrets 和 Variables（`DNSHE_API_KEY`、`DNSHE_DOMAINS` 等）存在仓库设置里，不在文件树内，同步不会动它们。

### 工作流文件默认不同步

Actions 自带的 `GITHUB_TOKEN` 无法创建或修改 `.github/workflows/` 下的文件，这是平台限制，`permissions` 块和仓库设置都提不了权。没配 `SYNC_TOKEN` 时本工作流会自动跳过该目录，避免整次同步因为推送被拒而失败。

想让工作流也跟着自动同步，建一个细粒度 PAT（`Contents: Read and write` + `Workflows: Read and write`），存成仓库密钥 `SYNC_TOKEN` 即可。

## 修改执行时间

默认每周一 04:23 UTC。编辑 `.github/workflows/dnshe-auto-renew.yml` 中的 `cron` 字段，并把该文件加进 `sync-upstream.yml` 的 `PROTECTED_PATHS`，否则下次同步会改回默认值。

## 文件说明

- `scripts/dnshe_auto_renew.py`：续期脚本
- `.github/workflows/dnshe-auto-renew.yml`：每周 GitHub Actions 工作流
- `.github/workflows/sync-upstream.yml`：每周从上游模板同步整个仓库
- `state/domains-state.json`：状态文件，保存最近解析到的到期时间，接口不返回时用它兜底；内容变化才会提交

## 官方文档

- [DNSHE 后台](https://my.dnshe.com)
- [DNSHE API 手册](https://my.dnshe.com/knowledgebase/1/Free-Domain-Name-Service-API-User-Manual.html)

## 许可证

MIT License
