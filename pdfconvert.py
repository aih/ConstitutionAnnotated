#python
# -*- coding: utf-8 -*-
from __future__ import division
from io import BytesIO
import re
import operator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from elasticsearch import Elasticsearch
es = Elasticsearch()

INDEX = 'constitution'
DOCTYPE = 'page'

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
    es.index(index=INDEX, doc_type=DOCTYPE, body={"pageindex":pageindex, "pagenumber":pagenumber, "text":text, 'html':html, 'keywords':[]})

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

def getBestTerms(terms,maxTerms=5):
    termScores={term:terms[term]['doc_freq']/terms[term]['ttf'] for term in terms if len(term)>3 and (not term.isdigit()) and terms[term]['doc_freq']>1 and terms[term]['doc_freq']/terms[term]['ttf']<1}
    sortedTerms = sorted(termScores.items(), key=operator.itemgetter(1), reverse=True)
    return sortedTerms[0:maxTerms]



def setAllTerms(maxTerms=5):
    numdocs = es.count(index=INDEX, doc_type=DOCTYPE)['count']
    for pageindex in range(numdocs):
        doc = es.search(index=INDEX, doc_type=DOCTYPE, body={"query": {"match":{"pageindex":pageindex}}})
        docID=doc['hits']['hits'][0]['_id']
        termvector = es.termvector(index=INDEX, doc_type=DOCTYPE, id=docID, body={"fields":["text"],"offsets":"false","positions":"false","term_statistics":"true","field_statistics":"true"})
        try:
            terms = termvector['term_vectors']['text']['terms']
            bestTerms = getBestTerms(terms, maxTerms)
            print(pageindex)
            print(bestTerms)
            es.update(index=INDEX, doc_type=DOCTYPE, id=docID, body={"doc": {"keywords":bestTerms}})
        except:
            pass



