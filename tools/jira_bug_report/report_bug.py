"""CLI для подачи бага в Jira по результатам прогона автотестов.

Намеренно отдельный инструмент, а не часть tests/ — это не автотест,
а разовая команда, которую запускает человек (или Claude Code по его просьбе)
после того, как прогон тестов выявил баг и бага решили завести.

Примеры:

    # 1) черновик — ничего не создаёт, только показывает, что будет отправлено,
    #    и есть ли уже такой тикет (по fingerprint)
    python -m tools.jira_bug_report.report_bug file \\
        --title "Jira-консьюмер: бесконечный retry на HTTP 400 от log_work" \\
        --component "vinnie-assistant-jira-consumer" \\
        --environment "docker-compose local, apache/kafka:4.0.0, Jira Cloud" \\
        --steps "1. Создать entry с time_spent=''" "2. Consumer публикует log_work в Jira" \\
        --expected "Consumer помечает entry как error и даёт очереди двигаться дальше (как для 404 not_found)" \\
        --actual "Consumer ретраит HTTP 400 бесконечно, блокируя обработку всех следующих сообщений в очереди" \\
        --severity high \\
        --evidence-file /tmp/consumer.log \\
        --fingerprint-seed "jira-consumer:infinite-retry-on-400-logwork"

    # 2) то же самое, но реально создать тикет в Jira
    ...--yes

    # 3) отметить повторное воспроизведение на существующем тикете
    python -m tools.jira_bug_report.report_bug comment --issue KAN-23 --text "Воспроизвелось повторно 2026-10-23, см. run_id=..."
"""

import argparse
import os
import sys
import textwrap

from dotenv import load_dotenv

from .jira_bug_client import JiraBugClient

SEVERITIES = ("blocker", "high", "medium", "low")


def build_description(
    component: str,
    environment: str,
    steps: list[str],
    expected: str,
    actual: str,
    severity: str,
    evidence: str | None,
) -> str:
    steps_block = "\n".join(steps)
    parts = [
        f"*Component:* {component}",
        f"*Environment:*\n{environment}",
        f"*Steps to reproduce:*\n{steps_block}",
        f"*Expected:*\n{expected}",
        f"*Actual:*\n{actual}",
        f"*Severity:* {severity}",
    ]
    if evidence:
        parts.append(f"*Evidence:*\n{{code}}\n{evidence}\n{{code}}")
    return "\n\n".join(parts)


def cmd_file(args: argparse.Namespace) -> int:
    client = JiraBugClient.from_env()
    fingerprint = JiraBugClient.make_fingerprint(args.fingerprint_seed)

    evidence = args.evidence
    if args.evidence_file:
        with open(args.evidence_file, encoding="utf-8") as f:
            evidence = f.read()[-4000:]  # хвост лога — самое релевантное, без раздувания тикета

    description = build_description(
        component=args.component,
        environment=args.environment,
        steps=args.steps,
        expected=args.expected,
        actual=args.actual,
        severity=args.severity,
        evidence=evidence,
    )

    existing = client.find_existing(fingerprint)
    if existing:
        print(f"Уже есть тикет с этим fingerprint: {client.issue_url(existing['key'])} ({existing['fields']['status']['name']})")
        print("Создавать дубликат не буду. Если хочешь отметить повторное воспроизведение — используй subcommand 'comment'.")
        return 0

    component_label = args.component.lower().replace(" ", "-")
    all_labels = ["autobug", f"severity-{args.severity}", component_label, *args.label]

    print("=== Черновик бага (дубликатов по fingerprint не найдено) ===")
    print(f"Title: {args.title} [fp:{fingerprint}]")
    print(f"Project: {client.project_key}")
    print(f"Labels: {', '.join(all_labels)}")
    print()
    print(description)
    print()

    if not args.yes:
        print("Это предпросмотр. Чтобы реально создать тикет в Jira, повтори команду с флагом --yes.")
        return 0

    created = client.create_bug(
        title=args.title,
        description=description,
        fingerprint=fingerprint,
        severity=args.severity,
        labels=[component_label, *args.label],
    )
    print(f"Создан тикет: {client.issue_url(created['key'])}")
    return 0


def cmd_comment(args: argparse.Namespace) -> int:
    client = JiraBugClient.from_env()
    client.add_comment(args.issue, args.text)
    print(f"Комментарий добавлен: {client.issue_url(args.issue)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env.test")
    load_dotenv(".env")

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    file_parser = subparsers.add_parser("file", help="Завести баг (с дедупликацией по fingerprint)")
    file_parser.add_argument("--title", required=True)
    file_parser.add_argument("--component", required=True)
    file_parser.add_argument("--environment", required=True)
    file_parser.add_argument("--steps", required=True, nargs="+", help="Шаги воспроизведения, по одному на аргумент")
    file_parser.add_argument("--expected", required=True)
    file_parser.add_argument("--actual", required=True)
    file_parser.add_argument("--severity", required=True, choices=SEVERITIES)
    file_parser.add_argument("--evidence", help="Текст доказательства (лог/стектрейс) прямо в аргументе")
    file_parser.add_argument("--evidence-file", help="Путь к файлу с логом — альтернатива --evidence")
    file_parser.add_argument(
        "--fingerprint-seed",
        required=True,
        help=textwrap.dedent("""\
            Стабильная строка-идентификатор ПРИЧИНЫ дефекта (не прогона!) —
            например 'jira-consumer:infinite-retry-on-400-logwork'.
            Должна быть одинаковой при каждом повторном обнаружении ТОГО ЖЕ бага,
            иначе дедупликация не сработает и тикеты задвоятся."""),
    )
    file_parser.add_argument("--label", action="append", default=[], help="Доп. метка, можно указать несколько раз")
    file_parser.add_argument("--yes", action="store_true", help="Реально создать тикет (без флага — только предпросмотр)")
    file_parser.set_defaults(func=cmd_file)

    comment_parser = subparsers.add_parser("comment", help="Добавить комментарий к существующему багу")
    comment_parser.add_argument("--issue", required=True, help="Ключ тикета, например KAN-23")
    comment_parser.add_argument("--text", required=True)
    comment_parser.set_defaults(func=cmd_comment)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
