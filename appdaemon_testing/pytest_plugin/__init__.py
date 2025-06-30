from unittest import mock
import inspect
import pytest_asyncio
from unittest.mock import AsyncMock
from typing import TypeVar, Callable
from appdaemon.plugins.hass.hassapi import Hass
from appdaemon.app_management import AppConfig
from appdaemon_testing.hass_driver import HassDriver

T = TypeVar("T")


def automation_fixture(App: type[Hass], initialize: bool = True, **args) -> Callable[..., T]:
    def decorator(fn: Callable[..., T]) -> pytest_asyncio.fixture:
        @pytest_asyncio.fixture
        async def inner(request, hass_driver: HassDriver):
            hass_driver.inject_mocks()

            # Patch required AppDaemon APIs for legacy app compatibility
            if not hasattr(hass_driver, "config"):
                hass_driver.config = mock.Mock()

            if not hasattr(hass_driver, "state"):
                hass_driver.state = mock.Mock()
                hass_driver.state.namespace_exists.return_value = True

            if not hasattr(hass_driver, "plugins"):
                hass_driver.plugins = mock.Mock()
                hass_driver.plugins.get_plugin_object.return_value = mock.Mock()

            if not hasattr(hass_driver, "http"):
                hass_driver.http = mock.Mock()

            if not hasattr(hass_driver, "logging"):
                hass_driver.logging = mock.Mock()
                hass_driver.logging.get_child.return_value = mock.Mock()

            if not hasattr(hass_driver, "events"):
                hass_driver.events = mock.Mock()
                hass_driver.events.listen_event = AsyncMock()
                hass_driver.logging.get_child.return_value = mock.Mock()

            if not hasattr(hass_driver, "services"):
                hass_driver.services = mock.Mock()
                hass_driver.services.register_service = AsyncMock()
                hass_driver.services.call_service = AsyncMock()

            if not hasattr(hass_driver, "state"):
                hass_driver.state = mock.Mock()
                hass_driver.state.namespace_exists.return_value = True
                hass_driver.state.get_state = AsyncMock(return_value="on")  # or whatever value you expect

            app_args = {
                "name": App.__name__,
                "module": App.__module__,
                "class": App.__name__,
            }
            if args:
                app_args.update(args)

            app_config = AppConfig(**app_args)
            app: Hass = App(hass_driver, app_config)

            if initialize:
                result = app.initialize()
                if inspect.isawaitable(result):
                    await result

            # If user fixture accepts hass_driver, pass it through
            if "hass_driver" in inspect.signature(fn).parameters:
                result = fn(hass_driver=hass_driver)
            else:
                result = fn()

            if inspect.isawaitable(result):
                await result

            return app

        return inner

    return decorator


# from functools import wraps
# from typing import Type, TypeVar, Callable, Awaitable
# import pytest_asyncio
# import inspect
# from unittest import mock
# from appdaemon.plugins.hass.hassapi import Hass
# from appdaemon.models.config.app import AppConfig
# from ..hass_driver import HassDriver

# # T = TypeVar("T", bound=Hass)


# # def automation_fixture(App: Type[T], args=None, initialize=True) -> Callable[..., Callable[..., Awaitable[T]]]:
# def automation_fixture(App, args=None, initialize=True):
#     def decorator(fn):
#         @pytest_asyncio.fixture
#         async def inner(request, hass_driver: HassDriver):
#             hass_driver.inject_mocks()

#             # Ensure compatibility with ADBase/Hass expectations
#             if not hasattr(hass_driver, "config"):
#                 hass_driver.config = mock.Mock()
#                 hass_driver.config.model_dump.return_value = {}

#             app_args = {
#                 "name": App.__name__,
#                 "module": App.__module__,
#                 "class": App.__name__,
#             }
#             if args:
#                 app_args.update(args)

#             app_config = AppConfig(**app_args)
#             app: Hass = App(hass_driver, app_config)

#             # Safely inspect if the user fixture wants hass_driver
#             if "hass_driver" in inspect.signature(fn).parameters:
#                 await fn(hass_driver=hass_driver)
#             else:
#                 await fn()

#             if initialize:
#                 await app.initialize()

#             return app
#         return inner
#     return decorator
