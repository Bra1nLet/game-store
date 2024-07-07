from src.parser.selectors.main_page.tags import main_page_tags


class MainPageSelector:
    def __init__(self):
        self.store = 'button#menu-button-primary--msg-store'
        self.ps5_btn = '#link-link-list--msg-store-0'
        self.ps4_btn = '#link-link-list--msg-store-1'
        self.games = 'a.psw-link.psw-content-link'
        self.page_number = 'button.psw-button.psw-b-0.psw-page-button.psw-p-x-3.psw-r-pill.psw-l-line-center.psw-l-inline.psw-t-size-3.psw-t-align-c'
        self.next_page = 'span.psw-icon.psw-icon--chevron-right.psw-icon.psw-icon-size-2.psw-icon--chevron-right'

        self.game_image_url = 'img.psw-fade-in.psw-top-left.psw-l-fit-cover'
        self.game_name = 'span.psw-t-body.psw-c-t-1.psw-t-truncate-2.psw-m-b-2'
        self.game_price = '.psw-m-r-3'

        self.data = {
            main_page_tags.ps5_btn: self.ps5_btn,
            main_page_tags.ps4_btn: self.ps4_btn,
            main_page_tags.store: self.store,
            main_page_tags.games: self.games,
            main_page_tags.next_page: self.next_page,
            main_page_tags.page_number: self.page_number,
            main_page_tags.game_image_url: self.game_image_url,
            main_page_tags.game_name: self.game_name,
            main_page_tags.game_price: self.game_price
        }

    def get_selector_by_tag(self, tag):
        return self.data[tag]


main_page_selector = MainPageSelector()
