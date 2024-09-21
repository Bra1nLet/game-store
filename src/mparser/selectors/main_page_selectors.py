class MainPageSelectors:
    def __init__(self):
        self.all_games = r'div[class="psw-l-w-1/1"] li[class]'
        self.total_pages = r'div[class="psw-l-w-1/1"] li'
        self.link_to_game = "a[href]"
        self.img_url = "img:not([aria-hidden])"
        self.name= r'span[data-qa~="ems-sdk-grid#productTile%#product-name"]'

main_page_selectors = MainPageSelectors()
