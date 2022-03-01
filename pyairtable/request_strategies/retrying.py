from typing import Any
from requests import Response
from .simple import SimpleRequestStrategy

try:
    from tenacity import Retrying
except ImportError:
    TENACITY_FOUND = False
else:
    TENACITY_FOUND = True
    from tenacity.retry import retry_if_result
    from tenacity.stop import stop_after_attempt
    from tenacity.wait import wait_random_exponential


class RetryingRequestStrategy(SimpleRequestStrategy):
    """
    Wraps SimpleRequestStrategy to retry requests.

    Accepts a tenacity.Retrying object to configure retry behavior.
    """

    _retrying: "Retrying"

    def __init__(self, retrying: "Retrying", *args: Any, **kwargs: Any):
        """
        If tenacity is installed, initialize the strategy.

        Accepts a tenacity.Retrying object for more fine-grained control.
        """
        if not TENACITY_FOUND:
            raise ModuleNotFoundError(
                """
                Could not find the tenacity module! Please install pyairtable
                with the tenacity extra. You can do so with:
                    $ pip install pyairtable[tenacity]
                """
            )
        super().__init__(*args, **kwargs)
        if retrying is None or not isinstance(retrying, Retrying):
            raise ValueError("Must provide a Retrying object as a strategy!")
        self.retrying = retrying

    @property
    def retrying(self) -> "Retrying":
        """Return the tenacity.Retrying object that wraps _request."""
        return self._retrying

    @retrying.setter
    def retrying(self, retrying: "Retrying"):
        """Set the tenacity.Retrying and update the wrapped _request method."""
        self._retrying = retrying
        self._retrying_request = retrying.wraps(super()._request)

    def _request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Make requests and retry based on the response code."""
        if self._retrying_request is None:
            return self._request(method, url, **kwargs)
        return self._retrying_request(method, url, **kwargs)


class RateLimitRetryingRequestStrategy(RetryingRequestStrategy):
    """
    Wraps SimpleRequestStrategy to retry requests based on response code.

    Airtable responds with a 429 if a request fails due to exceeding rate
    limits. We can implement the strategy used by the official airtable.js and
    retry with exponential and jittered backoff. See
    https://github.com/Airtable/airtable.js/blob/9d40666979af77de9546d43177cab086a03028bf/src/run_action.ts#L70-L75

    The API requires a wait of 30s after the rate limits are exceeded.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """Mimics the behavior of the offial airtable.js library."""
        if not TENACITY_FOUND:
            raise ModuleNotFoundError(
                """
                Could not find the tenacity module! Please install pyairtable
                with the tenacity extra. You can do so with:
                    $ pip install pyairtable[tenacity]
                """
            )
        rate_limit_retrying = Retrying(
            retry=retry_if_result(lambda r: r.status_code == 429),
            stop=stop_after_attempt(max_attempt_number=3),
            wait=wait_random_exponential(multiplier=30, max=480),
        )
        super().__init__(rate_limit_retrying, *args, **kwargs)
