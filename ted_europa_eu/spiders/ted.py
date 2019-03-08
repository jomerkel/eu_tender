# -*- coding: utf-8 -*-
import scrapy
import re

from ted_europa_eu.items import TedEuropaEuItem


class TedSpider(scrapy.Spider):
    name = 'ted'
    allowed_domains = ['ted.europa.eu']
    start_urls = ['http://ted.europa.eu/']

    def start_requests(self):
        yield scrapy.FormRequest(
            url='https://ted.europa.eu/TED/search/search.do',
            callback=self.start_requests2,
            dont_filter=True)

    def start_requests2(self, response):

        data = [
            ('action', 'search'),
            ('lgId', 'en'),
            ('Rs.gp.8686990.pid', 'secured'),
            ('Rs.gp.8686991.pid', 'secured'),
            ('searchCriteria.searchScope', 'ARCHIVE'),
            ('searchCriteria.freeText', 'Nokia'),
            ('Rs.pick.857511.refDataId', 'COUNTRY'),
            ('searchCriteria.documentTypeList', "'Results of design contests','Contract notice','Contract award notice','Voluntary ex ante transparency notice','Concession award notice'"),
            ('Rs.pick.857512.refDataId', 'DOCUMENT_TYPE'),
            ('Rs.pick.857513.refDataId', 'CONTRACT'),
            ('searchCriteria.publicationDateChoice', 'DEFINITE_PUBLICATION_DATE'),
            ('searchCriteria.cpvCodeList', '72000000,35000000,32000000,63000000,73000000,48000000'),
            ('Rs.pick.857514.refDataId', 'CPV_CODE'),
            ('Rs.pick.857515.refDataId', 'NUTS_CODE'),
            ('Rs.pick.857516.refDataId', 'MAIN_ACTIVITY'),
            ('Rs.pick.857517.refDataId', 'REGULATION'),
            ('Rs.pick.857518.refDataId', 'PROCEDURE'),
            ('Rs.pick.857519.refDataId', 'DIRECTIVE'),
            ('Rs.pick.857520.refDataId', 'TYPE_OF_AUTHORITY'),
            ('Rs.pick.857521.refDataId', 'HEADING_A'),
            ('_searchCriteria.statisticsMode', 'on'),
        ]

        yield scrapy.FormRequest(
            url='https://ted.europa.eu/TED/search/search.do',
            formdata=data,
            callback=self.parse)

    def parse(self, response):
        for row in response.css('table#notice > tbody > tr'):
            item = TedEuropaEuItem()
            tds = row.css('td')

            detail_url = 'https://ted.europa.eu' + row.css('a::attr(href)').extract_first()
            item['url'] = detail_url
            item['document_id'] = row.css('a::text').extract_first()
            # if '490757-2018' != item['document_id']:
            #     continue
            item['description'] = tds[2].css('::text').extract_first()
            item['country'] = tds[3].css('::text').extract_first()
            item['publication_date'] = tds[4].css('::text').extract_first()
            item['deadline'] = tds[5].css('::text').extract_first()
            request = scrapy.Request(detail_url, callback=self.parse_details, dont_filter=True)
            request.meta['item'] = item
            yield request

        next_page = response.css('a.pagenext-link::attr(href)')
        if next_page:
            next_page = 'https://ted.europa.eu/TED/search/' + next_page.extract_first()
            yield response.follow(url=next_page, callback=self.parse)

    def parse_details(self, response):
        item = response.meta['item']
        text_2_3 = 'Name and address of the contractor'
        text_2_4 = 'Information on value of the contract/lot (excluding VAT)'

        sections = response.css('div.grseq')

        sections_5 = []

        for section in sections:
            text = section.css('p::text').extract_first()
            if text and 'Section V: Award of' in text:
                sections_5.append(section)

        names = []
        values = []
        for section_5 in sections_5:
            if section_5:

                name = section_5.xpath(".//span[text()='{}']/following-sibling::div/text()".format(text_2_3)).extract_first()
                value = section_5.xpath(".//span[contains(text(),'{}')]/following-sibling::div/text()".format(text_2_4)).extract_first()
                print(section_5.css('div.txtmark::text').extract_first())
                print('name {} value {}'.format(name, value))
                if value:
                    value = re.sub(r'\s|[a-zA-Z]|[:/\;!?]', '', value)

                if name:
                    names.append(name)

                if value:
                    values.append(value)

        item['name'] = ';'.join(names)
        item['value'] = ';'.join(values)
        return item

