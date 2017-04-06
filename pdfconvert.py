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

from monkeylearn import MonkeyLearn
ml = MonkeyLearn('29499a676f605f72793d2290f5bdd8e6ac4d0868')
module_id = 'ex_y7BPYzNG'
def getKeywords(textList):
    text_list = textList
    res = ml.extractors.extract(module_id, text_list)
    return res.result

def setAllTerms(maxTerms=5):
    numdocs = es.count(index=INDEX, doc_type=DOCTYPE)['count']
    print(numdocs)
    for pageindex in range(numdocs):
        resp = es.search(index=INDEX, doc_type=DOCTYPE, body={"query": {"match":{"pageindex":pageindex}}})
        doc = resp['hits']['hits'][0]
        docID=doc['_id']
        #termvector = es.termvector(index=INDEX, doc_type=DOCTYPE, id=docID, body={"fields":["text"],"offsets":"false","positions":"false","term_statistics":"true","field_statistics":"true"})
        try:
            #terms = termvector['term_vectors']['text']['terms']
            keywords = getKeywords([doc['_source']['text']])
            bestTerms = [[keyword['keyword'],float(keyword['relevance'])] for keyword in keywords]
            es.update(index=INDEX, doc_type=DOCTYPE, id=docID, body={"doc": {"keywords":bestTerms}})
            print(pageindex)
            print(keywords)
            print(bestTerms)
        except:
            pass

def setAllTermsBatch(start=0,batch=200):
    numdocs = es.count(index=INDEX, doc_type=DOCTYPE)['count']
    print(numdocs)
    for pageindex in range(start,numdocs,batch):
        resp = es.search(index=INDEX, doc_type=DOCTYPE, size=batch, body={"query": {"range":{"pageindex": {"gte" : pageindex,"lt" : pageindex+batch}}}})
        docBatch = resp['hits']['hits']
        textBatch = [doc['_source']['text'] for doc in docBatch]
        print(len(textBatch))
        keywordBatch = getKeywords(textBatch)
        print(keywordBatch)
        print(len(keywordBatch))
        for index, keywords in enumerate(keywordBatch):
            bestTerms = [[keyword['keyword'],float(keyword['relevance'])] for keyword in keywords]
            doc =  docBatch[index]
            docID=doc['_id']
            print(doc['_source']['pageindex'])
            es.update(index=INDEX, doc_type=DOCTYPE, id=docID, body={"doc": {"keywords":bestTerms}})


#Split pdf into one page pdfs
from pyPdf import PdfFileWriter, PdfFileReader

def makeOnePagersOld(filename='GPO-CONAN-REV-2014.pdf' ,path='pdf/'):
    infile = PdfFileReader(open(filename, 'rb'))
    print(infile.getNumPages())
    for i in range(infile.getNumPages()):
        p = infile.getPage(i)
        outfile = PdfFileWriter()
        outfile.addPage(p)
        outputStream = file(path+'pageindex-%02d.pdf' % i, 'wb')
        outfile.write(outputStream)
        outputStream.close()

def makeOnePagersOld2(filename='GPO-CONAN-REV-2014.pdf' ,path='pdf/'):
    infile = file(filename, 'rb')
    for i, page in enumerate(PDFPage.get_pages(infile)):
        with open(path+'pageindex-%0s.pdf' % str(i), 'wb') as f:
            print(i)
            f.write(page.contents[0])

#Split pdf into one page pdfs
from pdfrw import PdfWriter, PdfReader

def makeOnePagers(filename='GPO-CONAN-REV-2014.pdf' ,path='pdf/'):
    infile = PdfReader(filename)
    pages = len(infile.pages)
    print(pages)
    for i in range(pages):
       p = infile.pages[i]
       if(p and len(p)>0):
           outfile = PdfWriter()
           outfile.addPage(p)
           try:
               outfile.write('pdf/pageindex-%s.pdf' % str(i))
           except:
               pass
           print(i)
