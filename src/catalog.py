from collections import defaultdict
from typing import List
from scales import Scale


class Catalog:
    def __init__(self):
        """
        Initializes the Catalog with an empty list of scales.
        """
        self.scales: List[Scale] = []

    def add_scale(self, scale: Scale) -> None:
        """
        Adds a new scale to the catalog.

        :param scale: Scale instance to add
        """
        self.scales.append(scale)

    def remove_scale(self, scale_name: str) -> bool:
        """
        Removes a scale from the catalog by name.

        :param scale_name: Name of the scale to remove
        :return: True if removed, False if not found
        """
        for scale in self.scales:
            if scale.name == scale_name:
                self.scales.remove(scale)
                return True
        return False

    def get_scale(self, scale_name: str) -> Scale:
        """
        Retrieves a scale by name.

        :param scale_name: Name of the scale to retrieve
        :return: Scale instance
        :raises ValueError: If scale not found
        """
        for scale in self.scales:
            if scale.name == scale_name:
                return scale
        raise ValueError(f"Scale '{scale_name}' not found in catalog.")