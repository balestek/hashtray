import re

import tldextract
from unidecode import unidecode


class GetElements:
    """
    Class to handle chunking and deduping a gravatar profile data.
    """

    def __init__(self, gravatar_info: dict):
        self.gravatar_info = gravatar_info
        self.elements = []
        self.domains = []
        self.name_pattern = "[-_ ./]"

    @staticmethod
    def last_url_chunk(url: str) -> str:
        """
        Get the last chunk of a URL.
        """
        return url.split("/")[-1]

    def format_elements(self) -> None:
        """
        Build an intermediary list of elements, deduped, lowercased and unidecode.
        """
        # lowercase and unidecode all elements
        lower_elements = [
            unidecode(element.lower())
            for element in self.elements
        ]
        unique_element = []
        # dedupe elements
        [
            unique_element.append(element)
            for element in lower_elements if element not in unique_element
        ]
        self.elements = unique_element

    def is_combination(self, s: str, chunks: list) -> bool:
        """
        Check if a string is a combination of other strings in the list.
        """
        if s in chunks:
            chunks.remove(s)
        # try all possible splits
        for i in range(1, len(s)):
            left = s[:i]
            right = s[i:]
            if left in chunks and right in chunks:
                return True
            if left in chunks and self.is_combination(right, chunks):
                return True
            if right in chunks and self.is_combination(left, chunks):
                return True
        return False

    def dedup_chunks(self) -> list:
        """
        Remove chunks that are made from other strings in the list.
        """
        # keep only elements that are not combinations of others
        return [s for s in self.elements if not self.is_combination(s, self.elements.copy())]

    def add_preferred_username(self) -> None:
        """
        Add the preferred username from gravatar_info to elements.
        """
        preferred_username = self.gravatar_info.get("Preferred username")
        if preferred_username:
            self.elements.append(preferred_username)

    def add_display_name(self) -> None:
        """
        Add display name and its parts to elements.
        """
        display_name = self.gravatar_info.get("Display name")
        # split display name using the pattern and clean up
        names = re.split(self.name_pattern, unidecode(display_name))
        names = [name.replace('"', "").replace("'", "") for name in names]
        # add all name parts
        self.elements.extend(name for name in names if name)
        # add initials
        self.elements.extend(name[:1] for name in names if len(name) > 1)

    def add_accounts(self) -> None:
        """
        Add account chunks for verified accounts.
        """
        accounts = self.gravatar_info.get("Verified accounts")
        if accounts:
            for account in accounts:
                account_url = account["url"].rstrip("/")
                self.process_account(account["account"], account_url)

    def process_account(self, account: str, account_url: str) -> None:
        """
        Process the account and add relevant chunks to elements and domains.
        """
        # handle each account type specifically
        if account in ["Mastodon", "Fediverse", "TikTok"]:
            self.elements.append(self.last_url_chunk(account_url).replace("@", ""))
        elif account == "LinkedIn":
            # only add if URL matches LinkedIn profile
            (
                self.elements.append(self.last_url_chunk(account_url))
                if f"{account.lower()}.com/in/" in account_url
                else None
            )
        elif account == "YouTube":
            self.elements.append(self.last_url_chunk(account_url).lstrip("@"))
        elif account == "Tumblr":
            extracted = tldextract.extract(account_url)
            if extracted.subdomain:
                self.elements.append(extracted.subdomain)
            else:
                self.elements.append(account_url.split("/")[-1])
        elif account == "WordPress":
            extracted = tldextract.extract(account_url)
            if extracted.subdomain:
                self.elements.append(extracted.subdomain)
            else:
                if extracted.domain:
                    self.elements.append(extracted.domain)
                    self.domains.append(extracted.domain + "." + extracted.suffix)
        elif account == "Bluesky":
            handle = account_url.split("/")[-1]
            match = re.match(r"([a-zA-Z0-9._-]+)\.bsky\.social", handle)
            if match:
                self.elements.append(match.group(1))
            else:
                handle_parts = handle.split(".")
                self.elements.append(handle_parts[0])
                self.domains.append(handle_parts[0] + "." + handle_parts[1])
        elif account in ["Facebook", "Instagram"]:
            if "profile.php" not in account_url:
                self.elements.extend(
                    chunk for chunk in self.last_url_chunk(account_url).split(".")
                )
        elif account == "Stack Overflow":
            self.elements.extend(chunk for chunk in self.last_url_chunk(account_url).split("-"))
        elif account == "Flickr":
            if "/people/" not in account_url:
                self.elements.extend(
                    chunk for chunk in self.last_url_chunk(account_url).split("-")
                )
        elif account in ["Twitter", "X"]:
            self.elements.extend(chunk for chunk in self.last_url_chunk(account_url).split("_"))
        elif account == "TripIt":
            if "/people/" in account_url:
                self.elements.extend(
                    chunk for chunk in self.last_url_chunk(account_url).split(".")
                )
        elif account == "Goodreads":
            self.elements.extend(
                chunk for chunk in self.last_url_chunk(account_url).split("-")[1:]
            )
        elif account not in [
            "Foursquare",
            "Yahoo",
            "Google+",
            "Vimeo",
        ]:
            chunk = self.last_url_chunk(account_url)
            self.elements.append(chunk)

    def get_elements(self) -> tuple[list[str | None], list[str | None]]:
        """
        Extract and return elements and domains from a Gravatar profile.
        """
        self.add_preferred_username()
        self.add_display_name()
        self.add_accounts()
        self.format_elements()
        self.elements = self.dedup_chunks()
        return self.elements, self.domains
