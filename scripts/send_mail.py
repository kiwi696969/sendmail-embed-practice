#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sendmail — Agent 发邮件技能的核心脚本
仅依赖 Python 标准库（smtplib + email），支持 QQ/163/126/新浪/Gmail 多邮箱。

用法：
  1. CLI 模式：
     python send_mail.py --config ../config/accounts.json --to "x@x.com" --subject "标题" --body "正文"

  2. 模块模式：
     from send_mail import send_email
     send_email(config_path="...", to="x@x.com", subject="标题", body="正文")
"""
import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from pathlib import Path
from typing import Optional, Union, List, Dict

# 常用邮箱服务商 SMTP 预设
PROVIDERS = {
    "qq":    {"host": "smtp.qq.com",    "port": 587, "label": "QQ邮箱"},
    "163":   {"host": "smtp.163.com",   "port": 465, "label": "163邮箱"},
    "126":   {"host": "smtp.126.com",   "port": 465, "label": "126邮箱"},
    "sina":  {"host": "smtp.sina.com",  "port": 465, "label": "新浪邮箱"},
    "gmail": {"host": "smtp.gmail.com", "port": 587, "label": "Gmail"},
}

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "accounts.json"


def _load_accounts(config_path: str) -> List[Dict]:
    """加载配置文件中的账号列表"""
    path = Path(config_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("accounts", [])
    except (json.JSONDecodeError, OSError):
        return []


def _resolve_account(accounts: List[Dict], from_addr: Optional[str]) -> Optional[Dict]:
    """根据发件人地址解析账号（含 SMTP 服务器/端口推断）"""
    if not accounts:
        return None

    account = None
    if from_addr:
        for acc in accounts:
            if acc.get("user") == from_addr:
                account = acc
                break
    if account is None:
        account = accounts[0]  # 默认用第一个账号

    # 推断 SMTP 服务器和端口
    provider = account.get("provider", "")
    if provider in PROVIDERS:
        account["host"] = PROVIDERS[provider]["host"]
        account["port"] = PROVIDERS[provider]["port"]
    elif provider == "custom":
        if not account.get("host") or not account.get("port"):
            return None
    else:
        # 未指定 provider，尝试从邮箱域名推断
        user = account.get("user", "")
        domain = user.split("@")[-1] if "@" in user else ""
        inferred = {
            "qq.com": "qq", "163.com": "163", "126.com": "126",
            "sina.com": "sina", "sina.cn": "sina", "gmail.com": "gmail",
        }.get(domain)
        if inferred and inferred in PROVIDERS:
            account["host"] = PROVIDERS[inferred]["host"]
            account["port"] = PROVIDERS[inferred]["port"]
        else:
            # 无法推断，尝试通用规则
            if not account.get("host"):
                account["host"] = f"smtp.{domain}"
                account["port"] = 465
    return account


def _split_addresses(value: Optional[Union[str, List[str]]]) -> List[str]:
    """把收件人参数转成列表"""
    if not value:
        return []
    if isinstance(value, str):
        return [a.strip() for a in value.replace(";", ",").split(",") if a.strip()]
    if isinstance(value, list):
        return [a.strip() for a in value if a and str(a).strip()]
    return []


def send_email(
    config_path: str = "",
    from_addr: Optional[str] = None,
    to: Union[str, List[str]] = "",
    subject: str = "",
    body: str = "",
    is_html: bool = False,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    attachment: Optional[str] = None,
) -> Dict:
    """发送邮件（核心函数）

    返回 {"ok": bool, "message": str} 或 {"ok": bool, "error": str}
    """
    cfg_path = config_path or str(DEFAULT_CONFIG_PATH)
    accounts = _load_accounts(cfg_path)

    # 参数校验
    to_list = _split_addresses(to)
    if not to_list:
        return {"ok": False, "error": "缺少收件人（to）"}
    if not subject:
        return {"ok": False, "error": "缺少邮件主题（subject）"}
    if not body:
        return {"ok": False, "error": "缺少邮件正文（body）"}

    if not accounts:
        return {
            "ok": False,
            "error": f"未找到配置文件 {cfg_path}，请先复制 accounts.example.json 为 accounts.json 并填入邮箱账号与授权码",
        }

    account = _resolve_account(accounts, from_addr)
    if account is None:
        return {"ok": False, "error": "无法解析发件人账号，请检查配置文件"}

    smtp_user = account.get("user", "")
    smtp_password = account.get("auth_code", "")
    smtp_host = account.get("host", "")
    smtp_port = int(account.get("port", 465))
    from_name = account.get("from_name", "") or smtp_user

    if not smtp_user or not smtp_password:
        return {"ok": False, "error": f"账号 {smtp_user} 未配置授权码，请检查配置文件"}

    # 构造邮件
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject

    if cc:
        cc_list = _split_addresses(cc)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
            to_list = to_list + cc_list

    # 收件人（含抄送密送）
    all_recipients = list(to_list)
    bcc_list = _split_addresses(bcc)
    if bcc_list:
        all_recipients += bcc_list

    # 正文
    content_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))

    # 附件
    if attachment:
        att_path = Path(attachment)
        if att_path.exists() and att_path.is_file():
            with open(att_path, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=("utf-8", "", att_path.name),
                )
                msg.attach(part)
        else:
            return {"ok": False, "error": f"附件不存在: {attachment}"}

    # 发送
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, all_recipients, msg.as_string())
        server.quit()
        return {"ok": True, "message": f"邮件已发送至 {', '.join(to_list)}"}
    except smtplib.SMTPAuthenticationError:
        return {
            "ok": False,
            "error": (
                "SMTP 认证失败：授权码错误。"
                "QQ/163/126/新浪邮箱请使用「授权码」（非登录密码），"
                "Gmail 请使用「应用专用密码」。"
            ),
        }
    except smtplib.SMTPConnectError:
        return {"ok": False, "error": f"无法连接 SMTP 服务器 {smtp_host}:{smtp_port}，请检查网络和服务器地址"}
    except Exception as e:
        return {"ok": False, "error": f"发送失败: {str(e)}"}


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Sendmail — Agent 发邮件技能")
    parser.add_argument("--config", default="", help="配置文件路径（默认 config/accounts.json）")
    parser.add_argument("--from", dest="from_addr", default=None, help="发件人邮箱（不传用第一个账号）")
    parser.add_argument("--to", required=True, help="收件人邮箱（多个用逗号分隔）")
    parser.add_argument("--subject", required=True, help="邮件主题")
    parser.add_argument("--body", required=True, help="邮件正文")
    parser.add_argument("--html", action="store_true", help="正文为 HTML")
    parser.add_argument("--cc", default=None, help="抄送")
    parser.add_argument("--bcc", default=None, help="密送")
    parser.add_argument("--attachment", default=None, help="附件路径")
    return parser.parse_args()


def main():
    args = _parse_args()
    result = send_email(
        config_path=args.config,
        from_addr=args.from_addr,
        to=args.to,
        subject=args.subject,
        body=args.body,
        is_html=args.html,
        cc=args.cc,
        bcc=args.bcc,
        attachment=args.attachment,
    )
    if result.get("ok"):
        print(result["message"])
        sys.exit(0)
    else:
        print(f"[错误] {result.get('error', '未知错误')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
