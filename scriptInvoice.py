import json
import datetime
import calendar
import locale
import generateInvoice
import query_yes_no

locale.setlocale(locale.LC_ALL, 'nl_BE')


def getLastDayOfMonth(date=datetime.date.today()):
    if isinstance(date, datetime.date):
        return datetime.date(
            date.year,
            date.month,
            calendar.monthrange(date.year, date.month)[1])
    print('ingevoerde datum is geen datetime.date, \
           datum van vandaag werd gereturned')
    return datetime.date.today()


def calcNumberOfDaysInMonth(datum):
    dagen = {
        'MAANDAG': 0,
        'DINSDAG': 0,
        'WOENSDAG': 0,
        'DONDERDAG': 0,
        'VRIJDAG': 0,
        'ZATERDAG': 0,
        'ZONDAG': 0
    }
    for dag in range(1, calendar.monthrange(datum.year, datum.month)[1] + 1):
        weekdag = datetime.date(datum.year, datum.month, dag).isoweekday()
        if weekdag == 1:
            dagen['MAANDAG'] += 1
        elif weekdag == 2:
            dagen['DINSDAG'] += 1
        elif weekdag == 3:
            dagen['WOENSDAG'] += 1
        elif weekdag == 4:
            dagen['DONDERDAG'] += 1
        elif weekdag == 5:
            dagen['VRIJDAG'] += 1
        elif weekdag == 6:
            dagen['ZATERDAG'] += 1
        elif weekdag == 7:
            dagen['ZONDAG'] += 1
    return dagen


def calcNumberOfWorkingDays(eenheid, werktijdenEenheid, werktijden, datum):
    dagenInMaand = calcNumberOfDaysInMonth(datum)
    aantalDagen = 0

    if werktijdenEenheid == 'boolean':
        werkdagen = []
        for key, value in werktijden.items():
            if value:
                werkdagen.append(key)
        for werkdag in werkdagen:
            aantalDagen += dagenInMaand[werkdag]/len(werkdagen)

    # if werktijdenEenheid=='uur':
        # NOG UITDENKEN HOE DIT GEPRINT GAAT WORDEN? PER UUR DAN?

    return round(aantalDagen * 2) / 2


def calcTotalAmount(factuurlijnen, btw=21):
    excl = 0
    for lijn in factuurlijnen:
        excl += lijn['AMOUNT']
    incl = excl * (1 + (btw / 100))
    return {'btw exclusief': round(excl, 2), 'btw inclusief': round(incl, 2)}


def inputValueAndCheck(beschrijving, standaardwaarde, typeBestand):
    while True:
        inputwaarde = input('Geef %s in (default: %s):' %
                            (beschrijving, standaardwaarde))
        try:
            if typeBestand == 'int':
                return int(inputwaarde) \
                    if inputwaarde else int(standaardwaarde)
            if typeBestand == 'float':
                return float(inputwaarde) \
                    if inputwaarde else float(standaardwaarde)
            elif typeBestand == 'datetime':
                for fmt in ('%Y-%m-%d', '%B %Y', '%Y/%m/%d'):
                    try:
                        # we willen datetime teruggeven,
                        # dus eerst zien dat standaardwaarde geen string is,
                        # anders omzetten naar datetime
                        standaardwaarde = standaardwaarde \
                            if type(standaardwaarde) == datetime.date \
                            else datetime.datetime.strptime(standaardwaarde,
                                                            fmt)
                        return datetime.datetime.strptime(inputwaarde, fmt) \
                            if inputwaarde else standaardwaarde
                    except ValueError:
                        pass
                raise ValueError(
                    'datum in foute formaat,\
                     gelieve een juist formaat in te voeren: \
                     jaar-maand-dag of maand jaar')
            elif typeBestand == 'str':
                return inputwaarde if inputwaarde else standaardwaarde
        except ValueError:
            print('Foute invoer, Gelieve opnieuw te proberen')


############### BEGIN
# LEES JSONFILES EN INITIATIE
with open('/home/ynnck/Git/CleanCo-facturen/bedrijven.json') as json_file:
    data = json.load(json_file)
with open('/home/ynnck/Git/CleanCo-facturen/settings.json') as json_file:
    settings = json.load(json_file)
FACTUUR = {'algemeen': {}, 'records': []}

# KEUZE BEDRIJF
for bedrijf in data:
    print('- %s (afkorting: %s)' % (data[bedrijf]['NAAM'], bedrijf))
INPUT_KEUZE_BEDRIJF = inputValueAndCheck(
    'de afkorting van bedrijf waarvoor u een factuur wilt maken',
    'none',
    'str')
BEDRIJF = data[INPUT_KEUZE_BEDRIJF]

# BTWPERCENTAGE
FACTUUR['algemeen']['BTW-percentage'] = settings['BTWTARIEF'] \
    if BEDRIJF['BTWPLICHTIG'] else 0

# VOLGNUMMER (+ handelen leading zeros)
FACTUUR['algemeen']['volgnummer'] = inputValueAndCheck(
    'volgnummer',
    '%d/%s/%04d' % (datetime.date.today().year, BEDRIJF['AFKORTING'], settings['TELLER']), 'str')
