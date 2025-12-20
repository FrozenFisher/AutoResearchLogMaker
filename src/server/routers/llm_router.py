from fastapi import APIRouter
from typing import Any, Dict, Optional, List
import json

from server.config import settings
from server.models import BaseResponse

router = APIRouter(prefix="/llm", tags=["llm"])

_LLM_CONFIG_PATH = settings.USRDATA_DIR / "llm_config.json"


def _load_llm_config() -> Dict[str, Any]:
  if _LLM_CONFIG_PATH.exists():
    try:
      with open(_LLM_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {
          "base_url": data.get("base_url"),
          "api_key": data.get("api_key"),
          "default_model": data.get("default_model"),
        }
    except (IOError, json.JSONDecodeError):
      pass
  # 回退到环境变量配置
  return {
    "base_url": settings.OPENAI_BASE_URL,
    "api_key": settings.OPENAI_API_KEY,
    "default_model": settings.DEFAULT_LLM_MODEL,
  }


def _save_llm_config(
  base_url: Optional[str],
  api_key: Optional[str],
  default_model: Optional[str],
) -> bool:
  try:
    _LLM_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LLM_CONFIG_PATH, "w", encoding="utf-8") as f:
      json.dump(
        {
          "base_url": base_url,
          "api_key": api_key,
          "default_model": default_model,
        },
        f,
        ensure_ascii=False,
        indent=2,
      )

    # 同步写入 .env 中的 OPENAI_BASE_URL / OPENAI_API_KEY，方便其他依赖读取
    try:
      env_path = settings.BASE_DIR / ".env"
      lines: List[str] = []
      if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as ef:
          lines = ef.readlines()

      def upsert(key: str, value: Optional[str]) -> None:
        nonlocal lines
        found = False
        new_lines: List[str] = []
        for line in lines:
          if line.startswith(f"{key}="):
            found = True
            if value is not None:
              new_lines.append(f"{key}={value}\n")
            # 如果 value 为空，则等于删除该键
          else:
            new_lines.append(line)
        if not found and value is not None:
          new_lines.append(f"{key}={value}\n")
        lines = new_lines

      upsert("OPENAI_BASE_URL", base_url)
      upsert("OPENAI_API_KEY", api_key)
      upsert("DEFAULT_LLM_MODEL", default_model)

      with open(env_path, "w", encoding="utf-8") as ef:
        ef.writelines(lines)
    except IOError:
      # 同步 .env 失败不应影响主流程
      pass

    return True
  except IOError:
    return False


@router.get("/config", response_model=BaseResponse)
async def get_llm_config() -> Dict[str, Any]:
  """获取当前 LLM 配置（OpenAI 兼容接口）"""
  cfg = _load_llm_config()
  # 为了安全，不回显 api_key 具体值，只告知是否已配置
  data = {
    "base_url": cfg.get("base_url"),
    "has_api_key": bool(cfg.get("api_key")),
    "default_model": cfg.get("default_model"),
  }
  return {"code": 0, "status": "ok", "message": "", "data": data}


@router.post("/config", response_model=BaseResponse)
async def update_llm_config(body: Dict[str, Any]) -> Dict[str, Any]:
  """更新 LLM 配置（base_url + api_key）"""
  base_url = body.get("base_url")
  api_key = body.get("api_key")
  default_model = body.get("default_model")

  if not base_url:
    return {
      "code": 1,
      "status": "error",
      "message": "base_url 不能为空",
      "data": None,
    }

  ok = _save_llm_config(base_url, api_key, default_model)
  if not ok:
    return {
      "code": 2,
      "status": "error",
      "message": "保存配置失败",
      "data": None,
    }

  return {
    "code": 0,
    "status": "ok",
    "message": "配置已更新（部分功能可能需要重启服务生效）",
    "data": {"base_url": base_url},
  }


@router.get("/models", response_model=BaseResponse)
async def list_llm_models() -> Dict[str, Any]:
  """根据当前 LLM 配置调用 /v1/models，返回可用模型列表"""
  cfg = _load_llm_config()
  base_url = cfg.get("base_url") or settings.OPENAI_BASE_URL
  api_key = cfg.get("api_key") or settings.OPENAI_API_KEY

  if not base_url:
    return {
      "code": 1,
      "status": "error",
      "message": "尚未配置 LLM base_url",
      "data": [],
    }

  try:
    try:
      import httpx  # type: ignore
    except ImportError:
      return {
        "code": 2,
        "status": "error",
        "message": "服务器缺少 httpx 依赖，无法请求模型列表",
        "data": [],
      }

    base = base_url.rstrip("/")
    # 兼容用户已经在 Base URL 里写了 /v1 的情况，避免出现 /v1/v1/models
    if base.endswith("/v1"):
      url = base + "/models"
    else:
      url = base + "/v1/models"
    headers = {}
    if api_key:
      headers["Authorization"] = f"Bearer {api_key}"

    with httpx.Client(timeout=10.0) as client:
      resp = client.get(url, headers=headers)
      resp.raise_for_status()
      data = resp.json()

    raw_models = data.get("data", [])
    models: List[Dict[str, Any]] = []
    for m in raw_models:
      models.append(
        {
          "id": m.get("id"),
          "owned_by": m.get("owned_by"),
          "object": m.get("object"),
        }
      )

    return {
      "code": 0,
      "status": "ok",
      "message": "",
      "data": models,
    }
  except Exception as e:
    return {
      "code": 3,
      "status": "error",
      "message": f"获取模型列表失败: {e}",
      "data": [],
    }


