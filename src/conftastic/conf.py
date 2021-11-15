from os.path import splitext, join, exists
import typing


class BaseException(Exception):
    pass


class UnknownFileType(BaseException):
    pass


class NoConfigFileFound(BaseException):
    pass


class Config(dict):
    def __init__(self, defaults: typing.Optional[dict] = None) -> None:
        dict.__init__(self, defaults or {})

    def from_file(
        self,
        filename: str,
        load: typing.Callable[[typing.IO[typing.Any]], typing.Mapping],
        silent: bool = False,
    ) -> "Config":
        if silent and not exists(filename):
            return self
        with open(filename) as f:
            self.update(load(f))
        return self

    def from_json(self, filename: str, silent: bool = False) -> "Config":
        from jstyleson import load

        self.from_file(filename, load, silent)
        return self

    def from_toml(self, filename: str, silent: bool = False) -> "Config":
        from toml import load

        self.from_file(filename, load, silent)
        return self

    def from_yaml(self, filename: str, silent: bool = False) -> "Config":
        from yaml import load

        self.from_file(filename, load, silent)
        return self

    def from_ini(self, filename: str, silent: bool = False) -> "Config":
        if silent and not exists(filename):
            return self

        from configparser import ConfigParser

        config = ConfigParser()
        config.read(filename)
        for section in config.sections():
            self[section] = dict(config[section])

        return self

    def from_dotenv(
        self,
        filename: typing.Optional[str] = None,
        silent: bool = False,
    ) -> "Config":
        if filename and not exists(filename):
            if silent:
                return self
            raise IOError("File not found")

        from dotenv import dotenv_values

        self.update(dotenv_values(filename))
        return self

    def from_environment(self, prefix: str) -> "Config":
        from os import environ

        search = prefix + "_"
        length = len(search)
        for key, value in environ.items():
            if key.startswith(search):
                self[key[length:]] = value

        return self

    def get(self, name: str, fallback: typing.Any = None) -> typing.Any:
        if name in self:
            return self[name]
        return fallback

    def get_recursive(self, setting: typing.Iterable[str], fallback=None) -> typing.Any:
        data = self
        for path in setting:
            if not isinstance(data, (dict, list)):
                return fallback
            elif isinstance(data, dict) and path not in data:
                return fallback
            elif isinstance(data, list):
                try:
                    path = int(path)
                except Exception:
                    return fallback
            try:
                data = data[path]
            except Exception:
                return fallback
        return data


class Loader(object):
    def __init__(
        self,
        filename: str,
        filetype: typing.Optional[str] = None,
        defaults: typing.Optional[dict] = None,
    ) -> None:
        self.filename = filename
        self.filetype = filetype
        self.paths: typing.List[str] = []
        self.defaults = defaults
        self._from_map = {
            "json": "from_json",
            "toml": "from_toml",
            "yaml": "from_yaml",
            "ini": "from_ini",
            "env": "from_dotenv",
        }

    def set_defaults(self, defaults: typing.Optional[dict] = None) -> "Loader":
        self.defaults = defaults
        return self

    def add_folder_path(self, path: str) -> "Loader":
        self.paths.append(path)
        return self

    def _get_filetype(self) -> str:
        filetype = self.filetype
        if not filetype:
            ext = splitext(self.filename)[1]
            if len(ext) < 1:
                raise UnknownFileType(
                    "Could not find file type from file name: " + self.filename
                )
            filetype = ext[1:]
        filetype_l = filetype.lower()
        if filetype_l not in self._from_map:
            raise UnknownFileType("Unknown file type: " + filetype)
        return filetype

    def build(self, silent: bool = False) -> Config:
        filetype = self._get_filetype()
        if not filetype in self._from_map:
            raise UnknownFileType("Unknown file type: " + filetype)
        config = Config(self.defaults)
        loader = getattr(config, self._from_map[filetype])
        config_file_found = False
        for path in self.paths:
            full_path = join(path, self.filename)
            if not exists(full_path):
                continue
            loader(full_path)
            config_file_found = True
        if not config_file_found and not silent:
            raise NoConfigFileFound("No configration file found")
        return config
