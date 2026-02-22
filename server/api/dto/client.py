from server.api.dto.extended_model import ExtendedBaseModel


class ClientProxyRequest(ExtendedBaseModel):
    """Запрос на добавление клиента: telegram_id как ключ в [access.users], secret как значение."""
    telegram_id: str
    secret: str


class ClientsProxyRequest(ExtendedBaseModel):
    clients: list[ClientProxyRequest]


class ClientRemoveRequest(ExtendedBaseModel):
    """Запрос на удаление клиента по telegram_id."""
    telegram_id: str


class RemoveClientsRequest(ExtendedBaseModel):
    clients: list[ClientRemoveRequest]
