# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals


class TetEuropaEuSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class TetEuropaEuDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


from scrapy.exceptions import NotConfigured
from scrapy.utils.misc import arg_to_iter
import itertools
import base64
from six.moves.urllib.parse import unquote

try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy
from six.moves.urllib.parse import urlunparse


class SimpleProxymeshMiddleware(object):
    def __init__(self, settings):
        if not settings.getbool('PROXYMESH_ENABLED', True):
            raise NotConfigured
        self.proxies = itertools.cycle(arg_to_iter(settings.get('PROXYMESH_URL', 'http://us-il.proxymesh.com:31280')))
        self.timeout = settings.getint('PROXYMESH_TIMEOUT', 0)

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        return o

    def _get_proxy(self, url):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse((proxy_type, hostport, '', '', '', ''))

        if user and password:
            user_pass = '%s:%s' % (unquote(user), unquote(password))
            creds = base64.b64encode(user_pass.encode('utf-8')).strip()
        else:
            creds = None

        return creds, proxy_url

    def process_request(self, request, spider):
        if not request.meta.get('bypass_proxy', False) and request.meta.get('proxy') is None:
            creds, proxy = self._get_proxy(next(self.proxies))
            request.meta['proxy'] = proxy
            if creds:
                request.headers['Proxy-Authorization'] = b'Basic ' + creds
            if self.timeout and not request.headers.get('X-ProxyMesh-Timeout'):
                request.headers.update({'X-ProxyMesh-Timeout': self.timeout})
