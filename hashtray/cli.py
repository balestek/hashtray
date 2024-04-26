import argparse
import sys

from rich.console import Console

from hashtray.__about__ import __version__ as version
from hashtray.email_enum import EmailEnum
from hashtray.gravatar import Gravatar

c = Console(highlight=False)


def parse_app_args(arguments=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    subp_email = subparsers.add_parser(
        "email", help="Find a Gravatar account from an email address"
    )
    subp_email.add_argument(
        "email", type=str, help="Email address to search in Gravatar.com"
    )

    subp_account = subparsers.add_parser(
        "account", help="Find an email address from a Gravatar username or hash"
    )
    subp_account.add_argument(
        "account",
        type=str,
        help="Gravatar username or hash to search for email in Gravatar.com",
    )
    subp_account.add_argument(
        "--domain_list",
        "-l",
        choices=["common", "long", "full"],
        help="Domain list to use for email enumeration. Default: common",
        default="common",
    )
    subp_account.add_argument(
        "--elements",
        "-e",
        type=str,
        help="Generate combinations with your elements/strings instead",
        nargs="*",
    )
    subp_account.add_argument(
        "--domains",
        "-d",
        type=str,
        help="Use your custom email domains for emails generation",
        nargs="*",
    )
    subp_account.add_argument(
        "--crazy",
        "-c",
        help="Go crazy and try EVERY SINGLE combination (with any special char. at any place in the combinations)",
        action="store_true",
    )

    return parser.parse_args(args=None if sys.argv[1:] else ["--help"])


def main() -> None:
    c.print(
        f"""[bold]
[turquoise2]⠀⠀⣠⣴⣶⠿⠿⣷⣶⣄⠀⠀⠀[/turquoise2]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
[turquoise2]⠀⢾⠟⠉⠀⠀⠀⠀⠈⠁⠀⠀⠀⠀[/turquoise2]⣤⡄⠀⣤⠀⠀⣤⣄⠀⢀⣤⠤⠤⠀⣤⠀⢠⡄⠤⢤⣤⠤⢠⣤⠤⣤⠀⠀⣠⣤⠀⠠⣤⠀⢠⡄
[turquoise2]⠀⠀⠀⠀⠀⠀⣶⣶⣶⣶⣶⣶⠂⠀[/turquoise2]⣿⣇⣀⣿⠀⢰⡟⢿⡀⠸⣧⣀⠀⠀⣿⣀⣸⡇⠀⢸⡇⠀⢸⡇⠀⣹⡇⢀⣿⢻⡇⠀⢹⣦⡿⠁
[turquoise2]⣀⣀⠀⠀⠀⠀⠋⠃⠀⠀⢸⣿⠀⠀[/turquoise2]⣿⡏⠉⣿⠀⣾⠧⢾⣇⠀⠈⠙⣿⠀⣿⠉⢹⡇⠀⢸⡇⠀⢸⡿⢺⣟⠀⣸⡷⠼⣿⠀⠀⣿⠃⠀
[turquoise2]⠘⢿⣦⣀⠀⠀⠀⠀⢀⣴⣿⠋⠀⠀[/turquoise2]⠛⠃⠀⠛⠐⠛⠀⠀⠛⠐⠶⠶⠛⠀⠛⠀⠘⠃⠀⠘⠃⠀⠘⠓⠀⠛⠂⠛⠀⠀⠙⠃⠀⠛⠀⠀
[turquoise2]⠀⠀⠙⠻⠿⣶⣶⡿⠿⠋⠁   [/turquoise2][/bold]jm  balestek⠀v{version}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       ⠀⠀⠀⠀⠀⠀
 """,
    )
    c.print(
        "[bold turquoise2]Gravatar Account and Email Finder[/bold turquoise2]\n"
        "Find a Gravatar account from an email address or\n"
        "find an email address from a Gravatar account or hash.\n"
        "\n"
        ":arrow_forward: [bold turquoise2]Find a gravatar account from en email:[/bold turquoise2]\n"
        "  [bright_white]Usage:[/bright_white] [gold1]hashtray[/gold1] [orange_red1]email[/orange_red1] email@example.com\n"
        "\n"
        ":arrow_forward: [bold turquoise2]Find a gravatar email from a gravatar username or hash:[/bold turquoise2]\n"
        "  [bright_white]Usage:[/bright_white] [gold1]hashtray[/gold1] [orange_red1]account[/orange_red1] username\n"
        "         [gold1]hashtray[/gold1] [orange_red1]account[/orange_red1] cc8c5b31041fcfd256ff6884ea7b28fb\n"
        "  [bright_white]Options:[/bright_white]\n"
        "    [orange3]--domain_list, -l[/orange3]  [tan]common|long|full[/tan]\n"
        "                       Domain list to use for email enumeration. Default: common\n"
        "    [orange3]--elements, -e[/orange3]     [tan]element1 element2 ...[/tan]\n"
        "                       Generate combinations with your elements/strings instead\n"
        "    [orange3]--domains, -d[/orange3]      [tan]domain1.com domain2.com ...[/tan]\n"
        "                       Use your custom email domains for emails generation\n"
        "    [orange3]--crazy, -c[/orange3]        Go crazy and try EVERY SINGLE combination\n"
        "                       (with any special character at any place in the combinations)\n"
        "                       Half as fast per sec., gazillion combinations but exhaustive\n"
    )

    args = parse_app_args()
    if args.cmd == "email" and args.email:
        Gravatar(args.email).print_info()
    elif args.cmd == "account" and args.account:
        EmailEnum(
            args.account,
            domain_list=args.domain_list,
            strings=args.elements,
            custom_domains=args.domains,
            crazy=args.crazy,
        ).find()
    else:
        exit("[red]Invalid command.[/red]")


if __name__ == "__main__":
    main()
