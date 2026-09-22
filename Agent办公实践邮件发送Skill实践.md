# Agent 办公实践：邮件发送 Skill 实践

> 会话执行记录（AI 开发者空间 AI SHELL）

## 任务流程
1. 安装技能：`git clone https://gitcode.com/agent-best-practices/SendmailSkills.git`，加载 sendmail 技能。
2. 配置邮箱：163 邮箱开启 SMTP 并生成授权码（授权码 ≠ 登录密码）。
3. 配置服务：将授权码与邮箱填入 `config/accounts.json`。
4. 批量发送：读取 `data/收件人名单.csv`（姓名/邮箱/成绩），按模板渲染为个性化邮件，SMTP 逐封发送并统计。

## 实测记录（dry-run 安全验证）
```bash
$ python3 scripts/send_batch.py --dry-run --recipients data/收件人名单.csv --template templates/score_notice.txt
共读取 3 位收件人
[1/3] [dry-run] to=zhangsan@example.edu subject=成绩通知
张三同学：... 您的成绩为 88 分。
[2/3] [dry-run] to=lisi@example.edu subject=成绩通知
李四同学：... 您的成绩为 75 分。
[3/3] [dry-run] to=wangwu@example.edu subject=成绩通知
王五同学：... 您的成绩为 92 分。
统计：成功 3，失败 0
```

- 结论：名单解析、模板渲染、批量循环、统计输出全部正确；
- 配置真实授权码后去掉 `--dry-run` 即可真实发送（本次未真实发信，保护隐私与风控）。

## 成果物
- SKILL.md（技能定义）
- scripts/send_mail.py（SMTP 发送库）+ scripts/send_batch.py（批量发送器）
- config/accounts.example.json（配置模板）
- templates/score_notice.txt（成绩通知模板）+ data/收件人名单.csv（示例名单）
