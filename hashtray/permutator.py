import itertools
import math
from typing import Any, Generator


if hasattr(math, "perm"):
    def _perm_count(n: int, r: int) -> int:
        return math.perm(n, r)
else:
    def _perm_count(n: int, r: int) -> int:
        result = 1
        for k in range(r):
            result *= n - k
        return result


class Permute:
    def __init__(self, chunks: list, domains: list, crazy: bool = False):

        self.chunks = chunks
        self.len_chunks = len(self.chunks)
        self.crazy = crazy
        self.separators = ["", ".", "_", "-"]
        self.domains = domains
        self.len_domains = len(self.domains)

    def get_combination_count(self) -> int:
        """
        Calculate the total number of combinations for tdqm bar progress
        """
        n = self.len_chunks
        if n == 0:
            return 0
        s = len(self.separators)
        total = n
        for r in range(2, n + 1):
            base = _perm_count(n, r)
            sep_factor = s ** (r - 1) if self.crazy else s
            total += base * sep_factor
        return total * self.len_domains

    def combinator(self) -> Generator[str, Any, None]:
        """
        Generate all email combinations for unique elements
        """

        chunks = self.chunks
        separators = self.separators
        domain_suffixes = [f"@{domain}" for domain in self.domains]
        crazy = self.crazy
        cache_limit = 10000

        # Generate all permutations/combinations of elements
        # Per chunk
        for r in range(1, len(chunks) + 1):
            # Per chunk permutation
            for permutation in itertools.permutations(chunks, r):
                # No need of separator for single chunks
                if r == 1:
                    locals_for_perm = [permutation[0]]
                else:
                    # Crazy mode: per separator, any kind of separator in each combination at any place
                    if crazy:
                        sep_count = len(separators) ** (r - 1)
                        if sep_count <= cache_limit:
                            locals_for_perm = []
                            for sep_combo in itertools.product(separators, repeat=r - 1):
                                email_local_part = "".join(
                                    f"{e}{s}"
                                    for e, s in itertools.zip_longest(
                                        permutation, sep_combo, fillvalue=""
                                    )
                                )
                                locals_for_perm.append(email_local_part)
                        else:
                            # Avoid large memory spikes in crazy mode.
                            for suffix in domain_suffixes:
                                for sep_combo in itertools.product(
                                    separators, repeat=r - 1
                                ):
                                    email_local_part = "".join(
                                        f"{e}{s}"
                                        for e, s in itertools.zip_longest(
                                            permutation, sep_combo, fillvalue=""
                                        )
                                    )
                                    yield f"{email_local_part}{suffix}"
                            continue
                    else:
                        # Normal mode: per separator, unique separator in each combination at any place
                        locals_for_perm = [
                            separator.join(permutation) for separator in separators
                        ]

                # Per domain, preserve order
                for suffix in domain_suffixes:
                    for local_part in locals_for_perm:
                        yield f"{local_part}{suffix}"
