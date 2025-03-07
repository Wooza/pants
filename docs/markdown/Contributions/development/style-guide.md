---
title: "Style guide"
slug: "style-guide"
excerpt: "Some conventions we encourage."
hidden: false
createdAt: "2020-05-17T04:29:11.796Z"
updatedAt: "2022-04-26T23:57:26.701Z"
---
Reminder: running the autoformatters and linters
------------------------------------------------

Most of Pants' style is enforced via Black, isort, Docformatter, Flake8, and MyPy. Run these commands frequently when developing:

```bash
$ ./pants --changed-since=HEAD fmt
$ build-support/githooks/pre-commit
```

> 📘 Tip: improving Black's formatting by wrapping in `()`
> 
> Sometimes, Black will split code over multiple lines awkwardly. For example:
> 
> ```python
> StrOption(
>     default="./pants",
>     help="The name of the script or binary used to invoke pants. "
>     "Useful when printing help messages.",
> )
> ```
> 
> Often, you can improve Black's formatting by wrapping the expression in parentheses, then rerunning `fmt`:
> 
> ```python
> StrOption(
>     default="./pants",
>     help=(
>         "The name of the script or binary used to invoke pants. "
>         "Useful when printing help messages."
>     ),
> )
> ```
> 
> This is not mandatory, only encouraged.

Comments
--------

### Style

Comments must have a space after the starting `#`. All comments should be complete sentences and should end with a period.

Good:

```python
# This is a good comment.
```

Bad:

```python
#Not This
```

Comment lines should not exceed 100 characters. Black will not auto-format this for you; you must manually format comments.

### When to comment

We strive for self-documenting code. Often, a comment can be better expressed by giving a variable a more descriptive name, adding type information, or writing a helper function.

Further, there is no need to document how typical Python constructs behave, including how type hints work. 

Bad:

```
# Loop 10 times.
for _ in range(10):
  pass

# This stores the user's age in days.
age_in_days = user.age * 365
```

Instead, comments are helpful to give context that cannot be inferred from reading the code. For example, comments may discuss performance, refer to external documentation / bug links, explain how to use the library, or explain why something was done a particular way.

Good:

```
def __hash__(self):
    # By overriding __hash__ here, rather than using the default implementation, 
    # we get a 10% speedup to `./pants list ::` (1000 targets) thanks to more
    # cache hits. This is safe to do because ...
    ...

# See https://github.com/LuminosoInsight/ordered-set for the original implementation.
class OrderedSet:
    ...
```

### TODOs

