from weasyprint import HTML, CSS
import os


def write(
    data={"default": "default"}, saveName="temp.pdf", html="invoice.html", folder=None, **args
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
    folder: STRING, optional
        DESCRIPTION. The defauls is None

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
        target = os.path.join(folder, saveName) if folder else saveName
        HTML(string=html_replaced, base_url=os.getcwd()).write_pdf(target=target)

    except Exception as e:
        print("File could not be printed")
        print(str(e))

def write_offer(
    data={"default": "default"}, saveName="offerte.pdf", html="offerte.html",
):
    write(data=data, saveName=saveName, html=html)
