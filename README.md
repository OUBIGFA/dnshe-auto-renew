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

## 3 分钟部署

### 第 0 步：获取 API 凭证

在 <https://my.dnshe.com> 拿到这两个值：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

### 第 1 步：转成你自己的私有仓库

1. 登录 GitHub，打开 <https://github.com/new/import>
2. 按以下信息填写：

| 字段 | 填什么 |
| --- | --- |
| `Your old repository's clone URL` | `https://github.com/OUBIGFA/dnshe-auto-renew` |
| `Owner` | 你的 GitHub 账号 |
| `Repository name` | 你的仓库名，例如 `my-dnshe-auto-renew` |
| `Privacy` | 选 `Private` |

3. 点击 `Begin import`，等待导入完成
4. 后续的 Secrets、Variables 和 workflow 都在这个新仓库里设置

### 第 2 步：添加 Secrets 和 Variable

进入 `Settings -> Secrets and variables -> Actions`。

Secrets（两个）：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

Variable（一个）：

- `DNSHE_DOMAINS`

### 第 3 步：配置域名

`DNSHE_DOMAINS` 一行一个域名：

```text
abc88.cc.cd
12366.cc.cd
```

### 第 4 步：手动运行一次

打开 `Actions`，手动运行 `DNSHE Auto Renew`。

之后工作流每周自动运行一次。

## 域名管理

一行一个域名，新增加一行，删除删一行。新域名在下一次运行时自动生效。

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

## 续期规则

- 官方续期窗口为到期前 **180** 天，本工具提前 **175** 天进入判断
- 每周检查一次，只有进入窗口后才会请求续期

## 重新生成 API 凭证

在 DNSHE 后台重新生成凭证后，同步更新这两个 Secrets：

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

## 与上游同步

`.github/workflows/sync-upstream.yml` 每周一自动把本仓库对齐到上游模板：上游新增、修改的文件会同步过来，上游删除的文件也会跟着删掉。

`state/domains-state.json` 不在同步范围内，它是本仓库自己的到期时间记录。

两点注意：

- 本仓库自己加的文件，下次同步会被删掉。需要保留就加进 `sync-upstream.yml` 的 `PROTECTED_PATHS`（空格分隔）。
- Secrets 和 Variables 存在仓库设置里，不在文件树内，同步不会动它们。

`.github/workflows/` 默认不同步。想让它一起同步，需要建一个细粒度 PAT（`Contents: Read and write` + `Workflows: Read and write`），存成仓库密钥 `SYNC_TOKEN`。

## 修改执行时间

默认每周一 **04:23 UTC**。编辑 `.github/workflows/dnshe-auto-renew.yml` 的 `cron` 字段。已配置 `SYNC_TOKEN` 时，还要把该文件加进 `sync-upstream.yml` 的 `PROTECTED_PATHS`，否则下次同步会改回默认值。

## 文件说明

- `scripts/dnshe_auto_renew.py`：续期脚本
- `.github/workflows/dnshe-auto-renew.yml`：每周续期工作流
- `.github/workflows/sync-upstream.yml`：每周从上游模板同步整个仓库
- `state/domains-state.json`：本仓库的到期时间记录，接口不返回时用它兜底

## 官方文档

- [DNSHE 后台](https://my.dnshe.com)
- [DNSHE API 手册](https://my.dnshe.com/knowledgebase/1/Free-Domain-Name-Service-API-User-Manual.html)

## 许可证

MIT License
