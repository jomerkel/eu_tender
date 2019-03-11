# eu_tender

**can be run with parameters, parameter name and default value you can see below:**
* cpvCodeList = '72000000,35000000,32000000,63000000,73000000,48000000'
* documentTypeList = "'Results of design contests','Contract notice','Contract award notice','Voluntary ex ante transparency notice','Concession award notice'"
* freeText = 'Nokia'


usage example:
```bash
scrapy crawl ted -a documentTypeList=""Results of design contests,Contract notice,Contract award notice,Voluntary ex ante transparency notice,Concession award notice"
```