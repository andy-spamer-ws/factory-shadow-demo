## Roman numeral converter

Convert between integers (1 to 3999) and Roman numerals:

```sh
python3 -m roman 1994      # prints MCMXCIV
python3 -m roman MCMXCIV   # prints 1994
python3 -m roman 4000      # prints "error: number must be between 1 and 3999" to stderr, exit 2
```

Invalid input prints one `error:` line to stderr and exits with status 2.

Run the tests:

```sh
uv run python -m pytest
python3 -m unittest tests.test_roman -v
```

## To-do list

Keep a to-do list in a JSON file:

```sh
python3 -m todo add "buy milk"   # prints "added 1: buy milk"
python3 -m todo done 1           # prints "done 1: buy milk"
python3 -m todo list             # prints "1 [x] buy milk"
python3 -m todo list --open      # lists only items not yet done
python3 -m todo remove 1         # prints "removed 1: buy milk"
```

The list is stored in the file named by the `TODO_FILE` environment variable, or `./todo.json` when it is unset or empty. Ids are never reused after removal.

Invalid input, an unknown id or a corrupt todo file prints one `error:` line to stderr and exits with status 2. A corrupt file is left unchanged.

Run the tests:

```sh
uv run python -m pytest
python3 -m unittest tests.test_store tests.test_items tests.test_cli -v
```
