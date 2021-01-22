import pytest

from dusk.script.internal import Domain
from dusk.script import domain, HorizontalDomains

from dusk import errors


def is_valid(domain: Domain) -> bool:
    if not isinstance(domain, Domain):
        return False

    if not domain.valid():
        return False
    return True


lb, nudging, interior, halo, end = HorizontalDomains(0, 1, 2, 3, 4)


def test_domain_functionality():

    assert is_valid(domain.upward)
    assert is_valid(Domain().upward)

    # simple cases
    assert is_valid(domain.upward[0:].across[lb:interior])
    assert is_valid(domain.across[nudging + 2 : halo - 1].upward[3])

    # only `upward`/`downward`
    assert is_valid(domain.upward)
    assert is_valid(domain.downward)
    # with intervals
    assert is_valid(domain.upward[0:3])
    assert is_valid(domain.downward[-6:-1])

    # accross
    assert is_valid(domain.upward.across[lb:lb])
    assert is_valid(domain.downward.across[interior:end])
    assert is_valid(domain.across[halo:end].upward)
    assert is_valid(domain.across[nudging:interior].downward)

    # TODO: intervals?

    # TODO: check correct interval + direction encodings


def test_domain_errors():

    # domain without `upward`/`downward` is invalid:
    assert not is_valid(domain)
    assert not is_valid(Domain())
    assert not is_valid(domain.across)
    assert not is_valid(Domain().across[lb:halo])

    # interval without `upward`/`downward`/`across`
    with pytest.raises(errors.SemanticError):
        domain[:]
    with pytest.raises(errors.SemanticError):
        Domain()[:]

    # `across` without interval
    assert not domain.across.valid()
    with pytest.raises(errors.SemanticError):
        domain.across.upward
    with pytest.raises(errors.SemanticError):
        domain.across.downward
    assert not is_valid(domain.downward.across)
    assert not is_valid(domain.upward.across)

    # invalid horizontal slices:
    with pytest.raises(errors.SemanticError):
        domain.upward.across["invalid_string"]
    with pytest.raises(errors.SemanticError):
        domain.downward.across[1]
    with pytest.raises(errors.SemanticError):
        domain.across[3:-3].downward
    with pytest.raises(errors.SemanticError):
        domain.across[lb:].upward

    # TODO: invalid intervals?
