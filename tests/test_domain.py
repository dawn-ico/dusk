import pytest

from dusk.script.internal import Domain
from dusk.script import domain

from dusk.errors import SemanticError


def is_valid(domain: Domain) -> bool:
    if not isinstance(domain, Domain):
        return False

    if not domain.valid():
        return False
    return True


def test_domain_functionality():

    assert is_valid(domain.upward)
    assert is_valid(Domain().upward)

    # simple cases
    assert is_valid(domain.upward[0:].across[1:-1])
    assert is_valid(domain.across[:2].upward[3])

    # only `upward`/`downward`
    assert is_valid(domain.upward)
    assert is_valid(domain.downward)
    # with intervals
    assert is_valid(domain.upward[0:3])
    assert is_valid(domain.downward[-6:-1])

    # accross
    assert is_valid(domain.upward.across[1])
    assert is_valid(domain.downward.across[:-5])
    assert is_valid(domain.across[:6].upward)
    assert is_valid(domain.across[7:].downward)

    # TODO: intervals?

    # TODO: check correct interval + direction encodings


def test_domain_errors():

    # domain without `upward`/`downward` is invalid:
    assert not is_valid(domain)
    assert not is_valid(Domain())
    assert not is_valid(domain.across)
    assert not is_valid(Domain().across[-5:])

    # interval without `upward`/`downward`/`across`
    with pytest.raises(SemanticError):
        domain[:]
    with pytest.raises(SemanticError):
        Domain()[:]

    # `across` without interval
    assert not domain.across.valid()
    with pytest.raises(SemanticError):
        domain.across.upward
    with pytest.raises(SemanticError):
        domain.across.downward
    assert not is_valid(domain.downward.across)
    assert not is_valid(domain.upward.across)

    # TODO: invalid intervals?
