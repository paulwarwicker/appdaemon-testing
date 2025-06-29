from functools import wraps
from typing import Type, TypeVar, Callable, Awaitable
import pytest_asyncio
from appdaemon.plugins.hass.hassapi import Hass
from appdaemon.models.config.app import AppConfig
from ..hass_driver import HassDriver

T = TypeVar("T", bound=Hass)


def automation_fixture(App: Type[T], args=None, initialize=True) -> Callable[..., Callable[..., Awaitable[T]]]:
    """
    Configures a pytest-asyncio fixture for the given AppDaemon automation.

    Parameters:
        App: The AppDaemon app class to instantiate
        args: Optional args dict to pass to the app
        initialize: Whether to call `app.initialize()`
    """
    def decorator(fn):
        @pytest_asyncio.fixture
        @wraps(fn)
        async def inner(*_args, **_kwargs) -> T:
            # Pull HassDriver from fixture args
            # hass_driver: HassDriver = next(
            #     arg for arg in _args if isinstance(arg, HassDriver)
            # )
            hass_driver: HassDriver = _kwargs.get('hass_driver')
            if hass_driver is None:
                raise RuntimeError("Missing 'hass_driver' fixture in automation_fixture")

            hass_driver.inject_mocks()

            app_args = {
                "name": App.__name__,
                "module": App.__module__,
                "class": App.__name__,
            }
            if args is not None:
                app_args.update(args)

            app_config = AppConfig(**app_args)
            app = App(hass_driver, app_config)

            # # Call the wrapped fixture for pre-initialization config (like set_state)
            # result = fn(*_args, **_kwargs)
            # if result is not None:
            #     app = result

            await fn(*_args, **_kwargs)

            if initialize:
                await app.initialize()

            return app

        return inner

    return decorator
