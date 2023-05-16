from datetime import datetime

expID = '2023-05-10_04_ESMT118'
target_date_str = "2023-05-10"

date_format = "%Y-%m-%d"
date_str = expID[:10]

try:
    file_date = datetime.strptime(date_str, date_format)
    target_date = datetime.strptime(target_date_str, date_format)
except ValueError:
    print("Invalid date format in the filename or target date")

result = file_date >= target_date