#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量邮件发送器：读取收件人名单(Excel) → 按模板逐封发送 → 输出成功/失败统计
支持 `--dry-run`：不真实发送，仅打印将发送的内容（用于配置验证与演示）。
"""
import argparse, csv, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from send_mail import send_email  # noqa: E402

def load_recipients(path):
    """支持 CSV / XLSX(简单CSV导出) 名单：列 姓名,邮箱,成绩(可选)"""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    # 兜底：按行解析 txt
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        name, email = line.split(",", 1)
        out.append({"姓名": name.strip(), "邮箱": email.strip()})
    return out

def render(template, row):
    text = template
    for k, v in row.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text

def main():
    ap = argparse.ArgumentParser(description="批量邮件发送（支持 --dry-run）")
    ap.add_argument("--config", default="config/accounts.json")
    ap.add_argument("--recipients", required=True, help="收件人名单 CSV：姓名,邮箱[,字段...]")
    ap.add_argument("--subject", default="成绩通知")
    ap.add_argument("--template", default="templates/score_notice.txt", help="模板文件，用 {{字段}} 占位")
    ap.add_argument("--dry-run", action="store_true", help="不真实发送，仅预览")
    args = ap.parse_args()

    rows = load_recipients(args.recipients)
    print(f"共读取 {len(rows)} 位收件人")
    template = Path(args.template).read_text(encoding="utf-8")
    ok = fail = 0
    for i, row in enumerate(rows, 1):
        body = render(template, row)
        to = row["邮箱"]
        if args.dry_run:
            print(f"[{i}/{len(rows)}] [dry-run] to={to} subject={args.subject}\n{body[:120]}...\n")
            ok += 1
            continue
        try:
            send_email(config_path=args.config, to=to, subject=args.subject, body=body)
            print(f"[{i}/{len(rows)}] ✅ 已发送 {to}")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(rows)}] ❌ 失败 {to}: {e}")
            fail += 1
        # 批量节奏：避免触发风控
        import time; time.sleep(0.5)
    print(f"\n统计：成功 {ok}，失败 {fail}")

if __name__ == "__main__":
    main()
