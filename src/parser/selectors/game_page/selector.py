from src.parser.selectors.game_page.tags import game_page_tags


class GamePageSelectors:
    def __init__(self):
        self.editions = "div.psw-root.psw-dark-theme div.psw-c-bg-0[data-qa~=mfeUpsell] article"
        self.edition_name = "h3.psw-t-title-s.psw-t-align-c.psw-fill-x.psw-p-t-6.psw-p-x-7"
        self.edition_price = "span.psw-t-title-m"
        self.edition_platforms = "div.psw-l-space-x-2.psw-l-line-center.psw-p-t-5"
        self.edition_detail = "ul.psw-t-list.psw-l-columns.psw-l-compact.psw-m-sub-b-1 li.psw-m-b-1"
        self.edition_picture = "span.psw-media-frame.psw-fill-x.psw-aspect-16-9[data-qa='']"

        self.buy_btn = '.psw-l-stack-bottom.psw-game-background-image-hero-h-min.psw-m-sub-t-9\@below-tablet-s.psw-m-t-9 div.psw-l-line-left.psw-hidden span.psw-fill-x.psw-t-truncate-1.psw-l-space-x-2 '

        self.age_limit = "img.psw-fade-in.psw-center.psw-l-fit-fill[alt]"
        self.rating = "span.psw-p-r-1.psw-t-title-l span[aria-hidden~=true]"

        self.game_details = "dl.psw-l-grid.psw-fill-x.psw-m-y-0"
        self.game_details_labels = self.game_details + " dt"
        self.game_details_information = self.game_details + " dd"


game_page_selectors = GamePageSelectors()
