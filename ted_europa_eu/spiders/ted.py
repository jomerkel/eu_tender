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
            ('chk', '72000000'),
            ('chk', '35000000'),
            ('chk', '32000000'),
            ('chk', '63000000'),
            ('chk', '73000000'),
            ('chk', '48000000'),
            ('action', 'search'),
            ('lgId', 'en'),
            ('Rs.gp.8686990.pid', 'secured'),
            ('Rs.gp.8686991.pid', 'secured'),
            ('searchCriteria.searchScope', 'ARCHIVE'),
            ('searchCriteria.freeText', '\u2018Nokia\u2019'),
            ('Rs.pick.857511.refDataId', 'COUNTRY'),
            ('searchCriteria.documentTypeList', '\'Results of design contests\',\'Contract notice\',\'Contract award notice\',\'Voluntary ex ante transparency notice\',\'Concession award notice\''),
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

        sections_5 = response.css('div.grseq')
        section_5 = None

        for section in sections_5:
            text = section.css('p::text').extract_first()
            if text and 'Section V: Award of' in text:
                section_5 = section
                break

        if section_5:
            name = section_5.xpath("//span[text()='{}']/following-sibling::div/text()".format(text_2_3)).extract_first()
            value = section_5.xpath("//span[contains(text(),'{}')]/following-sibling::div/text()".format(text_2_4)).extract_first()
            if value:
                value = re.sub(r'\s|[a-zA-Z]|[:/\;!?]', '', value)

            item['name'] = name
            item['value'] = value
            return item
        else:
            item['name'] = None
            item['value'] = None
            return item

