import json
import datetime as dt
import calendar
import locale
import generateInvoicePdf
import query_yes_no
import os
import html

from collections import Counter

locale.setlocale(locale.LC_ALL, "nl_BE")


def getFirstDayOfMonth(date=dt.date.today()):
    returndate = date.replace(day=1) if isinstance(date, dt.date) else dt.date.today()
    if returndate == dt.date.today():
        print(
            "ingevoerde datum is geen dt.date, \
            datum van vandaag werd gereturned"
        )
    return returndate


def getLastDayOfMonth(date=dt.date.today()):
    returndate = (
        dt.date(date.year, date.month, calendar.monthrange(date.year, date.month)[1])
        if isinstance(date, dt.date)
        else date.today()
    )
    if returndate == date.today():
        print(
            "ingevoerde datum is geen dt.date, \
            datum van vandaag werd gereturned"
        )
    return returndate


def calcNumberOfDaysInMonth(date_from, date_to):
    days = Counter()

    for i in range((date_to - date_from).days + 1):
        days[(date_from + dt.timedelta(i)).strftime("%A")] += 1
    return days


def calcNumberOfWorkingDays(unit, schedule, date_from, date_to):
    days_in_period = calcNumberOfDaysInMonth(date_from, date_to)
    number_of_work_units = 0

    if unit == "volledige dagen":
        workdays = [key.lower() for (key, value) in schedule.items() if value]
        number_of_work_units = (
            round(sum(days_in_period[day] / len(workdays) for day in workdays) * 2) / 2
        )
    elif unit == "uren":
        )
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


def calcTotalAmount(records, btw=21):
    excl = round(sum(rec["AMOUNT"] for rec in records), 2) if records else 0
    incl = (
        round(sum((rec["AMOUNT"] * ((100 + rec["VAT"]) / 100)) for rec in records), 2,)
        if records
        else 0
    )
    return {"btw exclusief": excl, "btw inclusief": incl}


def inputValueAndCheck(description, value_standard, extension):
    while True:
        value_input = input("Geef %s in (default: %s):" % (description, value_standard))
        try:
            if extension == "int":
                value_return = int(value_input) if value_input else int(value_standard)
            elif extension == "float":
                value_return = (
                    float(value_input) if value_input else float(value_standard)
                )
            elif extension == "dt":
                for date_format in ("%Y%m%d", "%Y-%m-%d", "%B %Y", "%Y/%m/%d"):
                    try:
                        # we willen dt teruggeven,
                        # dus eerst zien dat standaardwaarde geen string is,
                        # anders omzetten naar dt
                        value_standard = (
                            value_standard
                            if type(value_standard) == dt.date
                            else dt.datetime.strptime(
                                value_standard, date_format
                            ).date()
                        )
                        value_return = (
                            dt.datetime.strptime(value_input, date_format).date()
                            if value_input
                            else value_standard
                        )
                    except:
                        pass
                if not value_return:
                    print(
                        '"datum in foute formaat,\
                        gelieve een juist formaat in te voeren: \
                        jaar-maand-dag of maand jaar"'
                    )
                    pass

            elif extension == "str":
                value_return = value_input if value_input else value_standard
            return value_return
        except ValueError:
            print("Foute invoer, Gelieve opnieuw te proberen")


############### BEGIN
# LEES JSONFILES EN INITIATIE
script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, "bedrijven.json")) as json_file:
    data = json.load(json_file)
with open(os.path.join(script_dir, "settings.json")) as json_file:
    settings = json.load(json_file)

FACTUUR = {"algemeen": {}, "records": []}

# KEUZE BEDRIJF
for bedrijf in data:
    print("- {} (afkorting: {})".format(data[bedrijf]["NAAM"], bedrijf))
input_company = inputValueAndCheck(
    "de afkorting van bedrijf waarvoor u een factuur wilt maken", "none", "str"
)
BEDRIJF = data[input_company.upper()]

# BTWPERCENTAGE
VAT = settings["BTWTARIEF"] if BEDRIJF["BTWPLICHTIG"] else 0

# VOLGNUMMER (+ handelen leading zeros)
REFERENCE = inputValueAndCheck(
    "volgnummer",
    "{}/{}/{:04d}".format(
        dt.date.today().year, BEDRIJF["AFKORTING"], settings["TELLER"]
    ),
    "str",
)
# TELLER in settings updaten met ingevoerde volgnummer
settings["TELLER"] = int(REFERENCE.split("/")[2].lstrip("0"))