When creating a TODO, first [create an issue](https://github.com/pantsbuild/pants/issues/new) in GitHub. Then, link to the issue # in parantheses and add a brief description.

For example:

```python
# TODO(#5427): Remove this block once we can get rid of the `globs` feature.
```

Strings
-------

### Use `f-strings`

Use f-strings instead of `.format()` and `%`.

```python
# Good
f"Hello {name}!"

# Bad
"Hello {}".format(name)
"Hello %s" % name
```

Conditionals
------------

### Prefer conditional expressions (ternary expressions)

Similar to most languages' ternary expressions using `?`, Python has [conditional expressions](https://stackoverflow.com/a/394814). Prefer these to explicit `if else` statements because we generally prefer expressions to statements and they often better express the intent of assigning one of two values based on some predicate.

```python
# Good
x = "hola" if lang == "spanish" else "hello"

# Discouraged, but sometimes appropriate
if lang == "spanish":
   x = "hola"
else:
   x = "hello"
```

Conditional expressions do not work in more complex situations, such as assigning multiple variables based on the same predicate or wanting to store intermediate values in the branch. In these cases, you can use `if else` statements.

### Prefer early returns in functions

Often, functions will have branching based on a condition. When you `return` from a branch, you will exit the function, so you no longer need `elif` or `else` in the subsequent branches.

```python
# Good
def safe_divide(dividend: int, divisor: int) -> Optional[int]: 
    if divisor == 0:
        return None
    return dividend / divisor

# Discouraged
def safe_divide(dividend: int, divisor: int) -> Optional[int]: 
    if divisor == 0:
        return None
    else:
         return dividend / divisor
```

Why prefer this? It reduces nesting and reduces the cognitive load of readers. See [here](https://medium.com/@scadge/if-statements-design-guard-clauses-might-be-all-you-need-67219a1a981a) for more explanation.

Collections
-----------

### Use collection literals

Collection literals are easier to read and have better performance.

We allow the `dict` constructor because using the constructor will enforce that all the keys are `str`s. However, usually prefer a literal.

```python
# Good
a_set = {a}
a_tuple = (a, b)
another_tuple = (a,)
a_dict = {"k": v}

# Bad
a_set = set([a])
a_tuple = tuple([a, b])
another_tuple = tuple([a])

# Acceptable
a_dict = dict(k=v)
```

### Prefer merging collections through unpacking

Python has several ways to merge iterables (e.g. sets, tuples, and lists): using `+` or `|`, using mutation like `extend()`, and using unpacking with the `*` character. Prefer unpacking because it makes it easier to merge collections with individual elements; it is formatted better by Black; and allows merging different iterable types together, like merging a list and tuple together.

For dictionaries, the only two ways to merge are using mutation like `.update()` or using `**` unpacking (we cannot use PEP 584's `|` operator yet because we need to support \< Python 3.9.). Prefer merging with `**` for the same reasons as iterables, in addition to us preferring expressions to mutation.

```python
# Preferred
new_list = [*l1, *l2, "element"]
new_tuple = (*t1, *t2, "element")
new_set = {*s1, *s2, "element"}
new_dict = {**d1, "key": "value"}

# Discouraged
new_list = l1 + l2 + ["element"]
new_tuple = t1 + t2 + ("element",)
new_set = s1 | s2 | {"element"}
new_dict = d1
new_dict["key"] = "value"
```

### Prefer comprehensions

[Comprehensions](https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Comprehensions.html) should generally be preferred to explicit loops and `map`/`filter` when creating a new collection. (See <https://www.youtube.com/watch?v=ei71YpmfRX4> for a deep dive on comprehensions.)

Why avoid `map`/`filter`? Normally, these are fantastic constructs and you'll find them abundantly in the [Rust codebase](doc:contributions-rust). They are awkward in Python, however, due to poor support for lambdas and because you would typically need to wrap the expression in a call to `list()` or `tuple()` to convert it from a generator expression to a concrete collection.

```python
# Good
new_list = [x * 2 for x in xs]
new_dict = {k: v.capitalize() for k, v in d.items()}

# Bad
new_list = []
for x in xs:
    new_list.append(x * 2)

# Discouraged
new_list = list(map(xs, lambda x: x * 2))
```

There are some exceptions, including, but not limited to:

- If mutations are involved, use a `for` loop.
- If constructing multiple collections by iterating over the same original collection, use a `for` loop for performance.
- If the comprehension gets too complex, a `for` loop may be appropriate. Although, first consider refactoring with a helper function.

Classes
-------

### Prefer dataclasses

We prefer [dataclasses](https://realpython.com/python-data-classes/) because they are declarative, integrate nicely with MyPy, and generate sensible defaults, such as a sensible `repr` method.

```python
from dataclasses import dataclass

# Good
@dataclass(frozen=True)
class Example:
    name: str
    age: int = 33

# Bad
class Example:
    def __init__(self, name: str, age: int = 33) -> None:
        self.name = name
        self.age = age
```

Dataclasses should be marked with `frozen=True`.

If you want to validate the input, use `__post_init__`:

```python
@dataclass(frozen=True)
class Example:
    name: str
    age: int = 33

    def __post_init__(self) -> None:
        if self.age < 0:
            raise ValueError(
                f"Invalid age: {self.age}. Must be a positive number."
            )
```

If you need a custom constructor, such as to transform the parameters, use `@frozen_after_init` and `unsafe_hash=True` instead of `frozen=True`.

```python
from dataclasses import dataclass
from typing import Iterable, Tuple

from pants.util.meta import frozen_after_init

@frozen_after_init
@dataclass(unsafe_hash=True)
class Example:
    values: Tuple[str, ...]

    def __init__(self, values: Iterable[str]) -> None:
        self.values = tuple(values)
```

Type hints
----------

Refer to [MyPy documentation](https://mypy.readthedocs.io/en/stable/introduction.html) for an explanation of type hints, including some advanced features you may encounter in our codebase like `Protocol` and `@overload`.

### Annotate all new code

All new code should have type hints. Even simple functions like unit tests should have annotations. Why? MyPy will only check the body of functions if they have annotations. 

```python
# Good
def test_demo() -> None:
   assert 1 in "abc"  # MyPy will catch this bug.

# Bad
def test_demo():
   assert 1 in "abc"  # MyPy will ignore this.
```

Precisely, all function definitions should have annotations for their parameters and their return type. MyPy will then tell you which other lines need annotations.

> 📘 Interacting with legacy code? Consider adding type hints.
> 
> Pants did not widely use type hints until the end of 2019. So, a substantial portion of the codebase is still untyped.
> 
> If you are working with legacy code, it is often valuable to start by adding type hints. This will both help you to understand that code and to improve the quality of the codebase. Land those type hints as a precursor to your main PR.

### Prefer `cast()` to override annotations

MyPy will complain when it cannot infer the types of certain lines. You must then either fix the underlying API that MyPy does not understand or explicitly provide an annotation at the call site. 

Prefer fixing the underlying API if easy to do, but otherwise, prefer using `cast()` instead of a variable annotation.

```python
from typing import cast

# Good
x = cast(str, untyped_method()

# Discouraged
x: str = untyped_method()
```

Why? MyPy will warn if the `cast` ever becomes redundant, either because MyPy became more powerful or the untyped code became typed.

### Use error codes in `# type: ignore` comments

```python
# Good
x = "hello"
x = 0  # type: ignore[assignment]

# Bad
y = "hello"
y = 0  # type: ignore
```

MyPy will output the code at the end of the error message in square brackets.

### Prefer Protocols ("duck types") for parameters

Python type hints use [Protocols](https://mypy.readthedocs.io/en/stable/protocols.html#predefined-protocols) as a way to express ["duck typing"](https://realpython.com/lessons/duck-typing/). Rather than saying you need a particular class, like a list, you describe which functionality you need and don't care what class is used.

For example, all of these annotations are correct:

```python
from typing import Iterable, List, MutableSequence, Sequence

x: List = []
x: MutableSequence = []
x: Sequence = []
x: Iterable = []
```

Generally, prefer using a protocol like `Iterable`, `Sequence`, or `Mapping` when annotating function parameters, rather than using concrete types like `List` and `Dict`. Why? This often makes call sites much more ergonomic.

```python
# Preferred
def merge_constraints(constraints: Iterable[str]) -> str:
    ...

# Now in call sites, these all work.
merge_constraints([">=3.7", "==3.8"])
merge_constraints({">=3.7", "==3.8"})
merge_constraints((">=3.7", "==3.8"))
merge_constraints(constraint for constraint in all_constraints if constraint.startswith("=="))
```

```python
# Discouraged, but sometimes appropriate
def merge_constraints(constraints: List[str]) -> str
    ...

# Now in call sites, we would need to wrap in `list()`.
constraints = {">=3.7", "==3.8"}
merge_constraints(list(constraints))
merge_constraints([constraint for constraint in all_constraints if constraint.startswith("==")])
```

The return type, however, should usually be as precise as possible so that call sites have better type inference.

Tests
-----

### Use Pytest-style instead of `unittest`

```python
# Good
def test_demo() -> None:
   assert x is True
   assert y == 2
   assert "hello" in z

# Bad
class TestDemo(unittest.TestCase):
    def test_demo(self) -> None:
        self.assertEqual(y, 2)
```
