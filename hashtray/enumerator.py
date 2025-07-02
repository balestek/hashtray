import hashlib
import json
import re
from pathlib import Path

import tldextract
from rich.console import Console
from rich.prompt import Confirm
from tqdm import tqdm

from hashtray.get_elements import GetElements
from hashtray.get_gravatar import Gravatar
from hashtray.permutator import Permute


class Enumerator:
    def __init__(
        self,
        account,
        strings: list = None,
        domain_list: str = None,
        custom_domains: list = None,
        crazy: bool = False,
    ):
        self.account = account
        self.elements = strings
        self.chunks = []
        self.account_hash = None
        self.hash_type = None
        self.separators = ["", ".", "_", "-"]
        self.name_pattern = "[-_ ./]"
        self.emails = []
        self.public_emails = []
        self.crazy = crazy
        self.domain_list = domain_list
        # load default or custom domains
        self.domains = self.load_domains()
        if custom_domains:
            # add custom domains
            self.domains = custom_domains + self.domains
        self.len_domains = len(self.domains)
        self.gravatar = None
        self.gravatar_instance = None
        self.n = 0
        self.elapsed = 0
        self.combination_count = 0
        self.info = {}
        self.hasher = None
        self.rich = Console(highlight=False)

    def load_domains(self) -> json:
        """
        Load the list of email domains based on the domain_list type.
        """
        domain_files = {None: "", "common": "", "long": "_long", "full": "_full"}
        domain_file = domain_files[self.domain_list]
        with open(
            Path(Path(__file__).parent, "data", f"email_services{domain_file}.json"),
            "r",
        ) as f:
            return json.load(f)

    @staticmethod
    def check_email(s: str) -> bool:
        """
        Check if a string is a valid email address.
        """
        return re.fullmatch(
            r"(^[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", s
        ) is not None

    @staticmethod
    def check_md5(s: str) -> bool:
        """
        Check if a string is a valid MD5 hash.
        """
        return re.fullmatch(r"[a-fA-F0-9]{32}", s) is not None

    @staticmethod
    def check_sha256(s: str) -> bool:
        """
        Check if a string is a valid SHA256 hash.
        """
        return re.fullmatch(r"[a-fA-F0-9]{64}", s) is not None

    def check_hash(self, s: str) -> str or None:
        """
        Return the hash type if the string matches MD5 or SHA256, else None.
        """
        # detect MD5 first, then SHA256
        if self.check_md5(s):
            return "MD5"
        elif self.check_sha256(s):
            return "SHA256"
        else:
            return None

    def show_chunks(self) -> str:
        """
        Return a comma-separated string of all chunks to display.
        """
        # join list of chunks with comma and space
        return ", ".join(self.chunks)

    def add_links_domains(self) -> None:
        """
        Add domains found in the Gravatar profile links at the top of the domains list.
        """
        if self.gravatar["Links"]:
            for link in self.gravatar["Links"]:
                # extract domain and suffix from URL
                ext = tldextract.extract(link["url"])
                domain = ext.domain + "." + ext.suffix
                if domain not in self.domains:
                    # insert new domain at beginning
                    self.domains.insert(0, domain)

    def add_element_domains(self, domains: list) -> None:
        """
        Add new domains from elements to the domains list if not already present.
        """
        [self.domains.insert(0, domain) for domain in domains if domain not in self.domains]

    def get_public_emails(self) -> None:
        """
        Extract public emails from the Gravatar profile.
        """
        if self.gravatar["Emails"]:
            # extend public_emails from the profile
            self.public_emails.extend(self.gravatar["Emails"])
        # find email in the "About me" section
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        find = (
            re.findall(pattern, self.gravatar["About me"])
            if self.gravatar["About me"]
            else None
        )
        self.public_emails.extend(find) if find else None

    @staticmethod
    def _get_hasher(hash_type):
        """
        Return a hash based on the hash type.
        """
        if hash_type == "MD5":
            # MD5 hashing function (lowercased email)
            return lambda email: hashlib.md5(email.lower().encode()).hexdigest()
        elif hash_type == "SHA256":
            # SHA256 hashing function (lowercased email)
            return lambda email: hashlib.sha256(email.lower().encode()).hexdigest()
        else:
            # unsupported type
            raise ValueError("Unsupported hash type")

    def _print_no_gravatar(self) -> None:
        """
        Print an error message and exit if no Gravatar account is found.
        """
        # rich formatted error output with usage instructions
        self.rich.print(
            f"[bright_red]A matching Gravatar account for {self.account} could not be retrieved.[/bright_red]\n\n"
            "[bright_white]To continue, you’ll need the account’s hash and some known elements about the target.\n"
            "Use the command `[gold1]hashtray[/gold1] [orange_red1]account[/orange_red1] <MD5 OR SHA256 HASH> [orange3]-e[/orange3] [tan]element1 element2 ...[/tan]` to search for possible email addresses.\n"
            "Example: `hashtray account 437e4dc6d001f2519bc9e7a6b6412923 -e marco m polo p`\n"
            "[/bright_white]For elements like first or last names, consider including initials as well to match patterns like f_lastname@domain.tld\n"
        )
        exit()

    async def collect_elements(self) -> None:
        """
        Main method to collect elements, enumerate possible email addresses and display results.
        """
        # detect if account is a hash and set hash_type
        self.hash_type = self.check_hash(self.account)

        if self.hash_type:
            # account has already been a hash
            self.account_hash = self.account
            self.gravatar_instance = Gravatar(ghash=self.account)
            self.gravatar = await self.gravatar_instance.aggregate_gravatar_infos()
            if not self.gravatar:
                # no gravatar account found by hash
                if self.elements is None:
                    self._print_no_gravatar()
                    exit()
                elif self.elements:
                    # warn and continue with provided elements
                    self.rich.print(
                        f"[bright_red]No Gravatar account found for the provided hash: {self.account}.[/bright_red]\n"
                        "[orange3]Continuing with the provided elements to search for possible email addresses.[/orange3]\n"
                    )
        else:
            # account is an email or username
            self.gravatar_instance = Gravatar(account=self.account)
            self.gravatar = await self.gravatar_instance.aggregate_gravatar_infos()
            if self.gravatar:
                # set hash from gravatar data
                self.account_hash = self.gravatar["Hash"]
                self.hash_type = self.check_hash(self.account_hash)
            elif not self.gravatar:
                # no gravatar account at all
                self._print_no_gravatar()
                exit()

        if self.gravatar:
            # retrieve public emails and chunk elements/domains
            self.get_public_emails()
            self.chunks, domains = GetElements(self.gravatar).get_elements()
            self.add_links_domains()
            self.add_element_domains(domains)
            self.len_domains = len(self.domains)

        if self.elements:
            # include any user-provided elements
            for e in self.elements:
                if e not in self.chunks:
                    self.chunks.append(e)

        # prepare permutator and count combinations
        permute = Permute(self.chunks, self.domains, self.crazy)
        self.combination_count = permute.get_combination_count()

        # display enumeration stats
        self.rich.print(
            f"Elements to permute: [gold3]{self.show_chunks()}[/gold3]\n"
            f"Number of email domains: {self.len_domains}\n"
            f"Number of possible combinations: {self.combination_count}\n"
        )

        # get appropriate hashing function
        self.hasher = self._get_hasher(self.hash_type)

        enum_email_found = None
        # iterate over all permutations with progress bar
        progress = tqdm(total=self.combination_count, desc="Comparing email hashes", unit="it")
        for email in permute.combinator():
            hashed = self.hasher(email)
            progress.update(1)
            if hashed == self.account_hash:
                # email matching the hash
                enum_email_found = email
                break
        progress.close()

        # display results
        self.rich.print(f"\n[bold u turquoise2]RESULTS:")

        if self.public_emails:
            # list public emails found and check each against the hash
            self.rich.print(
                f"\n[dark_turquoise]Email{'s' if len(self.public_emails) > 1 else ''} found in the public profile:[/dark_turquoise] "
                f"[bright_white]{', '.join(self.public_emails)}[/bright_white]\n"
            )
            for public_email in self.public_emails:
                if self.account_hash == self.hasher(public_email):
                    # public email matches the account hash
                    self.rich.print(
                        f"[bold green3]{public_email} matches the account hash.[/bold green3] "
                        "It's used as the primary Gravatar email for the account"
                    )
                else:
                    #the public email is not the account hashed email
                    self.rich.print(
                        f"[orange3]{public_email} does not match the account hash:[/orange3]. "
                        "The Gravatar account email is not this email, there is at least another one to find."
                    )

        if enum_email_found:
            # Yay !
            self.rich.print(
                f"\n[bright_white]An email has been found with the email hashes enumeration:[/bright_white] "
                f"[bold green3]{enum_email_found}[/bold green3]\n"
            )
            # prompt to retrieve Gravatar profile
            show_profile = Confirm.ask("Do you want to see the gravatar profile if available?")
            if show_profile:
                await self.gravatar_instance.show_gravatar_infos(self.gravatar)
        elif not enum_email_found and not self.public_emails:
            #:(
            self.rich.print(
                f"\n[red]No email found matching the account hash:[/red] [bright_white]{self.account_hash}[/bright_white]"
            )
        print("\n")
