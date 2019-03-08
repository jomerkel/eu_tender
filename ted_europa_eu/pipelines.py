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
        self.file = open('search_result_{}.csv'.format(spider.name), 'wb')
        self.file_details = open('details_result_{}.csv'.format(spider.name), 'wb')

        self.exporter = CsvItemExporter(self.file)
        self.details_exporter = CsvItemExporter(self.file_details)

        self.exporter.fields_to_export = [
            'document_id', 'description', 'short_description',
            'country', 'publication_date', 'deadline']
        self.details_exporter.fields_to_export = [
            'url', 'document_id', 'name', 'value', 'total', 'currency',
            'contracting_country', 'award_date', 'product_type', 'contracting_authority',
            'contracting_authority_city']

        self.exporter.start_exporting()
        self.details_exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

        self.details_exporter.finish_exporting()
        self.file_details.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        self.details_exporter.export_item(item)
        return item
