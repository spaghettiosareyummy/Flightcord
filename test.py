import datetime

date_example = "2022-11-25 08:11Z".replace("Z", "").replace(" ", ", ")
date_format = datetime.datetime.strptime(date_example, "%Y-%m-%d, %H:%M")

unix_time = datetime.datetime.timestamp(date_format)
print(int(unix_time))