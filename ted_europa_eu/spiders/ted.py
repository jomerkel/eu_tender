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
            # if '545824-2018' != item['document_id']:
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
        text_1_7 = 'Total value of the procuremen'
        text_1_4 = 'Short description'
        desc_xpath = "//span[contains(text(), '{}')]//following-sibling::div".format(text_1_4)

        sections = response.css('div.grseq')

        sections_5 = []

        for section in sections:
            text = section.css('p::text').extract_first()
            if text and 'Section V: Award of' in text:
                sections_5.append(section)

        currency = ''
        total = response.xpath("//span[contains(text(), '{}')]//following-sibling::div/text()".format(text_1_7)).extract_first()

        if total:
            total = re.sub(r'\s|[a-zA-Z]|[:/\;!?]', '', total)

        short_description = ''
        for p in response.xpath(desc_xpath).xpath('string(.)').extract():
            short_description += p.strip()

        if sections_5:
            for section_5 in sections_5:
                new_item = TedEuropaEuItem()
                new_item.update(**item)
                if section_5:

                    name = section_5.xpath(".//span[text()='{}']/following-sibling::div/text()".format(text_2_3)).extract_first()
                    value = section_5.xpath(".//span[contains(text(),'{}')]/following-sibling::div/text()".format(text_2_4)).extract_first()

                    if not currency and value:
                        currency = value.split(' ')[-1]

                    if value:
                        value = re.sub(r'\s|[a-zA-Z]|[:/\;!?]', '', value)

                new_item['name'] = name
                new_item['value'] = value
                new_item['currency'] = currency
                new_item['total'] = total
                new_item['short_description'] = short_description.replace('\n', '') if short_description else ''
                new_item['contracting_country'] = item['country']
                # yield item
                request = scrapy.Request(response.url + '&tabId=3', callback=self.parse_data, dont_filter=True)
                request.meta['item'] = new_item
                yield request
        else:
            yield item

    def parse_data(self, response):
        item = response.meta['item']
        table = response.css('table.data')
        item['award_date'] = table.xpath(".//td[text()='Document sent']/following-sibling::td/text()").extract_first()
        item['contracting_authority'] = table.xpath(".//td[text()='Authority name']/following-sibling::td/text()").extract_first()
        product_type = table.xpath(".//td[text()='Contract']/following-sibling::td/text()").extract_first()

        if product_type:
            product_type = re.sub(r'\n|\s', '', product_type)

        item['product_type'] = product_type
        item['contracting_authority_city'] = table.xpath(".//td[text()='Place']/following-sibling::td/text()").extract_first()

        item['cpv_code'] = table.xpath(".//td[text()='CPV code']/following-sibling::td/text()").extract()
        yield item