volgnummer_split = FACTUUR['algemeen']['volgnummer'].split('/')
volgnummer_split[2] = volgnummer_split[2].lstrip('0')
FACTUUR['algemeen']['volgnummer'] = '/'.join(volgnummer_split)
settings['TELLER'] = int(volgnummer_split[2])

#PERIODE
FACTUUR['algemeen']['periode'] = inputValueAndCheck(
    'factuurperiode (in formaat: maand jaar)',
    datetime.date.today().strftime("%B %Y"),
    'datetime')

#FACTUURDATUM
FACTUUR['algemeen']['factuurdatum'] = inputValueAndCheck(
    'factuurdatum (in formaat: jaar-maand-dag)',
    getLastDayOfMonth(datetime.date.today()),
    'datetime')

#VERVALDATUM
FACTUUR['algemeen']['vervaldatum'] = FACTUUR['algemeen']['factuurdatum'] + \
    datetime.timedelta(days=BEDRIJF['BETALINGSTERMIJN'])

# FACTUURLIJNEN
for (key, rec) in BEDRIJF['DIENSTEN'].items():
    RECORD = {}
    RECORD['BESCHRIJVING'] = rec['BESCHRIJVING']
    RECORD['NUMBER_OF_WORKING_DAYS'] = calcNumberOfWorkingDays(
        rec['EENHEID'],
        rec['WERKTIJDEN_EENHEID'],
        rec['WERKTIJDEN'],
        FACTUUR['algemeen']['periode'])
    RECORD['NUMBER_OF_WORKING_DAYS'] = inputValueAndCheck(
            'aantal werkuren voor: %s' % rec['BESCHRIJVING'],
            RECORD['NUMBER_OF_WORKING_DAYS'],
            'float')
    RECORD['AMOUNT'] = RECORD['NUMBER_OF_WORKING_DAYS'] * rec['EENHEIDSPRIJS']
    RECORD['UNIT_PRICE'] = rec['EENHEIDSPRIJS']

    FACTUUR['records'].append(RECORD)

FACTUUR['algemeen']['totaalbedrag'] = calcTotalAmount(
    FACTUUR['records'],
    FACTUUR['algemeen']['BTW-percentage'])


with open("/home/ynnck/Git/CleanCo-facturen/facturen.json", "w") as write_file:
    def jsonConverter(val):
        if isinstance(val, datetime.date):
            return val.strftime("%Y-%m-%d")
    json.dump(FACTUUR, write_file, default=jsonConverter, indent=4)

if query_yes_no.ask_question('Wilt u de factuur afprinten?'):
    recordsInvoice = ""
    strBtwVerlegd = False
    for rec in FACTUUR['records']:
        
        if rec['NUMBER_OF_WORKING_DAYS'] > 0: 
            strBtw = '%s %%' % FACTUUR['algemeen']['BTW-percentage']
            if FACTUUR['algemeen']['BTW-percentage'] == 0:
                strBtw += '<sup>1</sup>'
                strBtwVerlegd = True

            recordsInvoice += '''
                <div class='recordsCell'>%s</div>
                <div class='recordsCell'>%s</div>
                <div class='recordsCell'>&#8364 %s</div>
                <div class='recordsCell'>%s</div>
                <div class='recordsCell'>&#8364 %s</div>
            ''' % (rec['BESCHRIJVING'], rec['NUMBER_OF_WORKING_DAYS'], rec['UNIT_PRICE'], strBtw, rec['AMOUNT'])

    if strBtwVerlegd:
        recordsInvoice += '<div class="footnote"><sup>1. Belasting te voldoen door de medecontractant, KB nr. 1, art. 20</sup></div>'

    dataInvoice = {"BEDRIJFSNAAM": BEDRIJF['NAAM'],
                   "ADRES": BEDRIJF['ADRES']['STRAAT'],
                   "NUMMER": BEDRIJF['ADRES']['NUMMER'],
                   "BUS": BEDRIJF['ADRES']['BUS'],
                   "POSTCODE": BEDRIJF['ADRES']['POSTCODE'],
                   "GEMEENTE": BEDRIJF['ADRES']['GEMEENTE'],
                   "VOLGNUMMER": FACTUUR['algemeen']['volgnummer'],
                   "FACTUURDATUM": FACTUUR['algemeen']['factuurdatum'].strftime("%d/%m/%Y"),
                   "VERVALDATUM": FACTUUR['algemeen']['vervaldatum'].strftime("%d/%m/%Y"),
                   "PERIODE": FACTUUR['algemeen']['periode'].strftime("%B %Y"),
                   "BTW EXCLUSIEF": FACTUUR['algemeen']['totaalbedrag']['btw exclusief'],
                   "BTW INCLUSIEF": FACTUUR['algemeen']['totaalbedrag']['btw inclusief'],
                   "RECORDS": recordsInvoice}
    nameInvoice = "factuur_%s_%04d_%s.pdf" % (
        FACTUUR['algemeen']['periode'].strftime("%Y"), settings['TELLER'], BEDRIJF['AFKORTING'])
    generateInvoice.write(data=dataInvoice, saveName=nameInvoice)

with open("/home/ynnck/Git/CleanCo-facturen/settings.json", "w") as write_file: 
    settings['TELLER'] += 1
    json.dump(settings, write_file, indent=4)