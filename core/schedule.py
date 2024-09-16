import json
import ical.calendar
import ical.event
import ical.types
from ical.calendar_stream import IcsCalendarStream
from pathlib import Path
import datetime
import re


def convert_to_datetime(
        first_monday: datetime.datetime, week_number: int, day_of_week: int, time: str
):
    """
    将学期第一周的周一日期、周次、星期几和时间转换为具体的日期和时间。

    Args:
        first_monday (datetime.datetime): 学期第一周的周一日期。
        week_number (int): 周次。
        day_of_week (int): 星期几（1表示星期一，2表示星期二，依次类推）。
        time (str): 时间，格式为"时:分"。

    Returns:
        datetime.datetime: 转换后的日期时间对象。
    """
    return first_monday + datetime.timedelta(
        weeks=week_number - 1,
        days=day_of_week - 1,
        hours=int(time.split(":")[0]),
        minutes=int(time.split(":")[1]),
    )


def convert_to_date(first_monday: datetime.datetime, week_number: int, day_of_week: int):
    """
    将学期第一周的周一日期、周次和星期几转换为具体的日期。

    Args:
        first_monday (datetime.datetime): 学期第一周的周一日期。
        week_number (int): 周次。
        day_of_week (int): 星期几（1表示星期一，2表示星期二，依次类推）。

    Returns:
        datetime.date: 转换后的日期对象。
    """
    return first_monday.date() + datetime.timedelta(
        weeks=week_number - 1, days=day_of_week - 1
    )


def get_time_range(date_range_str: str) -> list[datetime.datetime]:
    """
    将包含日期和时间范围的字符串转换为开始和结束时间。

    Args:
        date_range_str (str): 包含日期和时间范围的字符串，格式为"yyyy-mm-dd(HH:MM-HH:MM)"。

    Returns:
        list[datetime.datetime]: 开始时间和结束时间的列表。
    """
    date_str, time_range_str = list(filter(None, re.split(r"\(|\)", date_range_str)))
    start_time_str, end_time_str = time_range_str.split("-")

    start_time = datetime.datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
    end_time = datetime.datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")

    return [start_time, end_time]


def parse_week_ranges(week_range_str: str) -> list[list[int]]:
    """
    解析课程周次范围字符串并返回周次列表。

    Args:
        week_range_str (str): 周次范围字符串，格式为"1-4,6-8周"。

    Returns:
        list[list[int]]: 周次范围的列表。
    """
    week_ranges = []
    week_ranges_strs = week_range_str.split(",")

    for week_range in week_ranges_strs:
        parsed_range = re.split(r"-|周", week_range)
        parsed_range = [int(item) for item in parsed_range if item]
        week_ranges.append(parsed_range)

    return week_ranges


def convert_class_schedule_to_ics(
        first_monday: datetime.datetime,
        input_file_path: Path,
        output_file_path: Path,
        config_file_path: Path,
):
    """
    将课程表从JSON文件转换为ICS日历格式。

    Args:
        first_monday (datetime.datetime): 学期第一周的周一日期。
        input_file_path (Path): 包含课程表的JSON文件路径。
        output_file_path (Path): 输出ICS文件的路径。
        config_file_path (Path): 配置文件路径，包含时间表信息。
    """
    # 创建一个空的日历对象
    class_schedule = ical.calendar.Calendar()

    # 读取输入的JSON文件并解析课程列表
    with input_file_path.open("r", encoding="utf-8") as input_file:
        class_list = json.load(input_file)["kbList"]

    # 读取配置文件，获取时间表配置信息
    with config_file_path.open("r", encoding="utf-8") as config_file:
        configs = json.load(config_file)

    # 遍历课程列表，将每个课程转换为日历事件
    for class_ in class_list:
        # 解析周次范围
        week_ranges = parse_week_ranges(class_["zcd"])

        # 计算课程开始时间和结束时间
        start_time_str = configs["timetable"][class_["jcor"].split("-")[0]].split("-")[0]
        end_time_str = configs["timetable"][class_["jcor"].split("-")[-1]].split("-")[-1]

        start_time = convert_to_datetime(
            first_monday,
            week_ranges[0][0],
            int(class_["xqj"]),
            start_time_str
        )
        end_time = convert_to_datetime(
            first_monday,
            week_ranges[0][0],
            int(class_["xqj"]),
            end_time_str
        )

        # 计算需要排除的日期，即非上课周次对应的日期
        week_numbers = set()
        for week_range in week_ranges:
            week_numbers.update(range(week_range[0], week_range[-1] + 1))

        recurring_rule = ical.types.Recur(
            freq=ical.types.Frequency.WEEKLY,
            count=week_ranges[-1][-1] - week_ranges[0][0] + 1,
            interval=1,
        )

        exception_dates = []
        for week_number in range(week_ranges[0][0], week_ranges[-1][-1]):
            if week_number not in week_numbers:
                exception_dates.append(
                    convert_to_date(first_monday, week_number, int(class_["xqj"]))
                )

        # 创建课程事件，并添加到日历对象中
        class_event = ical.event.Event(
            dtstart=start_time,
            dtend=end_time,
            summary=class_["kcmc"],
            description=class_["xm"],
            location=class_["xqmc"][:-2] + " " + class_["cdmc"],
            rrule=recurring_rule,
            exdate=exception_dates,
        )
        class_schedule.events.append(class_event)

    # 将日历对象转换为ICS格式并写入输出文件
    with output_file_path.open("w", encoding="utf-8") as output_file:
        output_file.write(IcsCalendarStream.calendar_to_ics(class_schedule))
