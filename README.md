# Conftastic

Simple and straight forward configuration. Inspired by [Flask](https://flask.palletsprojects.com/) and [Viper](https://github.com/spf13/viper).

Supported formats:

* JSON - requires [jstyleson](https://github.com/linjackson78/jstyleson)
* TOML
* YAML
* INI
* .env - requires [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
* Environment variables

## Example using Config

```python
from conftastic import Config

# Creating a config with default values
config = Config({
    "a_default_value": 123,
})

# Loading from settings.json:
config.from_json("settings.json")

print(config)  # {'a_default_value': 123, 'a_setting': 'victory!'}
print(config["a_default_value"])  # 123
print(config["a_setting"])  # victory!

print(config.get("a_default_value"))  # 123
print(config.get("a_setting"))  # victory!

print(config["non_existing"])  # KeyError
print(config.get("non_existing"))  # None
print(config.get("non_existing", "fallback!"))  # fallback!
```

`settings.json`:

```json
{
    "a_setting": "victory!"
}
```

## Using Config with several config files

```python
from conftastic import Config

config = Config()

# Loading from settings.json:
config.from_json("settings.json")

# Loading from more_settings.json:
config.from_json("more_settings.json")

print(config)
```

`settings.json`:

```json
{
    "first": "First (settings.json)",
    "second": "Second  (settings.json)",
}
```

`more_settings.json`:

```json
{
    "second": "Second  (more_settings.json)",
    "third": "Third (more_settings.json)"
}
```

The `config` dictionary will now look like this:

```python
{
    'first': 'First (settings.json)',
    'second': 'Second  (more_settings.json)',
    'third': 'Third (more_settings.json)'
}
```

Each load of new settings will update the settings already loaded.

## Silent load of missing files

By default an exception is raised if you are trying to load a configuration file that does not exist. By passing `silent=True` to the method it will ignore the file if it cannot be found:

```python
from conftastic import Config

config = Config()

config.from_json("settings.json")
config.from_json("does_not_exist.json", silent=True)
```

## Example using Loader

```python
from conftastic import Loader, Config

loader = Loader(
    "settings.json",
    defaults={
    	"a_default_value": 123,
	}
)

loader.add_folder_path(".")

config: Config = loader.build()

print(config)  # {'a_default_value': 123, 'a_setting': 'victory!'}
```

`settings.json`:

```json
{
    "a_setting": "victory!"
}
```

You can add several folder paths. They will be looked up in the order that you have added them to the loader. 

The `build()` method of the `Loader` will throw an exception if _no_ configuration file is found. If you specify several folder paths, and a single configuration file is found, there'll be no exception raised.

You can suppress this exception by passing `silent=True` to `build()`:

```python
config = loader.build(silent=True)
```

## Using Loader with several config files

```python
from conftastic import Loader, Config

loader = Loader("settings.json")

loader.add_folder_path("defaults")
loader.add_folder_path("production")

config: Config = loader.build()

print(config)
```

`defaults/settings.json`:

```json
{
    "first": "First  (defaults)",
    "second": "Second (defaults)"
}
```

`production/settings.json`:

```json
{
    "second": "Second  (production)",
    "third": "Third (production)"
}
```

The `config` dictionary will now look like this:

```python
{
    'first': 'First (defaults)',
    'second': 'Second  (production)',
    'third': 'Third (production)'
}
```

## File types

The Loader will try to find a proper load method from the file extension. You can manually specify that:

```python
from conftastic import Loader, Config

loader = Loader("settings.abc", "json")

loader.add_folder_path(".")

config: Config = loader.build()
```

Supported values:

* json
* toml
* yaml
* ini
* env

## Using Loader with appdirs

[appdirs](https://github.com/ActiveState/appdirs) is a nice little utility to find paths on the system. Here's an example:

```python
from conftastic import Loader, Config
import appdirs

loader = Loader("settings.json")

loader.add_folder_path(".")
loader.add_folder_path(appdirs.user_config_dir("my-project"))

config: Config = loader.build()
```

On a Linux system, that will add the following folder path: `~/.config/my-project`. appdirs is platform independent - that's the beauty of it.

## Using the from_file() method

When loading a JSON file, the `from_file()` is called behind the scenes. We can create our own version. Maybe you prefer the more stricter `json` package, or maybe you have another loader/file format you want to use:

```python
import json
from conftastic import Config

config = Config()

config.from_file("settings.json", json.load)
```

## Dotenv

```python
from conftastic import Config

config = Config()

config.from_dotenv()

print(config)  # {'HELLO': 'world'}
```

`.env`:

```
HELLO=world
```

You can also specify the name of the dotenv file:

```python
config.from_dotenv(".my-env")
```

## Environment variables

```python
from conftastic import Config

config = Config()

config.from_environment("MY_COOL_APP")

print(config)
```

And in the terminal:

```python
> set MY_COOL_APP_EXAMPLE ohyes
> python3 my_cool_app.py
{'EXAMPLE': 'ohyes'}
```

The parameter sent to `from_environment()` is the prefix that shall be looked for. The prefix is stripped when added to the configuration.

## Passing Config to Loader as defaults

Since loading settings from environment variables is only working on the `Config` object, you are forced (sort of, we are coming to that later) to do like this:

```python
from conftastic import Loader, Config
import appdirs

loader = Loader("settings.json")

loader.add_folder_path(".")

config: Config = loader.build()
    
config.from_environment("MY_COOL_APP")
```

But what  happens if you want to have these settings as defaults, and let the setting file(s) have higher priority?

To our rescue, the `Config` is a dictionary, so we can pass it to the `Loader`:

```python
from conftastic import Loader, Config
import appdirs

loader = Loader(
    "settings.json",
    defaults=Config().from_environment("MY_COOL_APP_DEFAULTS")
)

loader.add_folder_path(".")

config: Config = loader.build()
```

## Config.get_recursive()

It's quite common that you have sub-dictionaries in your settings. You can use `get_recursive()` to fetch settings any level deep:

```python
from conftastic import Config

config = Config({
    "database": {
        "connection": {
            "path": "sqlite://example.db",
        }
    }
})

config.from_environment("MY_COOL_APP")

config.get_recursive(("database", "connection"))  # {'path': 'sqlite://example.db'}
config.get_recursive(("database", "connection", "path"))  # sqlite://example.db
config.get_recursive(("database", "connection", "non_existing"))  # None
config.get_recursive(
    ("database", "connection", "path"),
    "Fallback value"
)  # Fallback value
```

## Config.update()

You can also populate the configuration like a dictionary:

```python
from conftastic import Config

config = Config()

config.update(
	this="is",
    an="example",
)

config.from_json("settings.json")

config.update({
    "using": "dictionary",
    "also": "works",
})

config["this"] = "works too"
```

## Chainable

It's possible to chain the methods:

```python
from conftastic import Loader

config = (
    Loader("settings.json")
    .add_folder_path("defaults")
    .add_folder_path("production")
    .build()
    .from_environment("MY_COOL_APP")
)

print(config["a_setting"])
```

## This that are missing

* Unit tests
* Docstrings
* I think this README needs a bit more love
* PyPI package