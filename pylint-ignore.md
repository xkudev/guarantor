# Pylint-Ignore

**WARNING: This file is programmatically generated.**

This file is parsed by [`pylint-ignore`](https://pypi.org/project/pylint-ignore/)
to determine which
[Pylint messages](https://pylint.pycqa.org/en/stable/technical_reference/features.html)
should be ignored.

- Do not edit this file manually.
- To update, use `pylint-ignore --update-ignorefile`

The recommended approach to using `pylint-ignore` is:

1. If a message refers to a valid issue, update your code rather than
   ignoring the message.
2. If a message should *always* be ignored (globally), then to do so
   via the usual `pylintrc` or `setup.cfg` files rather than this
   `pylint-ignore.md` file.
3. If a message is a false positive, add a comment of this form to your code:
   `# pylint:disable=<symbol> ; explain why this is a false positive`


# Overview

 - [C0103: invalid-name (1x)](#c0103-invalid-name)


# C0103: invalid-name

## File src/guarantor/main.py - Line 30 - C0103 (invalid-name)

- `message: Argument name "q" doesn't conform to snake_case naming style`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2022-06-09T10:46:01`

```
  28: 
  29: @app.get("/testint/{param}")
> 30: async def testint(param: int, q: int | None = None):
  31:     return {'message': param, 'q': q}
  32:
```

