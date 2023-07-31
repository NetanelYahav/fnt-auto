
import typing
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RWModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def rw_model_dump(self) -> dict[str, typing.Any]:
        return {
            **self.model_dump(by_alias=True, exclude_defaults=True), 
            **self.model_dump(by_alias=True, exclude_unset=True), 
            **self.model_dump(by_alias=True, exclude_none=True)
        }
    