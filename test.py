import datetime


def accurate_utc_conv(date: str):
    date_str = str(date)
    date_format = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    unix_time = datetime.datetime.timestamp(date_format)
    return int(unix_time)


print(accurate_utc_conv(datetime.datetime.now()))
