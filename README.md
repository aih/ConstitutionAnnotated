# ConstitutionAnnotated
Search data for Constitution Annotated

[Demo](http://ca.linkedlegislation.com)

## Quick Start (development)
1. Clone this repository
2. Initialize the UI submodule in elasticsearch-gui:
`git submodule update --init`

3. [Install Elasticsearch 1.x](https://www.elastic.co/guide/en/elasticsearch/reference/1.7/_installation.html). Later versions will not work with the data dump format or the UI. These can be updated with moderate effort (a day or two), by changing the index mapping syntax and re-indexing the pdfs.

2. Add CORS support by adding the following lines to config/elasticsearch.yml:
```
http.cors.enabled: true
http.cors.allow-origin: "*"
```

3. Start Elasticsearch: `$./bin/elasticsearch`
4. Install [elasticdump](https://github.com/taskrabbit/elasticsearch-dump)
5. Load the constitutionmapping.json mapping to your local ES instance:
```
elasticdump --input=./constitutionsearchmap.json --type=mapping --output=http://localhost:9200/constitution
```
5. Load the search data to your local ES instance:
```
elasticdump --input=./constitutionsearch.json --type=data --output=http://localhost:9200/constitution
```
6. Serve elasticsearch-gui from a static local server (e.g. for Python, `python -m SimpleHTTPServer 8000`)

7. Navigate to /index.html

8. See ConstitionAnnotatedScreenshot.png for a preview of the search UI.
In production, ES may be served through a proxy server to the /elasticproxy url on your server. On Linux, you can use the sample nginx.conf to serve ES as a proxy.

