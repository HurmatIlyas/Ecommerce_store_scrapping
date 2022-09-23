import scrapy
import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from webscrapper.items import WebscrapperItem


class MinistryOfSupplyParseSpider:
    def parse(self, response):
        item = WebscrapperItem() 
        raw_products = self.parse_raw_product(response)
        color = self.product_color(response)

        item['brand'] = self.product_brand(raw_products)
        item['care'] = self.product_care(response)
        item['category'] = self.product_category(response)
        item['currency'] = self.product_currency(raw_products)
        item['description'] = self.product_description(raw_products)
        item['gender'] = self.product_gender(response)
        item['image_urls'] = self.product_image_urls(response, color)
        item['lang'] = self.product_language(response)
        item['name'] = self.product_name(response)
        item['price'] = self.product_price(response)
        item['retailer_sku'] = self.product_retailer_sku(raw_products)
        item['skus'] = self.product_skus(response, item['name'], item['price'], color)
        item['url'] = self.product_url(response)
        item['url_original'] = self.product_original_url(response)
        item['trail'] = self.product_trail(response)

        yield item

    def parse_raw_product(self, response):
        raw_products_details =response.css('script[vmid="richSnippet"]::text').get()
        raw_products = json.loads(raw_products_details)
            
        return raw_products

    def product_brand(self, raw_products):
        return raw_products['brand']['name']

    def product_care(self, response):
        return [i.strip() for i in response.css('div.AccordionGroup__text-block  ::text').getall()]

    def product_category(self, response):
        return [i.strip() for i in response.css('a.Breadcrumb__link span::text').getall()]

    def product_currency(self, raw_products):
        return raw_products['offers']['priceCurrency']

    def product_description(self, raw_products):
        return raw_products['description'].replace('\n', '').encode("ascii", "ignore").decode()

    def product_retailer_sku(self, raw_products):
        return raw_products['sku']

    def product_gender(self, response):
        return response.css('span.Breadcrumb__linkText::text').get().strip()

    def product_name(self, response):
        name = response.css('h1.ProductMetaHeader__heading::text').get().strip()
        return name
    
    def product_language(self,response):
        return response.css('html::attr(lang)').get()

    def product_price(self, response):
        price = response.css('span.BasePrice__integer::text').get()
        return price

    def product_color(self, response):
        color = response.css('span.CardProduct__title::text').get()
        return color

    def product_image_urls(self, response, color):
        return {color: response.css('img.ProductPage__carousel-image::attr(src)').getall()}

    def product_skus(self, response, name, price, color):
        size = response.css('select[id="Size"] option::text').getall()
        size = [i.strip() for i in size]
        splitted_sizes = [i.split("-") for i in size]

        for i in splitted_sizes:
            if len(i) > 1:
                availability = True
            else:
                availability = False    

        return {color + "_" + i: {"color": color,
                                      "name": name,
                                      "out_of_stock": availability,
                                      "price": price, 
                                      "size": i} for i in size}

    def product_url(self,response):
        return response.css('link[rel="canonical"]::attr(href)').get()
    
    def product_original_url(self, response):
        return response.url

    def product_trail(self, response):
        return [response.request.headers.get('Referer', None).decode()]


class MinistryOfSupplyCrawlSpider(CrawlSpider):
    name = 'ministryofsupply_spider' 
    allowed_domains = ['ministryofsupply.com']
    start_urls = ['https://www.ministryofsupply.com/all/shop-all']  
    ministryofsupply_parse_spider = MinistryOfSupplyParseSpider()
    rules = (
        Rule(LinkExtractor(restrict_css = 'a.CardProduct__link'), callback= ministryofsupply_parse_spider.parse),)
