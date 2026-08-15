# -*- coding: utf-8 -*-
"""Registry 發布。payload 組裝屬 NX-07；本模組只驗證與安全寫入。"""
from loopflow.features.registry.publisher import publish_registry
from loopflow.features.registry.validate import validate_payload

__all__ = ["publish_registry", "validate_payload"]
