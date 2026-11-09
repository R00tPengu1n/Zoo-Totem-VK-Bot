import asyncio
import logging
from pathlib import Path

import aiohttp
import pytest
from vkbottle import VKAPIError

from bot.services import photos
from bot.services.content import Animal
from bot.services.photos import PhotoService, PhotoUploadError


class FlakyUploadService(PhotoService):
    """PhotoService, у которого загрузка падает заданное число раз."""

    def __init__(self, failures: int) -> None:
        super().__init__(api=None, repository=None, images_dir=Path("."))
        self.failures = failures
        self.calls = 0

    async def _upload(self, path: Path, peer_id: int) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise PhotoUploadError("VK не принял файл")
        return "photo-1_2"


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(photos, "RETRY_DELAY", 0)


def test_upload_succeeds_after_transient_errors():
    service = FlakyUploadService(failures=photos.UPLOAD_ATTEMPTS - 1)

    attachment = asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))

    assert attachment == "photo-1_2"
    assert service.calls == photos.UPLOAD_ATTEMPTS


def test_upload_gives_up_after_all_attempts():
    service = FlakyUploadService(failures=photos.UPLOAD_ATTEMPTS)

    with pytest.raises(PhotoUploadError):
        asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))
    assert service.calls == photos.UPLOAD_ATTEMPTS


def test_unexpected_error_is_not_retried():
    class BrokenService(FlakyUploadService):
        async def _upload(self, path: Path, peer_id: int) -> str:
            self.calls += 1
            raise FileNotFoundError(path)

    service = BrokenService(failures=0)

    with pytest.raises(FileNotFoundError):
        asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))
    assert service.calls == 1


@pytest.mark.parametrize(
    "error",
    [
        VKAPIError[10](error_msg="Internal server error"),
        aiohttp.ClientConnectionError("reset"),
        aiohttp.ServerTimeoutError("timeout"),
        TimeoutError(),
    ],
    ids=["vk_api_error", "client_error", "server_timeout", "timeout"],
)
def test_every_transient_error_is_retried(error):
    class Service(FlakyUploadService):
        async def _upload(self, path: Path, peer_id: int) -> str:
            self.calls += 1
            if self.calls == 1:
                raise error
            return "photo-1_2"

    service = Service(failures=0)

    assert asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0)) == "photo-1_2"
    assert service.calls == 2


@pytest.mark.parametrize("code", [1, 6, 9, 10])
def test_temporary_vk_errors_are_retried(code):
    class Service(FlakyUploadService):
        async def _upload(self, path: Path, peer_id: int) -> str:
            self.calls += 1
            if self.calls == 1:
                raise VKAPIError[code](error_msg="temporary")
            return "photo-1_2"

    service = Service(failures=0)

    assert asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0)) == "photo-1_2"
    assert service.calls == 2


@pytest.mark.parametrize("code", [5, 15, 100])
def test_permanent_vk_errors_are_not_retried(code):
    class Service(FlakyUploadService):
        async def _upload(self, path: Path, peer_id: int) -> str:
            self.calls += 1
            raise VKAPIError[code](error_msg="permanent")

    service = Service(failures=0)

    with pytest.raises(VKAPIError):
        asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))
    assert service.calls == 1


def test_retry_waits_between_attempts(monkeypatch):
    monkeypatch.setattr(photos, "RETRY_DELAY", 0.5)
    delays: list[float] = []

    async def fake_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(photos.asyncio, "sleep", fake_sleep)
    service = FlakyUploadService(failures=photos.UPLOAD_ATTEMPTS)

    with pytest.raises(PhotoUploadError):
        asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))
    # Пауза между попытками, после последней попытки паузы нет
    assert delays == [0.5] * (photos.UPLOAD_ATTEMPTS - 1)


def test_single_attempt_setting_means_no_retry(monkeypatch):
    monkeypatch.setattr(photos, "UPLOAD_ATTEMPTS", 1)
    service = FlakyUploadService(failures=1)

    with pytest.raises(PhotoUploadError):
        asyncio.run(service._upload_with_retry(Path("lion.jpg"), peer_id=0))
    assert service.calls == 1


# --- get_attachment и preload: кэш и ошибки отдельных животных ---


def make_animal(animal_id: str) -> Animal:
    return Animal(
        id=animal_id,
        name=animal_id,
        headline="h",
        description="d",
        fact="f",
        image=f"{animal_id}.jpg",
    )


class FakeRepository:
    def __init__(self, cached: dict[str, str] | None = None) -> None:
        self.cached = dict(cached or {})
        self.saved: list[tuple[str, str, str]] = []

    async def get_cached_photo(self, animal_id: str, file_hash: str) -> str | None:
        return self.cached.get(animal_id)

    async def save_cached_photo(self, animal_id: str, file_hash: str, attachment: str) -> None:
        self.saved.append((animal_id, file_hash, attachment))
        self.cached[animal_id] = attachment


