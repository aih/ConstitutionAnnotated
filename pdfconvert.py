#python
# -*- coding: utf-8 -*-
from io import BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import re

from elasticsearch import Elasticsearch

es = Elasticsearch()


def convert(page, html=None):

    manager = PDFResourceManager()
    codec = 'utf-8'
    output = BytesIO()
    if(not html):
        converter = TextConverter(manager, output, codec=codec, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)
    else:
        converter = HTMLConverter(manager, output, codec=codec, showpageno=False, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)

    interpreter.process_page(page)
    pagetext = output.getvalue()
    converter.close()
    output.close
    return pagetext

pagePatterns = [b'(?:^.+\s{2,}([0-9IVXivx]+)\n+)', b'(?:^\s*([0-9IVXivx]+)\s+)',b'(?:\n{2,}([0-9IVXivx]+)\s*$)']
pp = re.compile('|'.join(pagePatterns))
def getPageNumber(text):
    try:
        pagenumber = pp.findall(text)
        pagenumber = reduce(None,filter(None,pagenumber[0]))
    except:
        pagenumber = '-1'
    return pagenumber

def savePage(pageindex, pagenumber, text, html):
    es.index(index="constitution", doc_type="page", body={"pageindex":pageindex, "pagenumber":pagenumber, "text":text, 'html':html})

def convertPages(fname, pages = None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    infile = file(fname, 'rb')
    print(fname)
    text = ''
    for pageindex, page in enumerate(PDFPage.get_pages(infile, pages)):
        text = convert(page)
        html = convert(page,'html')
        pagenumber = getPageNumber(text)
        savePage(pageindex, pagenumber, text, html)
        if(pagenumber == '-1'):
            print(text)

        print(pagenumber)
    infile.close()

