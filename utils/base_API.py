import requests
import enum
from typing import TypeVar, Type, Optional
from utils.models.response import ResponseSchema
from pydantic import BaseModel,TypeAdapter



class APIMethods(enum.Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"


def parse_as_type[T](json_text: str, model_type: Type[BaseModel]) -> T:
    type_adapter = TypeAdapter(model_type)
    return type_adapter.validate_json(json_text)


class BaseApi:
    def __init__(self, url):
        self.base_url = url

    T = TypeVar('T')

    def send[T](self,
                method: APIMethods,
                endpoint: str = None,
                headers: dict = None,
                params: dict = None,
                data=None,
                json=None,
                model_type: Optional[Type[T]] = None,
                url: str = None,
                **kwargs) -> ResponseSchema[T]:
        session = requests.Session()
        final_url = url if url else self.base_url + endpoint if endpoint else self.base_url
        response = session.request(method=method.value, url=final_url, headers=headers,
                                   params=params, data=data, json=json, **kwargs)

        response.raise_for_status()
        parsed_model = parse_as_type(response.text, model_type) if model_type else None
        return ResponseSchema(raw=response, data=parsed_model)


    def get(self, endpoint: str = None, headers: dict = None, params: dict = None, model_type=None, **kwargs):
        return self.send(APIMethods.GET, endpoint, headers, params, model_type=model_type, **kwargs)

    def post(self, endpoint: str = None, headers: dict = None, params: dict = None,
             json=None, data=None, **kwargs):
        return self.send(APIMethods.POST, endpoint, headers, params, json=json, data=data, model_type=None, **kwargs)

    def put(self, endpoint=None, data=None, params=None, **kwargs):
        return self.send(APIMethods.PUT, endpoint=endpoint, params=params, data=data, model_type=None, **kwargs)

    def delete(self, endpoint = None, headers=None, params=None):
        response = self.send(APIMethods.DELETE, endpoint=endpoint, headers=headers, params=params)
        return response
