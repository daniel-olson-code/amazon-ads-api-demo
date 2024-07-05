import msgspec
import io
from typing import Self, Union, Callable


def is_class(obj):
    """
    Check if the given object is a class.

    Args:
        obj: The object to check.

    Returns:
        bool: True if the object is a class, False otherwise.
    """
    return str(type(obj)).startswith("<class")


class JsonObject(msgspec.Struct):
    """
    A base class for JSON-serializable objects with utility methods for manipulation and serialization.

    This class extends msgspec.Struct and provides methods for creating, manipulating,
    and serializing JSON-like objects.
    """

    @classmethod
    def create(cls, values: dict):
        """
        Create a new instance of the class and populate it with the given values.

        Args:
            values (dict): A dictionary of attribute names and values to set on the new instance.

        Returns:
            An instance of the class with the given values set.
        """
        instance = cls()
        instance.absorb(values)
        return instance

    def unroll_kwargs(self, kwargs):
        """
        Recursively unroll nested dictionaries and lists, converting JsonObjects to their JSON representation.

        Args:
            kwargs (Union[list, dict]): The input structure to unroll.

        Returns:
            Union[list, dict]: The unrolled structure with JsonObjects converted to their JSON representation.
        """
        if isinstance(kwargs, (list, dict)):
            for key, value in (enumerate(kwargs) if isinstance(kwargs, list) else kwargs.items()):
                if isinstance(value, (dict, list)):
                    kwargs[key] = self.unroll_kwargs(value)
                if isinstance(value, JsonObject):
                    kwargs[key] = value.cjson
        return kwargs

    def absorb(self, new_data, allow_none=False):
        """
        Update the current instance with values from another object or dictionary.

        Args:
            new_data (Union[dict, Self]): The source of new values.
            allow_none (bool, optional): If True, allow None values to be set. Defaults to False.
        """
        obj = JsonObject.json_to_object(
            (new_data if not isinstance(new_data, self.__class__) else new_data.json),
            self.__class__)
        for attr, _ in self.__annotations__.items():
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                if value is not None or allow_none:
                    setattr(self, attr, getattr(obj, attr))

    def catch(self, attributes: set, refuse_none_type=False):
        """
        Retrieve specified attributes from the object.

        Args:
            attributes (set): A set of attribute names to retrieve.
            refuse_none_type (bool, optional): If True, exclude None values. Defaults to False.

        Returns:
            dict: A dictionary of the specified attributes and their values.
        """
        result = {}
        for attr in attributes:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value is None and refuse_none_type:
                    continue
                result[attr] = value
        return result

    def obj(self, keys=None, convert=None, **additional_keys):
        """
        Create a dictionary representation of the object with specified keys.

        Args:
            keys (Union[tuple, set, list], optional): Keys to include in the output.
            convert (dict, optional): A dictionary to map old keys to new keys.
            **additional_keys: Additional key-value pairs to include in the output.

        Returns:
            dict: A dictionary representation of the object with the specified keys.
        """
        convert = convert if isinstance(convert, dict) else {}
        keys = [*([] if not isinstance(keys, (tuple, set, list)) else keys), *additional_keys.keys()]
        result = {}
        for key in keys:
            new_key = convert.get(key, key)
            result[new_key] = getattr(self, key, additional_keys.get(key))
        return result

    def decode(self):
        """
        Placeholder method for decoding. To be implemented by subclasses if needed.
        """
        return

    @property
    def json(self):
        """
        Generate a JSON-compatible dictionary representation of the object.

        Returns:
            dict: A JSON-compatible dictionary of the object's attributes.
        """
        def check_for_json_object(val):
            if is_class(val):
                if issubclass(val.__class__, JsonObject):
                    return val.cjson
            return val

        result = {}
        for attr in self.__annotations__.keys():
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value is not None:
                    if isinstance(value, list):
                        value = [check_for_json_object(item) for item in value]
                    elif isinstance(value, dict):
                        value = {k: check_for_json_object(v) for k, v in value.items()}
                    else:
                        value = check_for_json_object(value)

                    result[attr] = value  # self.secure_type(value, self.__annotations__[attr])
        return result

    def from_json(self, json_data):
        """
        Create an instance of the class from a JSON-compatible dictionary.

        Args:
            json_data (dict): A JSON-compatible dictionary.

        Returns:
            Self: An instance of the class populated with the data from the input dictionary.
        """
        return msgspec.json.decode(msgspec.json.encode(json_data), type=type(self))

    @property
    def clone(self) -> Self:
        """
        Create a deep copy of the object.

        Returns:
            Self: A new instance of the class with the same attribute values.
        """
        return self.from_json(self.json)

    @staticmethod
    def json_to_object(json_data, target_class) -> Self:
        """
        Create an instance of the specified class from a JSON-compatible dictionary.

        Args:
            json_data (dict): A JSON-compatible dictionary.
            target_class (type): The class to instantiate.

        Returns:
            Self: An instance of target_class populated with the data from the input dictionary.
        """
        return msgspec.json.decode(msgspec.json.encode(json_data), type=target_class)

    def save(self, destination: Union[str, io.BytesIO, Callable]) -> None:
        """
        Save the object's JSON representation to a file, BytesIO object, or via a callable.

        Args:
            destination (Union[str, io.BytesIO, Callable]): The destination for the JSON data.

        Raises:
            TypeError: If the input is not a string, BytesIO object, or callable.
        """
        json_data = msgspec.json.encode(self.json)
        if isinstance(destination, str):
            with open(destination, 'wb') as f:
                f.write(json_data)
        elif isinstance(destination, io.BytesIO):
            destination.write(json_data)
        elif callable(destination):
            destination(json_data)
        else:
            print(f"Didn't save. {destination} of type {type(destination)} must be str, io.BytesIO or callable")

    @classmethod
    def class_load(cls, source: Union[str, Callable, io.BytesIO]) -> Self:
        """
        Load a saved JSON representation and create a new instance of the class.

        Args:
            source (Union[str, Callable, io.BytesIO]): The source of the JSON data.

        Returns:
            Self: A new instance of the class populated with the loaded data.

        Raises:
            TypeError: If the input is not a string, BytesIO object, or callable returning bytes.
        """
        if isinstance(source, str):
            with open(source, 'rb') as f:
                data = f.read()
        elif isinstance(source, io.BytesIO):
            data = source.read()
        elif callable(source):
            data = source()
        else:
            raise TypeError(f'source must be str, io.BytesIO or callable returning bytes, not {type(source)}')
        return msgspec.json.decode(data, type=cls)

    def load(self, source: Union[str, Callable]) -> None:
        """
        Load a saved JSON representation and update the current instance.

        Args:
            source (Union[str, Callable]): The source of the JSON data.
        """
        self.absorb(self.class_load(source))