DATE_FROM = inputValueAndCheck(
    "begindatum factuurperiode (in formaat: jaar-maand-dag)",
    getFirstDayOfMonth(),
    "dt",
)
DATE_TO = inputValueAndCheck(
    "einddatum factuurperiode (in formaat: jaar-maand-dag)", getLastDayOfMonth(date=DATE_FROM), "dt",
)
PERIOD = createStringPeriod(DATE_FROM, DATE_TO)
DATE_INVOICE = DATE_TO

DATE_START_PAYMENT = DATE_INVOICE if DATE_INVOICE > dt.date.today() else dt.date.today()
DATE_PAYMENT = DATE_START_PAYMENT + dt.timedelta(days=BEDRIJF["BETALINGSTERMIJN"])

# FACTUURLIJNEN
RECORDS = []
for (key, rec) in BEDRIJF["DIENSTEN"].items():
    RECORD = {}
    RECORD["NUMBER_OF_WORKING_DAYS"] = inputValueAndCheck(
        "aantal werkuren voor: {}".format(rec["BESCHRIJVING"]),
        calcNumberOfWorkingDays(
            rec["WERKTIJDEN_EENHEID"], rec["WERKTIJDEN"], DATE_FROM, DATE_TO,
        ),
        "float",
    )
    if RECORD["NUMBER_OF_WORKING_DAYS"] > 0:
        RECORD["DESCRIPTION"] = rec["BESCHRIJVING"]
        RECORD["AMOUNT"] = RECORD["NUMBER_OF_WORKING_DAYS"] * rec["EENHEIDSPRIJS"]
        RECORD["UNIT_PRICE"] = rec["EENHEIDSPRIJS"]
        RECORD["VAT"] = VAT
        RECORDS.append(RECORD)

TOTAL = calcTotalAmount(RECORDS)


with open(os.path.join(script_dir, "facturen.json"), "r") as read_file:
    feed = json.load(read_file)
with open(os.path.join(script_dir, "facturen.json"), "w") as write_file:

    def jsonConverter(val):
        if isinstance(val, dt.date):
            return val.strftime("%Y-%m-%d")

    feed.append(FACTUUR)
    json.dump(feed, write_file, default=jsonConverter, indent=4)

if query_yes_no.ask_question("Wilt u de factuur afprinten?"):
    recordsInvoice = ""

    for rec in RECORDS:
        # bereken string eerst en dan plakken
        VAT_SUPER = "<sup>1</sup>" if rec["VAT"] == 0 else ""
        strBtw = "{}%{}".format(rec["VAT"], VAT_SUPER)

        recordsInvoice += """
            <div class='recordsCell'>{}</div>
            <div class='recordsCell'>{}</div>
            <div class='recordsCell'>&#8364 {}</div>
            <div class='recordsCell'>{}</div>
            <div class='recordsCell'>&#8364 {}</div>
        """.format(
            rec["DESCRIPTION"],
            rec["NUMBER_OF_WORKING_DAYS"],
            rec["UNIT_PRICE"],
            strBtw,
            rec["AMOUNT"],
        )

    VAT_EXPL = (
        '<div class="footnote"><sup>1. Belasting te voldoen door de medecontractant, KB nr. 1, art. 20</sup></div>'
        if VAT == 0
        else ""
    )
    recordsInvoice += VAT_EXPL

    dataInvoice = {
        "BEDRIJFSNAAM": BEDRIJF["NAAM"],
        "ADRES": BEDRIJF["ADRES"]["STRAAT"],
        "NUMMER": BEDRIJF["ADRES"]["NUMMER"],
        "BUS": BEDRIJF["ADRES"]["BUS"],
        "POSTCODE": BEDRIJF["ADRES"]["POSTCODE"],
        "GEMEENTE": BEDRIJF["ADRES"]["GEMEENTE"],
        "VOLGNUMMER": str(REFERENCE).replace("/", "&#8725;"),
        "FACTUURDATUM": DATE_INVOICE.strftime("%d/%m/%Y"),
        "VERVALDATUM": DATE_PAYMENT.strftime("%d/%m/%Y"),
        "PERIODE": str(PERIOD).replace(" ", "&nbsp;").replace("-", "&#45;"),
        "BTW EXCLUSIEF": TOTAL["btw exclusief"],
        "BTW INCLUSIEF": TOTAL["btw inclusief"],
        "RECORDS": recordsInvoice,
    }
    nameInvoice = "factuur_{}_{:04d}_{}.pdf".format(
        DATE_INVOICE.strftime("%Y"), settings["TELLER"], BEDRIJF["AFKORTING"],
    )
    generateInvoicePdf.write(data=dataInvoice, saveName=nameInvoice)

with open(os.path.join(script_dir, "settings.json"), "w") as write_file:
    settings["TELLER"] += 1
    json.dump(settings, write_file, indent=4)
