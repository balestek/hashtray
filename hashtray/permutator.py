import itertools
from typing import Any, Generator


class Permute:
    def __init__(self, chunks: list, domains: list, crazy: bool = False):

        self.chunks = chunks
        self.len_chunks = len(self.chunks)
        self.crazy = crazy
        self.separators = ["", ".", "_", "-"]
        self.domains = domains
        self.len_domains = len(self.domains)

    def get_combination_count(self) -> int:
        # Calculate the total number of combinations for tdqm bar progress
        total = 0
        for r in range(1, self.len_chunks + 1):
            if r == 1:
                # Add single chunks
                total += self.len_chunks
            else:
                # Calc. combinations
                combinations = itertools.combinations(range(self.len_chunks), r)
                # Calc. permutations
                permutations = itertools.permutations(range(r))
                # Total possibilities for n chunks
                combination_count = len(list(combinations)) * len(list(permutations))
                # x number of special chars
                if self.crazy:
                    # crazy mode
                    total += combination_count * len(self.separators) ** (r - 1)
                else:
                    # normal mode
                    total += combination_count * len(self.separators)
        # Multiply by the number of domains
        return total * self.len_domains

    def combinator(self) -> Generator[str, Any, None]:
        # Generate all possible email combinations for unique elements

        # Generate all permutations/combinations of elements
        # Per chunk
        for r in range(1, len(self.chunks) + 1):
            # Per chunk permutation
            for permutation in itertools.permutations(self.chunks, r):
                # Per domain
                for domain in self.domains:
                    # No need of separator for single chunks
                    if len(permutation) == 1:
                        email_local_part = permutation[0]
                        yield f"{email_local_part}@{domain}"
                    else:
                        # Crazy mode: per separator, any kind of separator in each combination at any place
                        if self.crazy:
                            for separators in itertools.product(
                                self.separators, repeat=r - 1
                            ):
                                email_local_part = "".join(
                                    f"{e}{s}"
                                    for e, s in itertools.zip_longest(
                                        permutation, separators, fillvalue=""
                                    )
                                )
                                yield f"{email_local_part}@{domain}"
                        else:
                            # Normal mode: per separator, unique separator in each combination at any place
                            for separator in self.separators:
                                email_local_part = separator.join(permutation)
                                yield f"{email_local_part}@{domain}"
