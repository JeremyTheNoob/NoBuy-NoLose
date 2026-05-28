from .provider import DataProvider, StockData
from .akshare_provider import AkshareProvider
from .tushare_provider import TushareProvider
from .eastmoney_provider import EastmoneyProvider
from .sina_provider import SinaProvider
from .cache import get_cached, save_cache
from ..config import AppConfig


def _build_providers(config: AppConfig) -> list[DataProvider]:
    providers: list[DataProvider] = []
    for name in config.data.provider_order:
        if name == "tushare" and config.data.tushare.token:
            providers.append(TushareProvider(token=config.data.tushare.token))
        elif name == "akshare":
            providers.append(AkshareProvider())
        elif name == "sina":
            providers.append(SinaProvider())
        elif name == "eastmoney":
            providers.append(EastmoneyProvider())
    return providers


def _has_data(data: StockData) -> bool:
    """判断是否获取到了有效数据"""
    return bool(
        data.info.name
        or data.valuation.pe is not None
        or data.technical.price is not None
    )


def fetch_stock_data(symbol: str, config: AppConfig) -> tuple[StockData, str]:
    """
    按配置的优先级依次尝试数据源，优先读缓存。
    返回 (StockData, 实际使用的 provider_name)。
    若全部失败则抛出 RuntimeError。
    """

    # 1. 尝试缓存
    cached = get_cached(symbol, ttl=config.data.cache_ttl)
    if cached is not None:
        return cached, "cache"

    # 2. 按优先级尝试数据源
    providers = _build_providers(config)
    last_error = None

    for p in providers:
        if not p.is_available():
            continue
        try:
            data = p.fetch_all(symbol)
            if _has_data(data):
                save_cache(symbol, data)
                return data, p.name
        except Exception as e:
            last_error = e
            continue

    # 3. 全部失败，尝试用过期缓存兜底
    stale = get_cached(symbol, ttl=86400 * 7)
    if stale is not None:
        return stale, "cache(stale)"

    msg = "所有数据源均无法获取数据。\n"
    msg += "请检查：\n"
    msg += "1. 网络连接是否正常\n"
    msg += "2. 股票代码是否正确（6位数字）\n"
    msg += "3. 推荐在 config.yaml 中配置 tushare token（最稳定）\n"
    msg += "   注册地址: https://tushare.pro 免费注册即可获取 token"
    if last_error:
        msg += f"\n最后错误: {last_error}"
    raise RuntimeError(msg)
