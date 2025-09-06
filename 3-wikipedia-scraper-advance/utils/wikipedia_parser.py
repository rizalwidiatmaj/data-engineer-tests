from html.parser import HTMLParser


class WikipediaArticleParser(HTMLParser):
    """
    WikipediaArticleParser is a custom HTMLParser for extracting structured data from Wikipedia article HTML.
    Attributes:
        is_parsing_metadata (bool): Indicates if the parser is currently inside a metadata <script> tag.
        article_metadata (list): Stores metadata content extracted from <script type="application/ld+json"> tags.
        is_parsing_content (bool): Indicates if the parser is currently inside the main article content.
        article_content (list): Stores the main textual content of the article, extracted from <p>, <ul>, and heading <div> tags within the body.
        is_inside_body (bool): Tracks whether the parser is inside the main body content <div class="mw-body-content">.
        article_categories (list): Stores the categories associated with the article, extracted from the category links section.
        is_parsing_category (bool): Indicates if the parser is currently inside the category links section.
    Methods:
        handle_starttag(tag, attrs): Handles the start of HTML tags, updating parsing state based on tag type and attributes.
        handle_endtag(tag): Handles the end of HTML tags, updating parsing state accordingly.
        handle_data(data): Handles the textual data within tags, appending relevant content to the appropriate attribute lists.
    """
    def __init__(self):
        super().__init__()
        self.is_parsing_metadata = False
        self.article_metadata = []
        self.is_parsing_content = False
        self.article_content = []
        self.is_inside_body = False
        self.article_categories = []
        self.is_parsing_category = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == 'script':
            if attrs.get('type') == "application/ld+json":
                self.is_parsing_metadata = True
        if tag.lower() == 'div' and 'class' in attrs:
            if attrs.get('class') == 'mw-body-content':
                self.is_inside_body = True
            if attrs.get('class') == "catlinks":
                self.is_inside_body = False
            if attrs.get('class') == "mw-normal-catlinks":
                self.is_parsing_category = True
        if tag.lower() == 'p' and self.is_inside_body:
            self.is_parsing_content = True
        if tag.lower() == 'div' and 'class' in attrs and self.is_inside_body:
            if attrs.get("class") in ("mw-heading2", "mw-heading3", "mw-heading4"):
                self.is_parsing_content = True
        if tag.lower() == 'ul' and self.is_inside_body:
            self.is_parsing_content = True

    def handle_endtag(self, tag):
        if tag.lower() == 'script' and self.is_parsing_metadata:
            self.is_parsing_metadata = False
        if tag.lower() == 'p' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'div' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'ul' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'div' and self.is_parsing_category:
            self.is_parsing_category = False

    def handle_data(self, data):
        if self.is_parsing_metadata:
            self.article_metadata.append(data.strip())
        if self.is_parsing_content:
            self.article_content.append(data.strip())
        if self.is_parsing_category:
            self.article_categories.append(data.strip())
