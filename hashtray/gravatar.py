import hashlib
import re

import httpx
from rich.console import Console as c
from rich.theme import Theme


class Gravatar:
    def __init__(self, email=None, ghash: str = None, account: str = None):
        self.email = email
        self.gravatar_url = "https://gravatar.com/"
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
        self.infos = {
            "hash": None,
            "profileUrl": None,
            "thumbnailUrl": None,
            "last_profile_edit": None,
            "currentLocation": None,
            "preferredUsername": None,
            "displayName": None,
            "pronunciation": None,
            "name": None,
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

    def check_email(self):
        # Check if email is valid
        if re.match(r"(^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", self.email):
            return True
        else:
            self.c.print(f"[red]Invalid email address: {self.email}.[/red]")
            exit(0)

    def get_json(self):
        # Get Gravatar json data
        try:
            res = httpx.get(self.account_url + ".json")
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(e)

    def process_list(self, info, data):
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

    def info(self):
        # Get the Gravatar info if it's a list or not
        try:
            data = self.get_json()["entry"][0]
        except:
            if self.email:
                self.c.print(
                    f"[bold][red]:cross_mark:  Account not found for {self.email}.[/red][/bold]\n"
                )
                exit(0)
            else:
                return data
        self.json_hash = data["hash"]
        for info in data:
            if info in self.infos and data[info]:
                if isinstance(data[info], list):
                    self.infos[info] = self.process_list(info, data)
                else:
                    self.infos[info] = data[info]
        return self.infos

    def print_info(self):
        # Print the Gravatar profile infos
        data = self.info()
        if self.email:
            self.c.print(
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
