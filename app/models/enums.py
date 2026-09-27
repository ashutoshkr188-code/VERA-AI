from enum import Enum

class ContextScope(str, Enum):
    CATEGORY = "category"
    MERCHANT = "merchant"
    TRIGGER = "trigger"
    CUSTOMER = "customer"

class TriggerScope(str, Enum):
    MERCHANT = "merchant"
    CUSTOMER = "customer"

class TriggerSource(str, Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"

class SendAs(str, Enum):
    VERA = "vera"
    MERCHANT_ON_BEHALF = "merchant_on_behalf"

class CTA(str, Enum):
    BINARY_YES_STOP = "binary_yes_stop"
    BINARY_CONFIRM_CANCEL = "binary_confirm_cancel"
    OPEN_ENDED = "open_ended"
    MULTI_CHOICE_SLOT = "multi_choice_slot"
    NONE = "none"