---
name: sendmail
description: "支持 Agent 通过 SMTP 协议自动发送邮件。用户只需配置邮箱账号与授权码（QQ/163/126/新浪/Gmail），即可让 AI 智能体自动撰写并发送邮件，支持批量发送与模板渲染。"
version: "1.0.0"
metadata:
  dependencies:
    - "./scripts/send_mail.py"
    - "./scripts/send_batch.py"
    - "./config/accounts.example.json"
---

# Sendmail — Agent 发邮件技能

## 角色定位
邮件发送执行器：将用户或上游 Agent 的邮件意图转化为真实邮件发送操作。封装 SMTP 全流程，支持纯文本/HTML、多邮箱服务商、多账号路由、批量发送与个性化模板。

## 核心能力
- SMTP 发送纯文本 / HTML 邮件（仅依赖 Python 标准库 smtplib/email）
- 自动识别 QQ/163/126/新浪/Gmail 服务商（免填 host/port）
- 批量发送：读取收件人名单 → 模板渲染 → 逐封发送 → 统计成功/失败
- 安全 dry-run：`--dry-run` 仅预览不真实发送

## 配置
1. 获取邮箱授权码（163：设置→POP3/SMTP/IMAP→开启 SMTP→生成授权码）；
2. 按 `config/accounts.example.json` 填写 `config/accounts.json`；
3. **授权码不是登录密码**，不要硬编码进代码。

## 使用
```bash
# 单发
python scripts/send_mail.py --config config/accounts.json --to "x@x.com" --subject "标题" --body "正文"

# 批量（模板变量用 {{姓名}}/{{成绩}} 占位）
python scripts/send_batch.py --recipients data/收件人名单.csv --template templates/score_notice.txt

# 安全预览
python scripts/send_batch.py --dry-run --recipients data/收件人名单.csv
```

## 注意事项
- 遵守邮箱每日发送限额，批量加 0.5s 延时；
- 敏感配置放独立配置文件/环境变量，不进代码仓库；
- 记录发送结果，失败项可重试；实践完成后销毁授权码。
