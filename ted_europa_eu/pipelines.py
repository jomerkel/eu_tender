from datetime import datetime

from scrapy import signals
from scrapy.exporters import CsvItemExporter


class TedEuropaEuPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.duplicates = []

        time = datetime.now().strftime('%Y%m%d')
        self.file = open('{}_TED_Search_Result.csv'.format(time), 'wb')
        self.file_details = open('{}_TED_Details_Result.csv'.format(time), 'wb')
        self.file_cpv_codes = open('{}_TED_Details_CPV.csv'.format(time), 'wb')
        self.file_data = open('{}_TED_Data.csv'.format(time), 'wb')

        self.exporter = CsvItemExporter(self.file)
        self.details_exporter = CsvItemExporter(self.file_details)
        self.cpv_exporter = CsvItemExporter(self.file_cpv_codes)
        self.data_exporter = CsvItemExporter(self.file_data)

        self.exporter.fields_to_export = [
            'document_id', 'description', 'short_description',
            'country', 'publication_date', 'deadline']
        self.details_exporter.fields_to_export = [
            'url', 'document_id', 'name', 'value', 'lot_no', 'total', 'currency',
            'contracting_country', 'award_date', 'product_type', 'contracting_authority',
            'contracting_authority_city']

        self.data_exporter.fields_to_export = [
            'url', 'document_id', 'TI', 'ND', 'PD', 'OJ', 'TW', 'AU', 'OL', 'HD', 'CY',
            'AA', 'HA', 'DS', 'NC', 'PR', 'TD', 'RP', 'TY', 'AC', 'PC', 'RC', 'IA', 'DI']

        self.exporter.start_exporting()
        self.details_exporter.start_exporting()
        self.cpv_exporter.start_exporting()
        self.data_exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

        self.details_exporter.finish_exporting()
        self.file_details.close()

        self.cpv_exporter.finish_exporting()
        self.file_cpv_codes.close()

        self.data_exporter.finish_exporting()
        self.file_data.close()

    def process_item(self, item, spider):
        if item['document_id'] not in self.duplicates:
            self.exporter.export_item(item)
            self.duplicates.append(item['document_id'])

            if 'cpv_code' in item and item['cpv_code']:
                for code in item['cpv_code']:
                    self.cpv_exporter.export_item({'document_id': item['document_id'], 'cpv_code': code})

        self.details_exporter.export_item(item)
        self.data_exporter.export_item(item)
        return item
