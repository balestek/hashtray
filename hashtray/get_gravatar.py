import hashlib
import logging
import re

import httpx
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from scrapling.fetchers import AsyncFetcher

logging.getLogger("scrapling").setLevel(logging.CRITICAL)

class Gravatar:
    def __init__(self, email=None, ghash: str = None, account: str = None):
        self.rich = Console(
            highlight=False, theme=Theme({"repr.url": "not underline white"})
        )
        self.gravatar_url = "https://gravatar.com/"
        self.email = email
        self.account = account
        if account:
            self.account_url = self.gravatar_url + account
        elif ghash:
            self.ghash = ghash
            self.account_url = self.gravatar_url + ghash
            self.hash = ghash
        else:
            self.check_email()
            self.hash = hashlib.md5(email.encode()).hexdigest()
            self.account_url = self.gravatar_url + self.hash
        self.json_hash = None
        self.is_exists = False


    def check_email(self) -> bool:
        """
        Check if a string is a valid email
        """
        if re.match(r"(^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", self.email):
            return True
        else:
            self.rich.print(f"[red]Invalid email address: {self.email}.[/red]\n")
            exit()

    async def get_gravatar_json(self) -> dict | None:
        """
        Get the user's json data from Gravatar
        """
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(self.account_url + ".json")
                res.raise_for_status()
                self.is_exists = True
                self.hash = res.json()["entry"][0]["hash"]
                return res.json()["entry"][0]
            except httpx.HTTPError:
                if res.status_code == 404:
                    self.rich.print(f"[red]Gravatar profile not found (404 HTTP status error)[/red]")
                elif res.status_code == 429:
                    self.rich.print(
                        f"[red]Too many requests. Please try again later or with another IP (429 HTTP status error)[/red]")
                else:
                    self.rich.print(f"[red]An error occurred. Try again.[/red]")
                return None

            except Exception as e:
                self.rich.print(f"[red]An error occurred: {e}[/red]")
            return None

    async def scrap_account(self) -> dict:
        """
        Scrap the user account page to retrieve all infos as the json/API is now limited
        """
        def find_accounts(page):
            if verified := page.find(".is-verified-accounts"):
                accounts_list = []
                for account in verified.find_all(".card-item__info"):
                    network = account.find(".card-item__label-text").text.clean()
                    urls = account.find_all("a")
                    for url in urls:
                        if url.attrib.get("class") != "card-item__checkmark-icon":
                            account_url = url.attrib["href"]
                            accounts_list.append({"account": network, "url": account_url})
                return accounts_list
            return None

        def find_images(page):
            if gallery := page.find(".g-profile__photo-gallery"):
                images_list = []
                for image in gallery.find_all("img"):
                    url = image.attrib["data-url"] + "?size=666"
                    images_list.append(url)
                return images_list
            return None

        def find_payments(page):
            if payment := page.find(".payments-drawer"):
                payment_list = []
                for item in payment.find_all(".card-item"):
                    title = item.find(".card-item__label-text").text.clean()
                    try:
                        asset = item.find("a").attrib["href"]
                    except:
                        asset = item.find(".card-item__info span:not(.card-item__label-text)").text.clean()
                    payment_list.append({"title": title, "asset": asset})
                return payment_list if len(payment_list) > 0 else None
            return None

        def find_interests(page):
            if interests := page.find(".g-profile__interests-list"):
                interests_list = []
                for interest in interests.find_all("li a"):
                    interests_list.append(interest.text.clean())
                for interest in interests.find_all("li span"):
                    interests_list.append(interest.text.clean())
                return interests_list
            return None

        def find_links(page):
            if links := page.find(".g-profile__links"):
                links_list = []
                for link in links.find_all(".card-item__info"):
                    description = None
                    a = link.find("a")
                    name = a.text.clean()[:-2]
                    url = a.attrib["href"]
                    if desc := link.find("p"):
                        description = desc.text
                    links_list.append({"name": name, "url": url, "description": description})
                return links_list
            return None

        gravatar_page = await AsyncFetcher().get(self.account_url)

        scrapped_infos = {
            "accounts": find_accounts(gravatar_page),
            "photos": find_images(gravatar_page),
            "payments": find_payments(gravatar_page),
            "interests": find_interests(gravatar_page),
            "links": find_links(gravatar_page),
        }
        return scrapped_infos

    async def aggregate_gravatar_infos(self) -> dict | None:
        """
        Aggregate the account json data and scrapped data
        """
        if json_data := await self.get_gravatar_json():
            scrapped_data = await self.scrap_account()

            infos = {
                "Hash": self.hash or self.json_hash,
                "Profile URL": self.account_url,
                "Avatar": json_data.get("thumbnailUrl") + "?size=666",
                "Last edit": json_data.get("lastProfileEdit"),
                "Location": json_data.get("currentLocation"),
                "Preferred username": json_data.get("preferredUsername"),
                "Display name": json_data.get("displayName"),
                "Pronunciation": json_data.get("pronunciation"),
                "Name": json_data.get("name"),
                "Pronouns": json_data.get("pronouns"),
                "About me": json_data.get("aboutMe"),
                "Job Title": json_data.get("jobTitle"),
                "Company": json_data.get("company"),
                "Emails": [email["value"] for email in json_data.get("emails")] if json_data.get("emails") else None,
                "Contact Info": json_data.get("contactInfo"),
                "Phone Numbers": json_data.get("phoneNumbers"),
                "Verified accounts": scrapped_data["accounts"],
                "Payments": scrapped_data["payments"],
                "Photos": scrapped_data["photos"],
                "Interests": scrapped_data["interests"],
                "Links": scrapped_data["links"],
            }
            return infos
        else:
            return None

    async def show_gravatar_infos(self, data: dict = None) -> None:
        """
        Print the gravatar infos in a table format
        """
        # Print data in list format
        def print_list(key: str, value: list) -> None:
            all_values = []
            for item in value:
                all_values.append(str(item))
            table.add_row(key, "\n".join(all_values))
        # Print data in list of dicts format
        def print_list_of_dicts(key: str, value: list) -> None:
            all_values = []
            for item in value:
                if isinstance(item, dict) and len(item) == 2:
                    keys = list(item.keys())
                    left = item[keys[0]]
                    right = item[keys[1]]
                    all_values.append("{:<13s}{}".format(left, right))

                else:
                    for sub_key, sub_value in item.items():
                        all_values.append(sub_value)

            table.add_row(key, "\n".join(all_values))

        # Get gravatar data
        with self.rich.status("Retrieving and scraping profile...", spinner="dots", spinner_style="turquoise2") as status:
            data = await self.aggregate_gravatar_infos()
            if not data:
                exit("\n")

        # Build the table
        table = Table(title=f"[b turquoise2]{data['Preferred username']}[/b turquoise2]", show_header=False, show_lines=True)
        table.add_column("", justify="right", style="turquoise2")
        table.add_column("", style="bold bright_white")

        if data:
            for key, value in data.items():
                if value:
                    if isinstance(value, list) and all(isinstance(i, dict) for i in value):
                        print_list_of_dicts(key, value)
                    elif isinstance(value, list):
                        print_list(key, value)
                    else:
                        table.add_row(key, str(value))

        # Print the table
        self.rich.print(table)
