from typing import Any, Dict, Optional, Tuple, Union
from requests import Response, Session
from .abstract import RequestStrategy, Headers, process_response


class SimpleRequestStrategy(RequestStrategy):
    """Simple request strategy that manages timeouts & headers."""

    session: Session
    _timeout: Optional[Union[float, Tuple[int, int]]]

    def __init__(
        self,
        session: Optional[Session] = None,
    ):
        """Create a new instance."""
        if session is None:
            session = Session()
        self.session = session

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        timeout: Optional[Tuple[int, int]],
        headers: Headers,
    ) -> Any:
        """Make a request using the session."""
        response = self._request(
            method,
            url,
            params=params,
            json=json,
            timeout=timeout,
            headers=headers,
        )
        return process_response(response)

    def _request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Make a request using the session."""
        return self.session.request(method, url, **kwargs)
