from core import schedule
import datetime
import tzlocal
import argparse
from pathlib import Path


def parse_date(date_str: str) -> datetime.datetime:
    """
    解析日期字符串并返回带时区信息的日期时间对象。

    Args:
        date_str (str): 日期字符串，格式为"YYYY-MM-DD"。

    Returns:
        datetime.datetime: 带时区信息的日期时间对象。
    """
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=tzlocal.get_localzone()
    )


def main():
    parser = argparse.ArgumentParser(description="帮助")

    parser.add_argument(
        "-f",
        "--first-Monday",
        type=parse_date,
        help="该学期第一周周一的日期（格式为年-月-日）",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="输入文件路径",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="输出文件路径",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=Path(r".\config.json"),
        type=Path,
        help="配置文件路径",
    )

    args = parser.parse_args()

    schedule.convert_class_schedule_to_ics(
        args.first_Monday, args.input, args.output, args.config
    )


if __name__ == "__main__":
    main()
