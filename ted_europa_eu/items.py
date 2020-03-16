import scrapy


class TedEuropaEuItem(scrapy.Item):
    document_id = scrapy.Field()
    description = scrapy.Field()
    country = scrapy.Field()
    publication_date = scrapy.Field()
    deadline = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    value = scrapy.Field()
    currency = scrapy.Field()
    total = scrapy.Field()
    short_description = scrapy.Field()
    contracting_country = scrapy.Field()
    award_date = scrapy.Field()
    contracting_authority = scrapy.Field()
    product_type = scrapy.Field()
    contracting_authority_city = scrapy.Field()
    cpv_code = scrapy.Field()
    lot_no = scrapy.Field()
