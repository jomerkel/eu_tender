# -*- coding: utf-8 -*-
import scrapy
import re

from ted_europa_eu.items import TedEuropaEuItem


class NewTedSpider(scrapy.Spider):
    name = 'new_ted'
    allowed_domains = ['ted.europa.eu']
    start_urls = ['http://ted.europa.eu/']

    custom_settings = {
        'DOWNLOAD_DELAY': 3
    }

    def start_requests(self):
        yield scrapy.FormRequest(
            url='https://ted.europa.eu/TED/search/search.do',
            callback=self.search,
            dont_filter=True
        )

    def search(self, response):
        data = {
            '$parameterType': 'cclQuery',
            'value': self.settings['SEARCH_QUERY']
        }

        yield scrapy.FormRequest(
                url='https://ted.europa.eu/TED/search/queryExtractor.do',
                formdata=data,
                callback=self.query_extractor
            )

    def query_extractor(self, response):
        data = {
                'action': 'search',
                'lgId': 'en',
                'quickSearchCriteria': '',
                'expertSearchCriteria.searchScope': 'ARCHIVE',
                'expertSearchCriteria.query': self.settings['SEARCH_QUERY'],
                '_expertSearchCriteria.statisticsMode': 'on'
            }
        yield scrapy.FormRequest(
                url='https://ted.europa.eu/TED/search/expertSearch.do',
                formdata=data,
                callback=self.expert_search
            )

    def expert_search(self, response):
        yield scrapy.Request(
                url='https://ted.europa.eu/TED/search/searchResult.do',
                dont_filter=True,
                callback=self.parse
            )

    def parse(self, response):
        rows = response.css('table#notice tr')
        for r in rows[1:]:
            item = TedEuropaEuItem()
            tds = r.css('td')

            detail_url = 'https://ted.europa.eu' + r.css('a::attr(href)').extract_first()
            item['url'] = detail_url
            item['document_id'] = r.css('a::text').extract_first().strip()
            item['description'] = tds[2].css('::text').extract_first().strip()
            item['country'] = tds[3].css('::text').extract_first().strip()
            item['publication_date'] = tds[4].css('::text').extract_first().strip()
            item['deadline'] = tds[5].css('::text').extract_first().strip()

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

        text_2_2_1 = 'Number of tenders received:'
        text_2_2_2 = 'Number of tenders received from SMEs'
        text_2_2_3 = 'Number of tenders received from tenderers from other EU Member States'
        text_2_2_4 = 'Number of tenders received from tenderers from non-EU Member States'
        text_2_2_5 = 'Number of tenders received by electronic means'
        text_2_2_6 = 'The contract has been awarded to a group of economic operators'
        xpath_2_2 = ".//div[contains(text(), '{}')]/text()"

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
                    lot_no = section_5.xpath(".//b[contains(text(),'Lot No')]/parent::div/text()").extract()
                    lot_no = ' '.join(lot_no) if lot_no else lot_no
                    lot_no = re.sub(r'\D', '', lot_no) if lot_no else lot_no

                    if not currency and value:
                        currency = value.split(' ')[-1]

                    if value:
                        value = re.sub(r'\s|[a-zA-Z]|[:/\;!?]', '', value)

                new_item['name'] = name.split(':')[-1] if name and ':' in name else name
                new_item['lot_no'] = lot_no
                new_item['value'] = value
                new_item['currency'] = currency
                new_item['total'] = total
                new_item['short_description'] = short_description.replace('\n', '') if short_description else ''
                new_item['contracting_country'] = item['country']

                NrTendersRecieved = section_5.xpath(xpath_2_2.format(text_2_2_1)).extract_first()
                NrTendersRecievedSME = section_5.xpath(xpath_2_2.format(text_2_2_2)).extract_first()
                NrTendersRecievedoEU = section_5.xpath(xpath_2_2.format(text_2_2_3)).extract_first()
                NrTendersRecievednonEU = section_5.xpath(xpath_2_2.format(text_2_2_4)).extract_first()
                NrTendersRecievedelectronic = section_5.xpath(xpath_2_2.format(text_2_2_5)).extract_first()
                Consortium = section_5.xpath(xpath_2_2.format(text_2_2_6)).extract_first()

                new_item['NrTendersRecieved'] = NrTendersRecieved.split(':')[-1] if NrTendersRecieved else None
                new_item['NrTendersRecievedSME'] = NrTendersRecievedSME.split(':')[-1] if NrTendersRecievedSME else None
                new_item['NrTendersRecievedoEU'] = NrTendersRecievedoEU.split(':')[-1] if NrTendersRecievedoEU else None
                new_item['NrTendersRecievednonEU'] = NrTendersRecievednonEU.split(':')[-1] if NrTendersRecievednonEU else None
                new_item['NrTendersRecievedelectronic'] = NrTendersRecievedelectronic.split(':')[-1] if NrTendersRecievedelectronic else None
                new_item['Consortium'] = Consortium.split(':')[-1] if Consortium else None

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
        item['TI'] = self.get_data_from_table(table, 'TI')
        item['ND'] = self.get_data_from_table(table, 'ND')
        item['PD'] = self.get_data_from_table(table, 'PD')
        item['OJ'] = self.get_data_from_table(table, 'OJ')
        item['TW'] = self.get_data_from_table(table, 'TW')
        item['AU'] = self.get_data_from_table(table, 'AU')
        item['OL'] = self.get_data_from_table(table, 'OL')
        item['HD'] = self.get_data_from_table(table, 'HD')
        item['CY'] = self.get_data_from_table(table, 'CY')
        item['AA'] = self.get_data_from_table(table, 'AA')
        item['HA'] = self.get_data_from_table(table, 'HA')
        item['DS'] = self.get_data_from_table(table, 'DS')
        item['NC'] = self.get_data_from_table(table, 'NC')
        item['PR'] = self.get_data_from_table(table, 'PR')
        item['TD'] = self.get_data_from_table(table, 'TD')
        item['RP'] = self.get_data_from_table(table, 'RP')
        item['TY'] = self.get_data_from_table(table, 'TY')
        item['AC'] = self.get_data_from_table(table, 'AC')
        item['PC'] = self.get_data_from_table(table, 'PC')
        item['RC'] = self.get_data_from_table(table, 'RC')
        item['IA'] = self.get_data_from_table(table, 'IA')
        item['DI'] = self.get_data_from_table(table, 'DI')
        yield item

    def get_data_from_table(self, table, key):
        value = table.xpath(".//tr//th[text()='{}']/following-sibling::td[2]/text()".format(key)).extract_first()
        if value:
            value = re.sub(r'\n|\r|\t', '', value)
            return value.strip()
        return value
