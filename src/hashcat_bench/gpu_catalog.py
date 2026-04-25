"""Vast.ai GPU catalog. Names match Vast.ai's search filter exactly."""

GPU_FAMILIES: dict[str, list[dict]] = {
    # Consumer - RTX 50 Series (Blackwell)
    "rtx-50": [
        {"name": "RTX 5090", "family": "Blackwell"},
        {"name": "RTX 5080", "family": "Blackwell"},
        {"name": "RTX 5070 Ti", "family": "Blackwell"},
        {"name": "RTX 5070", "family": "Blackwell"},
        {"name": "RTX 5060 Ti", "family": "Blackwell"},
        {"name": "RTX 5060", "family": "Blackwell"},
    ],
    # Consumer - RTX 40 Series (Ada Lovelace)
    "rtx-40": [
        {"name": "RTX 4090 D", "family": "Ada Lovelace"},
        {"name": "RTX 4090", "family": "Ada Lovelace"},
        {"name": "RTX 4080 Super", "family": "Ada Lovelace"},
        {"name": "RTX 4080", "family": "Ada Lovelace"},
        {"name": "RTX 4070 Ti Super", "family": "Ada Lovelace"},
        {"name": "RTX 4070 Ti", "family": "Ada Lovelace"},
        {"name": "RTX 4070 Super", "family": "Ada Lovelace"},
        {"name": "RTX 4070", "family": "Ada Lovelace"},
        {"name": "RTX 4060 Ti", "family": "Ada Lovelace"},
        {"name": "RTX 4060", "family": "Ada Lovelace"},
    ],
    # Consumer - RTX 30 Series (Ampere)
    "rtx-30": [
        {"name": "RTX 3090 Ti", "family": "Ampere"},
        {"name": "RTX 3090", "family": "Ampere"},
        {"name": "RTX 3080 Ti", "family": "Ampere"},
        {"name": "RTX 3080", "family": "Ampere"},
        {"name": "RTX 3070 Ti", "family": "Ampere"},
        {"name": "RTX 3070", "family": "Ampere"},
        {"name": "RTX 3060 Ti", "family": "Ampere"},
        {"name": "RTX 3060", "family": "Ampere"},
        {"name": "RTX 3050", "family": "Ampere"},
    ],
    # Consumer - RTX 20 Series (Turing)
    "rtx-20": [
        {"name": "RTX 2080 Ti", "family": "Turing"},
        {"name": "RTX 2080 Super", "family": "Turing"},
        {"name": "RTX 2080", "family": "Turing"},
        {"name": "RTX 2070 Super", "family": "Turing"},
        {"name": "RTX 2070", "family": "Turing"},
        {"name": "RTX 2060 Super", "family": "Turing"},
        {"name": "RTX 2060", "family": "Turing"},
    ],
    # Consumer - GTX 16 Series (Turing)
    "gtx-16": [
        {"name": "GTX 1660 Ti", "family": "Turing"},
        {"name": "GTX 1660 Super", "family": "Turing"},
        {"name": "GTX 1660", "family": "Turing"},
        {"name": "GTX 1650 Ti", "family": "Turing"},
        {"name": "GTX 1650 Super", "family": "Turing"},
        {"name": "GTX 1650", "family": "Turing"},
    ],
    # Consumer - GTX 10 Series (Pascal)
    "gtx-10": [
        {"name": "GTX 1080 Ti", "family": "Pascal"},
        {"name": "GTX 1080", "family": "Pascal"},
        {"name": "GTX 1070 Ti", "family": "Pascal"},
        {"name": "GTX 1070", "family": "Pascal"},
        {"name": "GTX 1060", "family": "Pascal"},
        {"name": "GTX 1050 Ti", "family": "Pascal"},
        {"name": "GTX 1050", "family": "Pascal"},
    ],
    # Consumer - GTX 900 Series (Maxwell)
    "gtx-900": [
        {"name": "GTX 980 Ti", "family": "Maxwell"},
        {"name": "GTX 980", "family": "Maxwell"},
        {"name": "GTX 970", "family": "Maxwell"},
        {"name": "GTX 960", "family": "Maxwell"},
    ],
    # Consumer - GTX 700 Series (Kepler/Maxwell)
    "gtx-700": [
        {"name": "GTX 750 Ti", "family": "Maxwell"},
        {"name": "GTX 750", "family": "Maxwell"},
    ],
    # Workstation - RTX PRO Blackwell
    "rtx-pro-blackwell": [
        {"name": "RTX PRO 6000 Blackwell Workstation", "family": "Blackwell"},
        {"name": "RTX PRO 6000 Blackwell Server", "family": "Blackwell"},
        {"name": "RTX PRO 5000 Blackwell", "family": "Blackwell"},
        {"name": "RTX PRO 4500 Blackwell", "family": "Blackwell"},
        {"name": "RTX PRO 4000 Blackwell", "family": "Blackwell"},
    ],
    # Workstation - RTX Ada Generation
    "rtx-ada": [
        {"name": "RTX 6000 Ada Generation", "family": "Ada Lovelace"},
        {"name": "RTX 5880 Ada Generation", "family": "Ada Lovelace"},
        {"name": "RTX 5000 Ada Generation", "family": "Ada Lovelace"},
        {"name": "RTX 4500 Ada Generation", "family": "Ada Lovelace"},
        {"name": "RTX 4000 Ada Generation", "family": "Ada Lovelace"},
    ],
    # Workstation - RTX Ax000 Series
    "rtx-ax000": [
        {"name": "RTX A6000", "family": "Ampere"},
        {"name": "RTX A5000", "family": "Ampere"},
        {"name": "RTX A4500", "family": "Ampere"},
        {"name": "RTX A4000", "family": "Ampere"},
        {"name": "RTX A2000", "family": "Ampere"},
    ],
    # Datacenter - H-series
    "h-series": [
        {"name": "H200 NVL", "family": "Hopper"},
        {"name": "H200 SXM", "family": "Hopper"},
        {"name": "H100 NVL", "family": "Hopper"},
        {"name": "H100 PCIe", "family": "Hopper"},
        {"name": "H100 SXM", "family": "Hopper"},
        {"name": "GH200 SXM", "family": "Hopper"},
        {"name": "B200", "family": "Blackwell"},
    ],
    # Datacenter - A100 Series
    "a100": [
        {"name": "A800 PCIe", "family": "Ampere"},
        {"name": "A100 PCIe", "family": "Ampere"},
        {"name": "A100 SXM4", "family": "Ampere"},
        {"name": "A100 SXM", "family": "Ampere"},
        {"name": "A100X", "family": "Ampere"},
    ],
    # Datacenter - A Series
    "a-series": [
        {"name": "A40", "family": "Ampere"},
        {"name": "A30", "family": "Ampere"},
        {"name": "A16", "family": "Ampere"},
        {"name": "A10G", "family": "Ampere"},
        {"name": "A10", "family": "Ampere"},
    ],
    # Datacenter - L Series
    "l-series": [
        {"name": "L40S", "family": "Ada Lovelace"},
        {"name": "L40", "family": "Ada Lovelace"},
        {"name": "L4", "family": "Ada Lovelace"},
    ],
    # Titan
    "titan": [
        {"name": "Titan RTX", "family": "Turing"},
        {"name": "Titan V", "family": "Volta"},
        {"name": "Titan X", "family": "Pascal"},
        {"name": "Titan Xp", "family": "Pascal"},
    ],
    # Workstation - Quadro RTX
    "quadro-rtx": [
        {"name": "RTX 8000", "family": "Turing"},
        {"name": "RTX 6000", "family": "Turing"},
        {"name": "RTX 5000", "family": "Turing"},
        {"name": "RTX 4000", "family": "Turing"},
    ],
    # Workstation - Quadro P Series
    "quadro-p": [
        {"name": "GP100", "family": "Pascal"},
        {"name": "P6000", "family": "Pascal"},
        {"name": "P5000", "family": "Pascal"},
        {"name": "P4000", "family": "Pascal"},
        {"name": "P2000", "family": "Pascal"},
        {"name": "P106-100", "family": "Pascal"},
        {"name": "P104-100", "family": "Pascal"},
    ],
}
