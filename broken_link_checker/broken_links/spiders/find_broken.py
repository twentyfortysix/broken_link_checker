import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.item import Item, Field
from urllib.parse import urlparse
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError

START_PAGE = "https://web.cz"

class MyItems(Item):
    referer = Field()  # where the link is extracted
    response = Field()  # URL that was requested
    status = Field()  # status code received
    link_url = Field()  # the link URL
    link_text = Field()  # the link text
    redirect_url = Field()  # the redirect URL
    link_img = Field()  # the image src if the link contains an image

def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    return urlparse(link.strip()).netloc == urlparse(START_PAGE).netloc


class broken_links(CrawlSpider):
    name = "linkchecker"
    target_domains = ["web.cz"]  # list of domains that will be allowed to be crawled
    start_urls = [START_PAGE]  # list of starting URLs for the crawler
    handle_httpstatus_list = [404, 410, 500]  # only 200 by default. you can add more status to list

    # Throttle crawl speed to prevent hitting site too hard
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,  # only 2 requests at the same time
        'DOWNLOAD_DELAY': 0.5  # delay between requests
    }

    rules = [
        Rule(
            LinkExtractor(allow_domains=target_domains, deny=('patternToBeExcluded'), unique=('Yes')),
            callback='parse_my_url',  # method that will be called for each request
            follow=True
        ),
        # crawl external links but don't follow them
        Rule(
            LinkExtractor(allow=(''), deny=("patternToBeExcluded"), unique=('Yes')),
            callback='parse_my_url',
            follow=False
        )
    ]

    def parse_my_url(self, response):
        if response.status in self.handle_httpstatus_list:  # if the response matches then creates a MyItem
            item = MyItems()
            item['referer'] = response.meta.get('referer', response.url)
            item['status'] = response.status
            item['link_url'] = response.request.url  # add the link URL to the item
            item['link_text'] = response.meta.get('link_text', '')  # add the link text to the item
            item['redirect_url'] = response.meta.get('redirect_urls', [None])[-1]  # add the redirect URL to the item
            item['link_img'] = response.meta.get('link_img', '')  # Use the 'link_img' from the referring page 
            yield item
        else:
            # Check if the content type is text/html
            content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
            if 'text/html' not in content_type:
                # Handle non-HTML content
                item = MyItems()
                item['referer'] = response.meta.get('referer', response.url)
                item['status'] = response.status
                item['link_url'] = response.url
                item['link_text'] = ''  # Set link_text to empty string
                item['redirect_url'] = response.meta.get('redirect_urls', [None])[-1]
                item['link_img'] = response.url  # add the non-HTML content URL to the link_img field
                yield item
                return

            # Follow all valid links within the domain
            for a in response.xpath('//a'):
                link_img = a.xpath('.//img/@src').get()
                if link_img:
                    link_text = ''
                else:
                    link_text = a.xpath('normalize-space(text())').get() or ''
                    link_img = ''

                link_url = response.urljoin(a.xpath('./@href').get())
                if not is_valid_url(link_url):
                    continue

                meta = {'link_text': link_text, 'link_img': link_img, 'referer': response.url}

                if follow_this_domain(link_url):
                    yield scrapy.Request(link_url, callback=self.parse_my_url, meta=meta, errback=self.handle_error)
                else:
                    yield scrapy.Request(link_url, callback=self.parse_external, meta=meta, errback=self.handle_error)

    def parse_external(self, response):
        if response.status in self.handle_httpstatus_list:
            item = MyItems()
            item["referer"] = response.meta.get('referer', response.url)
            item['status'] = response.status
            item['response'] = response.url
            item['link_url'] = response.request.url
            item['link_text'] = response.meta.get('link_text', '')
            item['redirect_url'] = response.meta.get('redirect_urls', [None])[-1]
            item['link_img'] = response.meta.get('link_img', '')  # Use the 'link_img' from the referring page 
            yield item

    def handle_error(self, failure):
        # log all failures
        request = failure.request
        item = MyItems()
        item["referer"] = request.meta.get('referer', request.url)
        if failure.check(DNSLookupError):
            item["status"] = 'DNSLookupError'
        elif failure.check(TimeoutError, TCPTimedOutError):
            item["status"] = 'TimeoutError'
        else:
            item["status"] = 'UnhandledError'
        item["response"] = request.url
        item["link_url"] = request.url
        item["link_text"] = request.meta.get('link_text', '')
        item['link_img'] = request.meta.get('link_img', '')  # Crucial: Use the 'link_img' from the referring page 
        yield item