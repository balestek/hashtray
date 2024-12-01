import hashlib
import re
import asyncio

import httpx
from scrapling import Fetcher
from rich.console import Console as c
from rich.theme import Theme
from icecream import ic


class Gravatar:
    def __init__(self, email=None, ghash: str = None, account: str = None):
        self.gravatar_url = "https://gravatar.com/"
        self.email = email
        self.account = account
        if account:
            self.account_url = self.gravatar_url + account
        elif ghash:
            self.account_url = self.gravatar_url + ghash
            self.hash = ghash
        else:
            self.check_email()
            self.hash = hashlib.md5(email.encode()).hexdigest()
            self.account_url = self.gravatar_url + self.hash
        self.json_hash = None
        self.is_exists = False
        self.data = self.get_json()

        self.infos = {
            "hash": None,
            "profileUrl": None,
            "thumbnailUrl": None,
            "last_profile_edit": None,
            "currentLocation": None,
            "preferredUsername": None,
            "displayName": None,
            "pronunciation": None,
            "pronouns": None,
            "aboutMe": None,
            "job_title": None,
            "company": None,
            "emails": None,
            "contactInfo": None,
            "phoneNumbers": None,
            "accounts": None,
            "payments": None,
            "currency": None,
            "photos": None,
            "urls": None,
        }
        self.labels = {
            "hash": "Hash",
            "profileUrl": "Profile URL",
            "thumbnailUrl": "Avatar",
            "last_profile_edit": "Last profile edit",
            "currentLocation": "Location",
            "preferredUsername": "Preferred username",
            "displayName": "Display name",
            "pronunciation": "Pronunciation",
            "name": "Name",
            "pronouns": "Pronouns",
            "aboutMe": "About me",
            "job_title": "Job title",
            "company": "Company",
            "emails": "Emails",
            "contactInfo": "Contact info",
            "phoneNumbers": "Phone numbers",
            "accounts": "Accounts",
            "payments": "Payments",
            "currency": "Wallets",
            "photos": "Photos",
            "urls": "URLs",
            "familyName": "Family name",
            "givenName": "Given name",
            "formatted": "Formatted name",
            "contactform": "Contact form",
        }
        self.c = c(
            highlight=False, theme=Theme({"repr.url": "not underline bold white"})
        )

    def check_email(self) -> bool:
        # Check if email is valid
        if re.match(r"(^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", self.email):
            return True
        else:
            self.c.print(f"[red]Invalid email address: {self.email}.[/red]")
            exit()

    # def is_exists(self) -> bool:
    #     # Get Gravatar json data
    #     try:
    #         res = httpx.get(self.account_url + ".json")
    #         res.raise_for_status() ## Raise an exception for non-200 status codes
    #         return True
    #     except Exception as e:
    #         return False

    def get_json(self) -> dict:
        # Get Gravatar json data
        try:
            res = httpx.get(self.account_url + ".json")
            res.raise_for_status() ## Raise an exception for non-200 status codes
            self.is_exists = True
            self.hash = res.json()["entry"][0]["hash"]
            return res.json()
        except httpx.HTTPError as e:
            if res.response.status_code == 404:
                self.c.print(f"[red]Profile not found (404 error)[/red]")
            elif res.response.status_code == 429:
                self.c.print(
                    f"[red]Too many requests. Please try again later (429 error)[/red]")
            else:
                self.c.print(f"[red]HTTP error occurred: {e}[/red]")
        except Exception as e:
            self.c.print(f"[red]An error occurred: {e}[/red]")
        return {}

    def scrap_account(self) -> dict:
        # Scrap the user account page to retrieve all infos

        def find_accounts(page):
            if verified := page.find(".is-verified-accounts"):
                accounts_list = []
                for account in verified.find_all(".card-item__info"):
                    network = account.find(".card-item__label-text").text.clean()
                    url = account.find_all("a").last.attrib["href"]
                    accounts_list.append({"account": network, "url": url})
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
                link = None
                crypto = None
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
                for interest in interests.find_all("li"):
                    interests_list.append(interest.text)
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

        page = Fetcher().get(self.account_url)

        infos = {
            "accounts": find_accounts(page),
            "photos": find_images(page),
            "payments": find_payments(page),
            "interests": find_interests(page),
            "links": find_links(page),
        }

        return infos

    def process_list(self, info: list, data: dict) -> dict:
        # Build a dictionary with the json data
        info_dict = {}
        for i, item in enumerate(data[info]):
            if info == "photos":
                info_dict[f"photo {str(i + 1)}"] = item["value"]
            elif info == "emails":
                info_dict[f"email {str(i + 1)}"] = item["value"]
            elif info == "accounts":
                info_dict[item["name"]] = item["url"]
            elif info == "urls":
                if "title" in item.keys():
                    info_dict[item["title"]] = item["value"]
                else:
                    info_dict[item["value"]] = item["value"]
            elif item["type"] and item["value"]:
                info_dict[item["type"]] = item["value"]
            else:
                for key in item:
                    info_dict[key] = item[key]
        return info_dict

    def aggregate_infos(self, data: dict) -> dict:
        # Aggregate the json data and the scrapped data
        scrapped_data = self.scrap_account()

        infos = {
            "Hash": self.hash or self.json_hash,
            "Profile URL": self.account_url,
            "Avatar": data.get("thumbnailUrl") + "?size=666",
            "Last edit": data.get("lastProfileEdit"),
            "Location": data.get("currentLocation"),
            "Preferred username": data.get("preferredUsername"),
            "Display name": data.get("displayName"),
            "Pronunciation": data.get("pronunciation"),
            "Name": data.get("name"),
            "Pronouns": data.get("pronouns"),
            "About me": data.get("aboutMe"),
            "Job Title": data.get("jobTitle"),
            "Company": data.get("company"),
            "Emails": [email["value"] for email in data.get("emails")] if data.get("emails") else None,
            "Contact Info": data.get("contactInfo"),
            "Phone Numbers": data.get("phoneNumbers"),
            "Verified accounts": scrapped_data["accounts"],
            "Payments": scrapped_data["payments"],
            "Photos": scrapped_data["photos"],
            "Interests": scrapped_data["interests"],
            "Links": scrapped_data["links"],
        }
        return infos

    def info(self) -> dict:
        # Get the Gravatar info if it's a list or not
        data = {}
        try:
            data = self.data["entry"][0]
        except:
            if self.email:
                self.c.print(
                    f"[bold][red]:cross_mark:  Account not found on Gravatar for {self.email}.[/red][/bold]\n"
                )
                exit(0)
            else:
                return data

        self.json_hash = data["hash"]

        infos = self.aggregate_infos(data)
        return infos

        for info in data:
            if info in self.infos and data[info]:
                if isinstance(data[info], list):
                    self.infos[info] = self.process_list(info, data)
                else:
                    self.infos[info] = data[info]
        # return self.infos

    def print_info(self) -> None:
        # Print the Gravatar profile infos
        data = self.info()
        if self.email:
            self.c.print(
                f"------------------------------------------------------------------------------------\n"
                f"Gravatar info for    [bold white]{self.email}[/bold white]:\n"
            )
        for info in data:
            if data[info] is not None:
                if isinstance(data[info], dict):
                    self.c.print(f"{self.labels[info]}:")
                    for key, value in data[info].items():
                        if key not in self.labels[info]:
                            try:
                                key = self.labels[key]
                            except KeyError:
                                pass
                        self.c.print(
                            "{:<5s} {:<14s} [bold white]{:<10s}[/bold white]".format(
                                "", key, str(value)
                            )
                        )
                else:
                    self.c.print(
                        "{:<20s} [bold white]{:<10s}[/bold white]".format(
                            self.labels[info], str(data[info])
                        )
                    )
        print("\n")
        if self.email and self.hash != self.json_hash:
            self.c.print(
                f"[dark_orange]The hash of the email {self.email} is not the one of the primary Gravatar email of the account but a secondary email hash.[/dark_orange]\n"
                f"There is at least another email registered with this gravatar account.\n"
                "You can try to find it with the command 'hashtray account {account or account hash}'\n"
            )
