import logging
from typing import List
from scales import Scale

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Catalog:
    def __init__(self):
        """
        Initializes the Catalog with an empty list of scales.
        """
        self.scales: List[Scale] = []
        logger.info("Catalog initialized with an empty list of scales.")

    def add_scale(self, scale: Scale) -> None:
        """
        Adds a new scale to the catalog.

        :param scale: Scale instance to add
        """
        self.scales.append(scale)
        logger.info(f"Scale '{scale.name}' added to the catalog.")

    def remove_scale(self, scale_name: str) -> bool:
        """
        Removes a scale from the catalog by name.

        :param scale_name: Name of the scale to remove
        :return: True if removed, False if not found
        """
        for scale in self.scales:
            if scale.name == scale_name:
                self.scales.remove(scale)
                logger.info(f"Scale '{scale_name}' removed from the catalog.")
                return True
        logger.warning(f"Scale '{scale_name}' not found in the catalog for removal.")
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
                logger.info(f"Scale '{scale_name}' retrieved from the catalog.")
                return scale
        logger.error(f"Scale '{scale_name}' not found in catalog.")
        raise ValueError(f"Scale '{scale_name}' not found in catalog.")