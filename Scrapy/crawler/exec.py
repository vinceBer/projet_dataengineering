from scrapy.crawler import CrawlerProcess
from fichier_scrapping import OpenPowerliftingSpider
process = CrawlerProcess()
process.crawl(OpenPowerliftingSpider)
process.start()