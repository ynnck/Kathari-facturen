# Script voor genenereren facturen pdf

## TODO

- Facturen is lijst met json, maar enkel laatste wordt bijgehouden op dit moment, moet geappend worden

## files

- scriptInvoice.py: eigenlijke scriptfile
- generateInvoice.py: module om data om te zetten in een pdf
- settings.json: bestand met settings

### bedrijven.json: velden

```json
"BOS": {
    "NAAM": "",
    "AFKORTING": "BOS",
    "BTWNUMMER": "",
    "BTWPLICHTIG": false,
    "BETALINGSTERMIJN": 15,
    "ADRES": {
      "STRAAT": "",
      "NUMMER": "",
      "BUS": "",
      "POSTCODE": "",
      "GEMEENTE": ""
    },
    "DIENSTEN": {
      "SCHOONMAAK": {
        "BESCHRIJVING": "wekelijkse schoonmaak kantoor",
        "EENHEIDSPRIJS": 159.25,
        "EENHEID": "week",
        "WERKTIJDEN_EENHEID": "boolean",
        "WERKTIJDEN": {
          "MAANDAG": false,
          "DINSDAG": false,
          "WOENSDAG": false,
          "DONDERDAG": false,
          "VRIJDAG": false,
          "ZATERDAG": false,
          "ZONDAG": true
        }
      },
      "RAMEN": {
        "BESCHRIJVING": "wekelijkse schoonmaak ramen",
        "EENHEIDSPRIJS": 24.5,
        "EENHEID": "week",
        "WERKTIJDEN_EENHEID": "boolean",
        "WERKTIJDEN": {
          "MAANDAG": false,
          "DINSDAG": false,
          "WOENSDAG": false,
          "DONDERDAG": false,
          "VRIJDAG": false,
          "ZATERDAG": false,
          "ZONDAG": true
        }
      },
      "MISC": {
        "BESCHRIJVING": "schoonmaak algemeen",
        "EENHEIDSPRIJS": 24.5,
        "EENHEID": "uur",
        "WERKTIJDEN_EENHEID": "boolean",
        "WERKTIJDEN": {
          "MAANDAG": false,
          "DINSDAG": false,
          "WOENSDAG": false,
          "DONDERDAG": false,
          "VRIJDAG": false,
          "ZATERDAG": false,
          "ZONDAG": false
        }
      }
    }
  }
```

### generateInvoice: Input

- data: object
  {zoek: vervang}
  de key wordt gezocht in de template en vervangen door de value
  standaard: '{"default": "default"}'
- saveName: string
  relatief pad voor opslagen document
  standaard: "temp.pdf"
- html: string
  relatief pad voor template
  standaard: "invoice.html"

### settings: velden

- BTWPERCENTAGE: percentage voor btw, in Belgie 21%
- teller: nummer voor de volgnummer

### facturen:

json file met alle facturen in
