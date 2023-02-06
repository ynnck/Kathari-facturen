import calendar
import datetime
from collections import Counter


def getFirstDayOfMonth(date=datetime.date.today()):
    returndate = (
        date.replace(day=1)
        if isinstance(date, datetime.date)
        else datetime.date.today()
    )
    if not isinstance(date, datetime.date):
        print(
            "ingevoerde datum is geen datetime.date, \
            datum van vandaag werd gereturned"
        )
    return returndate


def getLastDayOfMonth(date=datetime.date.today()):
    returndate = (
        datetime.date(
            date.year, date.month, calendar.monthrange(date.year, date.month)[1]
        )
        if isinstance(date, datetime.date)
        else datetime.date.today()
    )
    if not isinstance(date, datetime.date):
        print(
            "ingevoerde datum is geen datetime.date, \
            datum van vandaag werd gereturned"
        )
    return returndate


def calcNumberOfDaysInMonth(date_from, date_to):
    days = Counter()

    for i in range((date_to - date_from).days + 1):
        days[(date_from + datetime.timedelta(i)).strftime("%A")] += 1
    return days


def calcNumberOfWorkingDays(unit, schedule, date_from, date_to):
    days_in_period = calcNumberOfDaysInMonth(date_from, date_to)
    number_of_work_units = 0

    if unit == "volledige dagen":
        workdays = [key.lower() for (key, value) in schedule.items() if value]
        number_of_work_units = (
            round(sum(days_in_period[day] / len(workdays) for day in workdays) * 2) / 2
        )
    # elif unit == "uren":
    # if werktijdenEenheid=='deeltijdse dagen':

    return number_of_work_units


def createStringPeriod(date_from, date_to):
    period = ""
    if date_from == getFirstDayOfMonth(date_from) and date_to == getLastDayOfMonth(
        date_to
    ):
        period = date_from.strftime("%B %Y")
    elif date_from.strftime("%m%y") == date_to.strftime("%m%y"):
        period = "{} - {} {}".format(
            date_from.strftime("%d"),
            date_to.strftime("%d"),
            date_from.strftime("%B %Y"),
        )
    else:
        period = "{} - {}".format(
            date_from.strftime("%d %B %Y"), date_to.strftime("%d %B %Y")
        )
    return period
