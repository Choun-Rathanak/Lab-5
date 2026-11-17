import hashlib, re, scrapy

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, max_pages=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max(1, int(max_pages))
        self.pages_seen = 0

    def parse(self, response):
        self.pages_seen += 1

        # TODO: for each card, yield response.follow(href, callback=self.parse_book)
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, callback=self.parse_book)

        # TODO: if pages_seen < max_pages, follow li.next a
        next_page = response.css("li.next a::attr(href)").get()
        if next_page and self.pages_seen < self.max_pages:
            yield response.follow(next_page, callback=self.parse)

    # TODO: extract full detail fields, clean missing values
    def parse_book(self, response):
        def clean(values, default=None):
            value = " ".join(part.strip() for part in values if part.strip())
            return value or default

        title = clean(response.css("div.product_main h1::text").getall(), "")

        description = clean(
            response.css("#product_description + p::text").getall(), ""
        )

        category = clean(response.css(
            "ul.breadcrumb li:nth-child(3) a::text"
        ).getall())

        price_text = response.css("p.price_color::text").get("")
        price_match = re.search(r"[\d.]+", price_text)
        price_gbp = float(price_match.group()) if price_match else None

        rating_class = response.css("p.star-rating::attr(class)").get("")
        rating_word = rating_class.split()[-1] if rating_class else None
        rating = RATINGS.get(rating_word)

        availability = clean(
            response.css("p.instock.availability::text").getall(), ""
        )

        doc_id = hashlib.sha1(
            response.url.encode("utf-8")
        ).hexdigest()[:12]

        # TODO: yield an IR-ready dict (see field list above)
        yield {
            "doc_id": doc_id,
            "title": title,
            "text": f"{title} {description}".strip(),
            "description": description,
            "url": response.url,
            "category": category,
            "price_gbp": price_gbp,
            "rating": rating,
            "availability": availability,
            "source": "books.toscrape.com",
        }
