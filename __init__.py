# ComfyUI-ZH-Tag-Helper: Chinese tag autocomplete, a categorized tag panel next to the prompt box,
# live tag count, and a "画风图鉴" sidebar window. Frontend only, no nodes.
# Optional local folders (not in the repo): explorer/ (Illustrious-NoobAI-Style-Explorer) and lora_styles/.
import os

from server import PromptServer

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web"

_here = os.path.dirname(os.path.abspath(__file__))
for _route, _sub in (("/artist-explorer", "explorer"), ("/lora-styles", "lora_styles")):
    _path = os.path.join(_here, _sub)
    if os.path.isdir(_path):
        PromptServer.instance.app.router.add_static(_route, _path)