class RecordingService(PhotoService):
    """Загрузка без сети: животные из `broken` всегда падают."""

    def __init__(self, repository, images_dir: Path, broken=()) -> None:
        super().__init__(api=None, repository=repository, images_dir=images_dir)
        self.broken = set(broken)
        self.uploaded: list[str] = []
        self.peer_ids: list[int] = []

    async def _upload(self, path: Path, peer_id: int) -> str:
        self.uploaded.append(path.stem)
        self.peer_ids.append(peer_id)
        if path.stem in self.broken:
            raise PhotoUploadError("VK не принял файл")
        return f"photo-1_{path.stem}"


@pytest.fixture
def images(tmp_path):
    for name in ("lion", "tiger", "bear"):
        (tmp_path / f"{name}.jpg").write_bytes(name.encode())
    return tmp_path


def preload_log(caplog) -> str:
    return [r.getMessage() for r in caplog.records if "Предзагрузка" in r.getMessage()][-1]


def test_preload_continues_after_one_animal_fails(images, caplog):
    repository = FakeRepository()
    service = RecordingService(repository, images, broken={"tiger"})
    animals = [make_animal(name) for name in ("lion", "tiger", "bear")]

    with caplog.at_level(logging.INFO, logger="bot.services.photos"):
        asyncio.run(service.preload(animals))

    assert [saved[0] for saved in repository.saved] == ["lion", "bear"]
    assert service.uploaded.count("tiger") == photos.UPLOAD_ATTEMPTS
    assert set(service.peer_ids) == {0}
    assert preload_log(caplog) == "Предзагрузка фото завершена: готово 2 из 3"


def test_preload_skips_cached_photos(images, caplog):
    repository = FakeRepository(cached={"lion": "photo-1_old"})
    service = RecordingService(repository, images)

    with caplog.at_level(logging.INFO, logger="bot.services.photos"):
        asyncio.run(service.preload([make_animal("lion"), make_animal("bear")]))

    assert service.uploaded == ["bear"]
    assert preload_log(caplog) == "Предзагрузка фото завершена: готово 2 из 2"


def test_preload_missing_file_is_counted_as_failed(images, caplog):
    service = RecordingService(FakeRepository(), images)

    with caplog.at_level(logging.INFO, logger="bot.services.photos"):
        asyncio.run(service.preload([make_animal("lion"), make_animal("ghost")]))

    assert service.uploaded == ["lion"]
    assert preload_log(caplog) == "Предзагрузка фото завершена: готово 1 из 2"


def test_preload_empty_list(images, caplog):
    service = RecordingService(FakeRepository(), images)

    with caplog.at_level(logging.INFO, logger="bot.services.photos"):
        asyncio.run(service.preload([]))

    assert service.uploaded == []
    assert preload_log(caplog) == "Предзагрузка фото завершена: готово 0 из 0"


def test_preload_accepts_generator(images, caplog):
    service = RecordingService(FakeRepository(), images)

    with caplog.at_level(logging.INFO, logger="bot.services.photos"):
        asyncio.run(service.preload(make_animal(name) for name in ("lion", "bear")))

    assert preload_log(caplog) == "Предзагрузка фото завершена: готово 2 из 2"


def test_second_request_uses_cache(images):
    service = RecordingService(FakeRepository(), images)
    lion = make_animal("lion")

    async def scenario():
        first = await service.get_attachment(lion, peer_id=0)
        second = await service.get_attachment(lion, peer_id=0)
        return first, second

    assert asyncio.run(scenario()) == ("photo-1_lion", "photo-1_lion")
    assert service.uploaded == ["lion"]


def test_concurrent_requests_upload_once(images):
    service = RecordingService(FakeRepository(), images)
    lion = make_animal("lion")

    async def scenario():
        return await asyncio.gather(*(service.get_attachment(lion, peer_id=0) for _ in range(5)))

    assert asyncio.run(scenario()) == ["photo-1_lion"] * 5
    assert service.uploaded == ["lion"]


def test_cache_failure_returns_none(images):
    class BrokenRepository(FakeRepository):
        async def get_cached_photo(self, animal_id, file_hash):
            raise RuntimeError("database is locked")

    service = RecordingService(BrokenRepository(), images)

    assert asyncio.run(service.get_attachment(make_animal("lion"), peer_id=0)) is None
    assert service.uploaded == []


def test_preload_cancellation_propagates(images):
    # Бот при остановке отменяет фоновую задачу: отмена не должна глотаться
    class SlowService(RecordingService):
        async def _upload(self, path: Path, peer_id: int) -> str:
            await asyncio.sleep(10)
            return "never"

    service = SlowService(FakeRepository(), images)

    async def scenario():
        task = asyncio.create_task(service.preload([make_animal("lion")]))
        await asyncio.sleep(0.01)
        task.cancel()
        await task

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(scenario())
