class GamePageSelectors:
    def __init__(self):
        self.price_containers = """div[class="pdp-cta"] label[class="psw-label psw-l-inline psw-l-line-left psw-interactive psw-c-bg-0 psw-l-anchor psw-fill-x"]"""
        self.price = "span.psw-t-title-m"
        self.price_without_discount = 'span.psw-t-title-s.psw-c-t-2.psw-t-strike'
        self.price_discount_percentage = 'span.psw-m-r-3'
        self.discount_ends = r'span.psw-t-overline.psw-t-bold.psw-l-line-left.psw-fill-x span.psw-c-t-2'
        self.rating = r'span[data-qa~="mfe-star-rating#overall-rating#average-rating"]'
        self.details_index = "dl dt"
        self.details_value = "dl dd"

        self.editions = "div.psw-l-grid article"

        self.editions_name = "h3.psw-t-title-s.psw-t-align-c.psw-fill-x.psw-p-t-6.psw-p-x-7"
        self.editions_price = "span.psw-t-title-m"
        self.editions_discount_percentage = "span.psw-m-r-3"
        self.editions_discount_ends = "span.psw-t-overline.psw-t-bold.psw-l-line-left.psw-fill-x span.psw-c-t-2"
        self.editions_platforms = "span.psw-p-x-2.psw-p-y-1.psw-t-tag"
        self.editions_details = "ul li"
        self.editions_picture = "span.psw-media-frame.psw-fill-x.psw-aspect-16-9"

game_page_selectors = GamePageSelectors()