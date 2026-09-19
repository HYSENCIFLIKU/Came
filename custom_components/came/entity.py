"""Base entity for the Came Eti Domo integration."""
from __future__ import annotations
from typing import Any
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import MANUFACTURER
from .coordinator import CameCoordinator

class CameEntity(CoordinatorEntity[CameCoordinator]):
    """Base class for CAME entities."""
    _attr_has_entity_name = False
    def __init__(self, coordinator: CameCoordinator, data_key: str, item_id: Any) -> None:
        super().__init__(coordinator)
        self._data_key = data_key
        self._id = item_id
    @property
    def _item(self) -> dict | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key, {}).get(self._id)
    @property
    def available(self) -> bool:
        return super().available and self._item is not None
    @property
    def device_info(self):
        return {"identifiers": {("came", str(self._id), self._data_key)}, "manufacturer": MANUFACTURER, "name": self._attr_name}
    def _optimistic_update(self, **changes: Any) -> None:
        if self.coordinator.data is None:
            return
        data = self.coordinator.data
        items = data.get(self._data_key)
        if items is None:
            return
        item = items.get(self._id)
        if item is None:
            return
        new_item = dict(item); new_item.update(changes)
        new_items = dict(items); new_items[self._id] = new_item
        new_data = dict(data); new_data[self._data_key] = new_items
        self.coordinator.async_set_updated_data(new_data)
