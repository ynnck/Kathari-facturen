import calendar
import datetime
import html
import json
import locale
import os
from collections import Counter

import scripts.generateInvoicePdf as generateInvoicePdf
import scripts.query_yes_no as query_yes_no

locale.setlocale(locale.LC_ALL, "nl_BE")


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
            elif extension == "datetime":
                for date_format in ("%Y%m%d", "%Y-%m-%d", "%B %Y", "%Y/%m/%d"):
                    try:
                        # we willen datetime teruggeven,
                        # dus eerst zien dat standaardwaarde geen string is,
                        # anders omzetten naar datetime
                        value_standard = (
                            value_standard
                            if type(value_standard) == datetime.date
                            else datetime.datetime.strptime(
                                value_standard, date_format
                            ).date()
                        )
                        value_return = (
                            datetime.datetime.strptime(value_input, date_format).date()
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
    if not data[bedrijf]["ACTIEF"]:
        continue
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
        datetime.date.today().year, BEDRIJF["AFKORTING"], settings["TELLER"]
    ),
    "str",
)
# TELLER in settings updaten met ingevoerde volgnummer
settings["TELLER"] = int(REFERENCE.split("/")[2].lstrip("0"))

DATE_FROM = inputValueAndCheck(
    "begindatum factuurperiode (in formaat: jaar-maand-dag)",
    getFirstDayOfMonth(),
    "datetime",
)

DATE_TO = inputValueAndCheck(
    "einddatum factuurperiode (in formaat: jaar-maand-dag)",
    getLastDayOfMonth(date=DATE_FROM),
    "datetime",
)
PERIOD = createStringPeriod(DATE_FROM, DATE_TO)
DATE_INVOICE = DATE_TO

DATE_START_PAYMENT = (
    DATE_INVOICE if DATE_INVOICE > datetime.date.today() else datetime.date.today()
)
DATE_PAYMENT = (
    DATE_START_PAYMENT + datetime.timedelta(days=BEDRIJF["BETALINGSTERMIJN"])
    if not BEDRIJF["CONTANT"]
    else "CONTANT"
)

# FACTUURLIJNEN
RECORDS = []
for key, rec in BEDRIJF["DIENSTEN"].items():
    RECORD = {}
    RECORD["NUMBER_OF_WORKING_DAYS"] = inputValueAndCheck(
        f"aantal werkuren voor: {rec['BESCHRIJVING']} ({rec['EENHEIDSPRIJS']})",
        calcNumberOfWorkingDays(
            rec["WERKTIJDEN_EENHEID"],
            rec["WERKTIJDEN"],
            DATE_FROM,
            DATE_TO,
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
        if isinstance(val, datetime.date):
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
        '<div class="footnote"><sup>Verlegging van heffing. Bij gebrek aan schriftelijke betwisting binnen een termijn van één maand na de ontvangst van de factuur, wordt de afnemer geacht te erkennen dat hij een belastingplichtige is gehouden tot de indiening van periodieke aangiften. Als die voorwaarde niet vervuld is, is de afnemer ten aanzien van die voorwaarde aansprakelijk voor de betaling van de verschuldigde belasting, intresten en geldboeten.</sup></div>'
        if VAT == 0
        else ""
    )
    recordsInvoice += VAT_EXPL

    dataInvoice = {
        "BEDRIJFSNAAM": BEDRIJF["NAAM"],
        "ADRES": BEDRIJF["ADRES"]["STRAAT"],
        "BTWNUMMER": BEDRIJF["BTWNUMMER"],
        "NUMMER": BEDRIJF["ADRES"]["NUMMER"],
        "BUS": BEDRIJF["ADRES"]["BUS"],
        "POSTCODE": BEDRIJF["ADRES"]["POSTCODE"],
        "GEMEENTE": BEDRIJF["ADRES"]["GEMEENTE"],
        "VOLGNUMMER": str(REFERENCE).replace("/", "&#8725;"),
        "FACTUURDATUM": DATE_INVOICE.strftime("%d/%m/%Y"),
        "VERVALDATUM": DATE_PAYMENT.strftime("%d/%m/%Y")
        if not isinstance(DATE_PAYMENT, str)
        else DATE_PAYMENT,
        "PERIODE": str(PERIOD).replace(" ", "&nbsp;").replace("-", "&#45;"),
        "BTW EXCLUSIEF": TOTAL["btw exclusief"],
        "BTW INCLUSIEF": TOTAL["btw inclusief"],
        "RECORDS": recordsInvoice,
    }
    nameInvoice = "factuur_{}_{:04d}_{}.pdf".format(
        DATE_INVOICE.strftime("%Y"),
        settings["TELLER"],
        BEDRIJF["AFKORTING"],
    )
    generateInvoicePdf.write(data=dataInvoice, saveName=nameInvoice, folder="Facturen")


