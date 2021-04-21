from __future__ import annotations

import typing

import abc

from dusk.ir import annotatable
from dusk import errors


TreeType = typing.TypeVar("TreeType")


class TreeHandle(annotatable.Annotatable, typing.Generic[TreeType]):
    tree: TreeType
    invariants: TreeInvariants[TreeType]

    def __init__(
        self,
        tree: TreeType,
        invariants: typing.Optional[TreeInvariants[TreeType]] = None,
    ):
        # TODO: should this constructor support cooperative inheritance?
        super().__init__()

        if invariants is None:
            invariants = TreeInvariants()

        self.tree = tree
        self.invariants = invariants


class TreeValidator(abc.ABC, typing.Generic[TreeType]):
    def name(self):
        return type(self).__name__

    @abc.abstractmethod
    def validate(self, tree_handle: TreeHandle[TreeType]) -> None:
        raise NotImplementedError

    def is_valid(self, tree_handle: TreeHandle[TreeType]) -> bool:
        try:
            self.validate(tree_handle)
            return True
        except errors.ValidationError:
            return False


class TreeInvariants(typing.Generic[TreeType]):

    invariants: typing.Dict[str, TreeValidator[TreeType]]

    def __init__(self, *validators: TreeValidator[TreeType]):
        self.invariants = {validator.name(): validator for validator in validators}

    def add(self, validator: TreeValidator[TreeType]) -> None:
        self.invariants[validator.name()] = validator

    def remove(self, validator: TreeValidator[TreeType]) -> None:
        self.invariants.pop(validator.name())

    def __contains__(self, validator: typing.Any) -> bool:
        if not isinstance(validator, TreeValidator):
            return False
        return validator.name() in self.invariants

    def __iter__(self) -> typing.Iterator[TreeValidator]:
        return (validator for validator in self.invariants.values())

    def validate(self, tree_handle: TreeHandle[TreeType]) -> None:
        for validator in self.invariants.values():
            validator.validate(tree_handle)


class TreeTransformer(abc.ABC, typing.Generic[TreeType]):
    preconditions: TreeInvariants[TreeType]
    postconditions: TreeInvariants[TreeType]

    tree_handle: TreeHandle[TreeType]

    def __init__(self, tree_handle: TreeHandle[TreeType]):
        self.tree_handle = tree_handle

        if not hasattr(type(self), "preconditions"):
            self.preconditions = TreeInvariants()
        if not hasattr(type(self), "postconditions"):
            self.postconditions = TreeInvariants()

    def transform(self) -> None:
        self.tree_handle.invariants.validate(self.tree_handle)
        self.preconditions.validate(self.tree_handle)
        self.transform_bare()
        self.postconditions.validate(self.tree_handle)
        self.tree_handle.invariants.validate(self.tree_handle)

    @abc.abstractmethod
    def transform_bare(self) -> None:
        raise NotImplementedError
