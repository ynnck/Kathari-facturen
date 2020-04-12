from weasyprint import HTML, CSS


def write(
    data={"default": "default"}, saveName="temp.pdf", html="invoice.html",
):
    """
    Reads html and data and prints pdf file

    Parameters
    ----------
    data : TYPE, optional
        DESCRIPTION. The default is {"default": "default"}.
    invoiceRecords : TYPE, optional
        DESCRIPTION. The default is {}.
    saveName : TYPE, optional
        DESCRIPTION. The default is "temp.pdf".
    html : TYPE, optional
        DESCRIPTION. The default is "invoice.html".

    Returns
    -------
    None.

    """
    try:
        with open(html) as fp:
            html_replaced = fp.read()
    except:
        print("HTML could not be loaded")

    try:

        for key, value in data.items():
            html_replaced = html_replaced.replace("{%s}" % key, str(value))

    except:
        print("Problem with data dictionairy")

    try:
        """ 
        Old option: Pdfkit (does not work on osx, css does not load)
        options = {
            "page-size": "A4",
            "dpi": 300,
            "encoding": "utf-8",
            "margin-top": "2.5cm",
            "margin-bottom": "0cm",
            "margin-left": "2cm",
            "margin-right": "2cm",
            "quiet": ""
        }
        config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
        pdfkit.from_string(html_replaced, saveName, options=options, configuration=config)
        print("{} has been created".format(saveName)) """
        HTML(string=html_replaced).write_pdf(target=saveName)

    except Exception as e:
        print("File could not be printed")
        print(str(e))
